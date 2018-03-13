# -*- coding: utf-8 -*-
'''
* File Name   : DEV_DTQ_HT46
* Description : 答题器相关类定义文件
* Input       : None
'''

import string
import datetime
import time
import os
import mp3play
from PyQt4.QtCore import *
from PyQt4.QtGui  import *
from qprocess import *

class voice_decode():
    def __init__(self, devid):
        # 语音数据管理
        self.devid = devid    # 设备ID
        self.voice_dict = {}  # 语音数据缓冲区
        self.start_pos = 0    # 起始包包号
        self.stop_pos = 0     # 结束包包号
        self.pac_cnt = 0      # 语音数据包计数器
        self.f_name = None    # MP3 文件名
        self.f_path = None    # MP3 文件存放路径
        self.player = None    # MP3 播放器实例
        self.state = 0        # 解析数据状态机：状态
        self.state_step = {
            0: self.get_update_f_name,
            1: self.decode_porcess
        }
        # 通用数据管理
        self.rev_seq = 0
        self.send_seq = 0

    # 答题器包号管理
    def seq_add(self):
        self.send_seq = self.send_seq + 1

    # 播放测试
    def play(self):
        print u"[ %08x ]:播放测试 :%s！" % (self.devid, self.f_name)
        self.player = mp3play.load(self.f_path)
        self.player.play()
        time.sleep(self.player.seconds())
        self.player.stop()

    # 转换文件
    def decode(self):
        self.pac_cnt = 0
        self.f_path = os.path.abspath("./") + '\\VOICE\\%s' % (self.f_name)
        f = open(self.f_path, 'wb')
        for item in range(self.start_pos, self.stop_pos+1):
            if item in self.voice_dict:
                f.write(bytearray(self.voice_dict[item])) 
                self.pac_cnt = self.pac_cnt + 1
        f.close()
        print u"[ %08x ]:数据记录 :发送数据包[%d], 接收数据包[%d]！" % \
            (self.devid, self.stop_pos+1-self.start_pos, self.pac_cnt)

    # 打印提示信息
    def get_update_f_name(self, voice_info, vocie_msg):
        voice_time = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
        self.f_name = "VOICE_%08X_%s.mp3" % (self.devid, voice_time)
        print u"[ %08x ]:录音开始 :%s！" % (self.devid, self.f_name)
        # 记录初始数据
        print voice_info
        if voice_info["FLG"] == 0:
            self.start_pos = voice_info["POS"]
            self.voice_dict[voice_info["POS"]] = vocie_msg
            # 切换状态
            self.state = 1

    def decode_porcess(self, voice_info, vocie_msg):
        # 语音数据分析
        if voice_info["FLG"] == 0:
            self.voice_dict[voice_info["POS"]] = vocie_msg
        if voice_info["FLG"] == 1:
            self.voice_dict[voice_info["POS"]] = vocie_msg
            self.stop_pos = voice_info["POS"]
            # 解码
            self.decode()
            # 切换状态
            self.state = 0

