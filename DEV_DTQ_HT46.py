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

class voice_monitor(QThread):
    def __init__(self, devid, pos, parent=None):
        super(voice_monitor, self).__init__(parent)
        self.working = True
        self.devid = devid
        self.pac_start_num = pos
        self.dat_dict = {}
        self.max_cnt = 0
        self.file_name = None
        self.mp3_file = None
        self.file_path = None
        self.mp3_player = None
        self.new_data = None
        self.rev_state = None

    def __del__(self):
        self.working = False
        self.wait()

    def get_update_file_name(self):
        # 打印提示信息
        voice_time = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
        self.file_name = "VOICE_%08X_%s.mp3" % (self.devid, voice_time)
        print u"[ %08x ]:录音开始 :%s！" % (self.devid, self.file_name)

    def run(self):
        while self.working == True:
            if self.new_data:
                # 数据开始检查
                if self.rev_state == None:
                    self.get_update_file_name()
                    self.rev_state = 1
                # 语音数据分析
                if self.new_data["FLG"] == 0:
                    self.dat_dict[self.new_data["POS"]] = self.new_data["DATA"]
                else:
                    self.dat_dict[self.new_data["POS"]] = self.new_data["DATA"]
                    # 转换文件
                    pos = self.new_data["POS"]
                    cnt = 0
                    self.file_path = os.path.abspath("./") + '\\VOICE\\%s' % (self.file_name)
                    self.mp3_file = open(self.file_path, 'wb')
                    for item in range(self.pac_start_num, pos+1):
                        if item in self.dat_dict:
                            self.mp3_file.write(bytearray(self.dat_dict[item])) 
                            cnt = cnt + 1
                    self.mp3_file.close()
                    # 播放测试
                    print u"[ %08x ]:数据记录 :发送数据包[%d], 接收数据包[%d]！" % \
                        (self.devid, pos+1-self.pac_start_num, cnt)
                    print u"[ %08x ]:播放测试 :%s！" % (self.devid, self.file_name)
                    self.mp3_player = mp3play.load(self.file_path)
                    self.mp3_player.play()
                    time.sleep(self.mp3_player.seconds())
                    self.mp3_player.stop()
                    self.rev_state = None
                self.new_data = {}

class XesHT46():
    def __init__(self, devid):
        self.devid = devid
        self.cur_seq = 0
        self.cur_cmd = 0
        self.voice_monitor = None

    def seq_add(self):
        self.cur_seq = self.cur_seq + 1