class dtq_xes_ht46():
    def __init__(self):
        self.PAC_LEN = 257
        self.dtqdict = {}
        self.jsq_uid = None
        self.jsq_seq = 0
        self.cmd = None
        self.len = None
        self.data = []
        self.encode_cmds_name = { 
            "ANSWER_INFO": 0x01,
            "ANSWER_ECHO": 0x04,
            "SET_RFCH": 0x11,
            "GET_DEVINFO": 0x13,
            "CLEAR_SET": 0x14,
            "BIND_START": 0x15,
            "BIND_INFO": 0x16,
            "BIND_STOP": 0x17}
        self.decode_cmds_name = {
            0x81: "ANSWER_INFO",
            0x02: "DTQ_ANSWER",
            0x03: "DTQ_VOICE",
            0x16: "CARD_ID",
            0x84: "ECHO_IFNO",
            0x93: "DEVICE_INFO"
        }
        self.decode_cmds = {
            0x81: self.answer_info_err,
            0x02: self.answer_info_decode,
            0x03: self.answer_voice_update,
            0x16: self.card_id_update,
            0x84: self.answer_info_err,
            0x93: self.dev_info_msg_update
            # 0x91: self.set_rfch_err,
            # 0x93: self.dev_info_update,
            # 0x94: self.clear_set_err,
            # 0x95: self.bind_start_err,
            # 0x96: self.bind_stop_err,
            # 0x97: self.bind_stop
        }

    '''
        协议内部数值转化函数
    '''
    def get_gbk_hex_arr(self, msg):
        msg_arr = []
        imsg = msg.encode("gbk")
        for item in imsg:
            msg_arr.append(ord(item))
        return msg_arr

    # UID 转化函数
    def uid_pos_code(self, uid_arr):
        return ((uid_arr[0] << 24) | (uid_arr[1] << 16) | (uid_arr[2] << 8) | uid_arr[3])

    def uid_neg_code(self, uid_arr):
        return ((uid_arr[3] << 24) | (uid_arr[2] << 16) | (uid_arr[1] << 8) | uid_arr[0])

    def get_uid_arr_neg(self, uid):
        uid_arr = []
        tmp = (uid & 0xFF000000) >> 24
        uid_arr.append(tmp)
        tmp = (uid & 0xFF0000) >> 16
        uid_arr.append(tmp)
        tmp = (uid & 0xFF00) >> 8
        uid_arr.append(tmp)
        tmp = (uid & 0xFF)
        uid_arr.append(tmp)
        return uid_arr
    
    def get_uid_arr_pos(self, uid):
        uid_arr = []
        tmp = (uid & 0xFF)
        uid_arr.append(tmp)
        tmp = (uid & 0xFF00) >> 8
        uid_arr.append(tmp)
        tmp = (uid & 0xFF0000) >> 16
        uid_arr.append(tmp)
        tmp = (uid & 0xFF000000) >> 24
        uid_arr.append(tmp)
        return uid_arr

    def dec_to_bcd(self, dec_data):
        bcd_data = ((((dec_data / 10) % 10) & 0x0F) << 4) | \
                    ((dec_data % 10) & 0x0F)
        return bcd_data

    def get_seq_hex_arr(self, seq):
        seq_arr = []
        tmp = (seq & 0xFF000000) >> 24
        seq_arr.append(tmp)
        tmp = (seq & 0xFF0000) >> 16
        seq_arr.append(tmp)
        tmp = (seq & 0xFF00) >> 8
        seq_arr.append(tmp)
        tmp = (seq & 0xFF)
        seq_arr.append(tmp)
        return seq_arr

    def get_cur_bcd_time_arr(self):
        time_arr = []
        # 获取当前时间
        cur_time = datetime.datetime.now()
        tmp = self.dec_to_bcd(cur_time.year / 100)          # 年
        time_arr.append(tmp)
        tmp = self.dec_to_bcd(cur_time.year % 100)
        time_arr.append(tmp)
        time_arr.append(self.dec_to_bcd(cur_time.month))    # 月
        time_arr.append(self.dec_to_bcd(cur_time.day))      # 日
        time_arr.append(self.dec_to_bcd(cur_time.hour))     # 时
        time_arr.append(self.dec_to_bcd(cur_time.minute))   # 分
        time_arr.append(self.dec_to_bcd(cur_time.second))   # 秒
        tmp = self.dec_to_bcd(cur_time.microsecond/10000)   # 毫秒
        time_arr.append(tmp)
        tmp = self.dec_to_bcd((cur_time.microsecond/100) % 100)
        time_arr.append(tmp)
        return time_arr

    def get_arr_time_str(self, arr):
        time_str = "%02x%02x-%02x-%02x %02x:%02x:%02x,%02x%02x" % \
         (arr[0], arr[1], arr[2], arr[3], arr[4], arr[5], arr[6], arr[7], arr[8])
        return time_str

    # 添加白名单
    def get_dtq_tcb(self, devid):
        if devid not in self.dtqdict:
            self.dtqdict[devid] = voice_decode(devid)
        return self.dtqdict[devid]

    '''
        协议下发指令生成函数
    '''
    # 下发回显指令
    def get_echo_cmd_msg(self, devid, msg):
        echo_msg = []
        dtq_tcb = self.get_dtq_tcb(devid)
        # 填充设备ID
        uid_arr = self.get_uid_arr_pos(dtq_tcb.devid)
        for item in uid_arr:
            echo_msg.append(item)
        # 填充包序号
        dtq_tcb.seq_add()
        seq_arr = self.get_seq_hex_arr(dtq_tcb.send_seq)
        for item in seq_arr:
            echo_msg.append(item)
        # 设置包指令
        echo_msg.append(self.encode_cmds_name["ANSWER_ECHO"])
        # 添加包内容
        msg_arr = self.get_gbk_hex_arr(msg)
        echo_msg.append(len(msg_arr))
        for item in msg_arr:
            echo_msg.append(item)
        return echo_msg

    # 下发题目指令
    def get_question_cmd_msg(self, q_t, msg):
        que_msg = [0x00, 0x00, 0x00, 0x00]
        # 填充包序号
        self.jsq_seq = self.jsq_seq + 1
        seq_arr = self.get_seq_hex_arr(self.jsq_seq)
        for item in seq_arr:
            que_msg.append(item)
        que_msg.append(self.encode_cmds_name["ANSWER_INFO"])
        # 添加包内容
        tim_arr = self.get_cur_bcd_time_arr()
        msg_arr = self.get_gbk_hex_arr(msg)
        # 添加长度
        que_msg.append(len(tim_arr)+len(msg_arr)+1)
        # 添加时间
        for item in tim_arr:
            que_msg.append(item)
        # 添加题型
        que_msg.append(q_t)
        # 添加内容
        for item in msg_arr:
            que_msg.append(item)
        return que_msg

    # 下发设置信道
    def get_set_rf_ch_msg(self, rf_ch):
        cof_msg = [0x00, 0x00, 0x00, 0x00]
        # 填充包序号
        self.jsq_seq = self.jsq_seq + 1
        seq_arr = self.get_seq_hex_arr(self.jsq_seq)
        for item in seq_arr:
            cof_msg.append(item)
        cof_msg.append(self.encode_cmds_name["SET_RFCH"])
        # 添加包内容
        cof_msg.append(1)
        cof_msg.append(rf_ch)
        return cof_msg

    # 接收器内部指令初始化
    def get_jsq_cmd_init(self, cmd_name):
        tmp_msg = [0x00, 0x00, 0x00, 0x00]
        # 填充包序号
        self.jsq_seq = self.jsq_seq + 1
        seq_arr = self.get_seq_hex_arr(self.jsq_seq)
        for item in seq_arr:
            tmp_msg.append(item)
        if cmd_name in self.encode_cmds_name:
            tmp_msg.append(self.encode_cmds_name[cmd_name])
        else:
            tmp_msg.append(0)
        # 添加包内容
        tmp_msg.append(0)
        return tmp_msg

    # 下发查询设备信息指令
    def get_check_dev_info_msg(self):
        return self.get_jsq_cmd_init("GET_DEVINFO")

    # 下发清除配置信息指令
    def get_clear_dev_info_msg(self):
        return self.get_jsq_cmd_init("CLEAR_SET")

    # 下发绑定开始
    def get_bind_start_msg(self):
        return self.get_jsq_cmd_init("BIND_START")

    # 下发绑定结束
    def get_bind_stop_msg(self):
        return self.get_jsq_cmd_init("BIND_STOP")

    # 下发题目指令操作结果返回
    def answer_info_err(self, dtq, msg_arr):
        if msg_arr[0] == 0:
            return True
        else:
            return False

    # 上报答案格式解析
    def answer_info_decode(self, dtq_tcb, msg_arr):
        answer_info = {}
        rpos = 0
        answer_info["RSSI"] = msg_arr[rpos:rpos+1][0]
        rpos = rpos + 1
        # answer_info["TIME"] = self.get_arr_time_str(msg_arr[rpos:rpos+9])
        rpos = rpos + 9
        answer_info["PRESS"] = self.uid_neg_code(msg_arr[rpos:rpos+4])
        rpos = rpos + 4
        answer_info["KEY"] = self.uid_neg_code(msg_arr[rpos:rpos+4])
        rpos = rpos + 4
        answer_info["SEND"] = self.uid_neg_code(msg_arr[rpos:rpos+4])
        rpos = rpos + 4
        answer_info["ECHO"] = self.uid_neg_code(msg_arr[rpos:rpos+4])
        rpos = rpos + 4
        answer_info["TYPE"] = msg_arr[rpos:rpos+1][0]
        rpos = rpos + 1
        if answer_info["TYPE"] <= 3:
            answer_info["ANSWERS"] = msg_arr[rpos:rpos+1]
        else:
            answer_info["ANSWERS"] = msg_arr[rpos:rpos+16]
        return answer_info

    # 上报语音格式解析
    def answer_voice_update(self, dtq_tcb, voice_arr):
        voice_msg = {}
        rpos = 0
        voice_msg["RSSI"] = voice_arr[rpos:rpos+1][0]
        rpos = rpos + 1
        voice_msg["FLG"] = voice_arr[rpos:rpos+1][0]
        rpos = rpos + 1
        pac_num = voice_arr[rpos:rpos+2]
        voice_msg["POS"] = (pac_num[0] << 8 | pac_num[1])
        rpos = rpos + 2
        voice_data = voice_arr[rpos:rpos+208]
        dtq_tcb.state_step[dtq_tcb.state](voice_msg, voice_data)
        # 返回处理结果
        return voice_msg

   # 上报刷卡格式解析
    def card_id_update(self, dtq_tcb, msg_arr):
        card_id_msg = {}
        rpos = 0
        card_id_msg["UID"] = self.uid_neg_code(msg_arr[rpos:rpos+4])
        rpos = rpos + 4
        card_id_msg["REP_UID"] = self.uid_neg_code(msg_arr[rpos:rpos+4])
        # 返回处理结果
        return card_id_msg

    def dev_info_msg_update(self, dtq_tcb, msg_arr):
        dev_info_msg = {}
        rpos = 0
        dev_info_msg["DEVICE_ID"] = self.uid_neg_code(msg_arr[rpos:rpos+4])
        rpos = rpos + 4
        dev_info_msg["SF_VERSION"] = "v%d.%d.%d" % (msg_arr[rpos],msg_arr[rpos+1],msg_arr[rpos+2])
        rpos = rpos + 3
        # dev_info_msg["HW_VERSION"] = msg_arr[rpos:rpos+15]
        rpos = rpos + 15
        # dev_info_msg["COMPLANY"] = msg_arr[rpos:rpos+8]
        rpos = rpos + 8
        dev_info_msg["RF_CH"] = msg_arr[rpos:rpos+1][0]
        rpos = rpos + 1
        dev_info_msg["RF_TX_POWER"] = msg_arr[rpos:rpos+1][0]
        # 返回处理结果
        return dev_info_msg

    '''
        协议上报指令解析函数
    '''
    def answer_cmd_decode(self, msg_arr):
        if msg_arr:
            pac_info = {}
            rpos = 1
            pac_info["UID"] = self.uid_neg_code(msg_arr[rpos:rpos+4])
            dtq_tcb = self.get_dtq_tcb(pac_info["UID"])
            rpos = rpos + 4
            pac_info["SEQ"] = self.uid_pos_code(msg_arr[rpos:rpos+4])
            rpos = rpos + 4
            cur_cmd = msg_arr[rpos:rpos+1][0]
            rpos = rpos + 1
            print "REV_CMD : %02x " % cur_cmd
            if cur_cmd in self.decode_cmds_name:
                pac_info["CMD"] = self.decode_cmds_name[cur_cmd]
                pac_info["LEN"] = msg_arr[rpos:rpos+1][0]
                rpos = rpos + 1
                if cur_cmd in self.decode_cmds:
                    pac_info["MSG"] = self.decode_cmds[cur_cmd](dtq_tcb, msg_arr[rpos:])
                else:
                    print "NOP PROCESS!"
                    return None
            else:
                print "UNKONW CMD!"
                return None
            return pac_info