class XesHT46Pro():
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
            0x03: "DTQ_VOICE"
        }
        self.decode_cmds = {
            0x81: self.answer_info_err,
            0x02: self.answer_info_decode,
            0x03: self.answer_voice_update,
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
    def get_dec_uid(self, uid_arr):
        return ((uid_arr[0] << 24) | (uid_arr[1] << 16) |
                (uid_arr[2] << 8) | uid_arr[3])

    def uid_negative(self, uid):
        return (((uid & 0xFF000000) >> 24) | ((uid & 0x00FF0000) >> 8) |
                ((uid & 0x0000FF00) << 8) | ((uid & 0x000000FF) << 24))

    def get_uid_hex_arr(self, uid):
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
        tmp = self.dec_to_bcd(cur_time.microsecond / 10000) # 毫秒
        time_arr.append(tmp)
        tmp = self.dec_to_bcd((cur_time.microsecond / 100) % 100)
        time_arr.append(tmp)

        return time_arr

    def get_arr_time_str(self, arr):
        time_str = "%02x%02x-%02x-%02x %02x:%02x:%02x,%02x%02x" % \
         (arr[0], arr[1], arr[2], arr[3], arr[4], arr[5], arr[6], arr[7], arr[8])
        return time_str

    # 添加白名单
    def dtqdict_add(self, devid):
        if devid in self.dtqdict:
            return self.dtqdict[devid]
        else:
            self.dtqdict[devid] = XesHT46(devid)
            return self.dtqdict[devid]

    '''
        协议下发指令生成函数
    '''
    # 下发回显指令
    def get_echo_cmd_msg(self, devid, msg):
        echo_msg = []
        curdev = self.dtqdict_add(devid)
        # 填充设备ID
        uid_arr = self.get_uid_hex_arr(curdev.devid)
        for item in uid_arr:
            echo_msg.append(item)
        # 填充包序号
        curdev.seq_add()
        seq_arr = self.get_seq_hex_arr(curdev.cur_seq)
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

    '''
        协议上报指令解析函数
    '''
    def answer_cmd_decode(self, msg_arr):
        if msg_arr:
            pac_info = {}
            rpos = 1
            pac_info["UID"] = self.get_dec_uid(msg_arr[rpos:rpos+4])
            curdev = self.dtqdict_add(pac_info["UID"])
            rpos = rpos + 4
            pac_info["SEQ"] = self.get_dec_uid(msg_arr[rpos:rpos+4])
            rpos = rpos + 4
            cur_cmd = msg_arr[rpos:rpos+1][0]
            rpos = rpos + 1
            if cur_cmd in self.decode_cmds_name:
                pac_info["CMD"] = self.decode_cmds_name[cur_cmd]
                pac_info["LEN"] = msg_arr[rpos:rpos+1][0]
                rpos = rpos + 1
                if cur_cmd in self.decode_cmds:
                    if cur_cmd > 0x80:
                        pac_info["RESULT"] = self.decode_cmds[cur_cmd](curdev, msg_arr[rpos:])
                    else:
                        pac_info["MSG"] = self.decode_cmds[cur_cmd](curdev, msg_arr[rpos:])
                else:
                    print "NOP PROCESS!"
                    return None
            else:
                print "UNKONW CMD!"
                return None
            
            return pac_info

    # 下发题目指令操作结果返回
    def answer_info_err(self, dtq, msg_arr):
        if msg_arr[0] == 0:
            return True
        else:
            return False

    # 上报答案格式解析
    def answer_info_decode(self, dtq, msg_arr):
        answer_info = {}
        rpos = 0
        answer_info["RSSI"] = msg_arr[rpos:rpos+1][0]
        rpos = rpos + 1
        answer_info["TIME"] = self.get_arr_time_str(msg_arr[rpos:rpos+9])
        rpos = rpos + 9
        answer_info["PRESS"] = self.get_dec_uid(msg_arr[rpos:rpos+4])
        rpos = rpos + 4
        answer_info["KEY"] = self.get_dec_uid(msg_arr[rpos:rpos+4])
        rpos = rpos + 4
        answer_info["SEND"] = self.get_dec_uid(msg_arr[rpos:rpos+4])
        rpos = rpos + 4
        answer_info["ECHO"] = self.get_dec_uid(msg_arr[rpos:rpos+4])
        rpos = rpos + 4
        answer_info["TYPE"] = msg_arr[rpos:rpos+1][0]
        rpos = rpos + 1
        if answer_info["TYPE"] <= 3:
            answer_info["ANSWERS"] = msg_arr[rpos:rpos+1]
        else:
            answer_info["ANSWERS"] = msg_arr[rpos:rpos+16]
        return answer_info

    # 上报语音格式解析
    def answer_voice_update(self, dtq, voice_arr):
        voice_info = {}
        voice_msg = {}
        rpos = 0
        voice_info["RSSI"] = voice_arr[rpos:rpos+1][0]
        voice_msg["RSSI"] = voice_arr[rpos:rpos+1][0]
        rpos = rpos + 1
        voice_info["FLG"] = voice_arr[rpos:rpos+1][0]
        voice_msg["FLG"] = voice_arr[rpos:rpos+1][0]
        rpos = rpos + 1
        pac_num = voice_arr[rpos:rpos+2]
        voice_info["POS"] = (pac_num[0] << 8 | pac_num[1])
        voice_msg["POS"] = (pac_num[0] << 8 | pac_num[1])
        if dtq.voice_monitor == None:
            dtq.voice_monitor = voice_monitor(dtq.devid, voice_msg["POS"])
            dtq.voice_monitor.start()
        rpos = rpos + 2
        voice_msg["DATA"] = voice_arr[rpos:rpos+208]
        # 送入其他进程处理
        dtq.voice_monitor.new_data = voice_msg
        # 返回处理结果
        return voice_info


if __name__=='__main__':
    wl_dict = {}
    uid_arr = [0x01, 0x02, 0x03, 0x04]
    xes_decode = XesHT46Pro()
    uid_dec = xes_decode.get_dec_uid(uid_arr)
    print "Arr to dec:",
    print uid_dec
    print u"输入回下参数：%d %s" % (uid_dec, u"恭喜你！答对了")
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

    print u"上传答题器指令"
    answer_info_msg = [0xAA, 0xBB, 0xCC, 0xDD,            # UID
    0x00, 0x00, 0x00, 0x01,                               # SEQ
    0x30,                                                 # RSSI
    0x20, 0x18, 0x03, 0x08, 0x17, 0x56, 0x02, 0x01, 0x00, # TIME
    0x00, 0x00, 0x00, 0x01,                               # PRESS_CNT
    0x00, 0x00, 0x00, 0x01,                               # KEY_CNT
    0x00, 0x00, 0x00, 0x01,                               # SEND_CNT
    0x00, 0x00, 0x00, 0x01,                               # ECHO_CNT
    0x01,                                                 # ANSWER_TYPE 
    0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01]
    print u"解析结果如下"
    answer_decode_msg = xes_decode.answer_info_decode(answer_info_msg)
    print answer_decode_msg