if __name__=='__main__':
    wl_dict = {}
    xes_decode = dtq_xes_ht46()
    uid_dec = xes_decode.get_uid_arr_neg( 0x11223344 )
    print "Arr to dec:",
    print uid_dec
    print u"输入回下参数：%02x%02x%02x%02x %s" % (uid_dec[0],uid_dec[1],uid_dec[2],uid_dec[3], u"恭喜你！答对了")
    echo_arr = xes_decode.get_echo_cmd_msg(0x061D942D, u"恭喜你！答对了")
    print u"输出指令数组：",
    echo_arr_str = ""
    for item in echo_arr:
        echo_arr_str += "%02X " % item
    print echo_arr_str

    print u"输入回下参数： %s" % (u"单选题测试")
    que_arr = xes_decode.get_question_cmd_msg(1, u"单选题测试")
    print u"输出指令数组：",
    echo_arr_str = ""
    for item in que_arr:
        echo_arr_str += "%02X " % item
    print echo_arr_str

    print u"测试下发设置信道指令"
    que_arr = xes_decode.get_set_rf_ch_msg(1)
    print u"输出指令数组：",
    echo_arr_str = ""
    for item in que_arr:
        echo_arr_str += "%02X " % item
    print echo_arr_str

    print u"下发查询设备信息指令"
    que_arr = xes_decode.get_check_dev_info_msg()
    print u"输出指令数组：",
    echo_arr_str = ""
    for item in que_arr:
        echo_arr_str += "%02X " % item
    print echo_arr_str

    print u"下发清除配置信息指令"
    que_arr = xes_decode.get_clear_dev_info_msg()
    print u"输出指令数组：",
    echo_arr_str = ""
    for item in que_arr:
        echo_arr_str += "%02X " % item
    print echo_arr_str

    print u"下发绑定开始"
    que_arr = xes_decode.get_bind_start_msg()
    print u"输出指令数组：",
    echo_arr_str = ""
    for item in que_arr:
        echo_arr_str += "%02X " % item
    print echo_arr_str

    print u"下发绑定结束"
    que_arr = xes_decode.get_bind_stop_msg()
    print u"输出指令数组：",
    echo_arr_str = ""
    for item in que_arr:
        echo_arr_str += "%02X " % item
    print echo_arr_str

    # print u"上传答题器指令"
    # answer_info_msg = [0xAA, 0xBB, 0xCC, 0xDD,            # UID
    # 0x00, 0x00, 0x00, 0x01,                               # SEQ
    # 0x30,                                                 # RSSI
    # 0x20, 0x18, 0x03, 0x08, 0x17, 0x56, 0x02, 0x01, 0x00, # TIME
    # 0x00, 0x00, 0x00, 0x01,                               # PRESS_CNT
    # 0x00, 0x00, 0x00, 0x01,                               # KEY_CNT
    # 0x00, 0x00, 0x00, 0x01,                               # SEND_CNT
    # 0x00, 0x00, 0x00, 0x01,                               # ECHO_CNT
    # 0x01,                                                 # ANSWER_TYPE 
    # 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01]
    # print u"解析结果如下"
    # answer_decode_msg = xes_decode.answer_info_decode(answer_info_msg)
    # print answer_decode_msg
