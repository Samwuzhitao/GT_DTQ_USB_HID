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

class dtq():
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
        self.state = 0
        # 通用数据管理
        self.rev_seq = 0
        self.send_seq = 0
        # 统计计数
        self.card_cnt = 0
        self.answer_cnt = 0

    # 答题器包号管理
    def seq_add(self):
        self.send_seq = self.send_seq + 1

    # 播放测试
    def play(self):
        self.player = mp3play.load(self.f_path)
        self.player.play()
        # print u"[ %010u ]:播放测试 :%s！" % (self.devid, self.f_name)

    # 数据校验
    def check(self,r_lcd):
        # 校验
        max_size = 0
        f = open(self.f_path, 'rb')
        rd_pos = 0
        pac_err = ""
        pac_ok_str = ""
        for item in range(self.start_pos, self.stop_pos+1):
            if item in self.voice_dict:
                f.seek(rd_pos,0)
                pac_len = len(self.voice_dict[item])
                rd_data = f.read(pac_len)
                # 读回数据输出
                rd_str = u"RD: 偏移:%d 数据: " % rd_pos
                for rd_item in rd_data:
                    rd_str += " %02X" % (ord(rd_item))
                # 写入数据输出
                wr_str = u"WR: 偏移:%d 数据: " % rd_pos
                for wr_item in self.voice_dict[item]:
                    wr_str += " %02X" % (wr_item)
                rd_pos = rd_pos + pac_len
                print rd_str
                print wr_str
                err = 0
                for pos in range(0, pac_len):
                    if ord(rd_data[pos]) != self.voice_dict[item][pos]:
                        print "write err! rd:%x wr:%x" % (ord(rd_data[pos]), 
                            self.voice_dict[item][pos])
                        err = 1
                if err:
                    print "COMPARE ERR: PACK[%d] %d " % (item,err)
                    pac_err += "[ %3d ]" % item
                else:
                    pac_ok_str += "[ %3d ]" % item
        f.close()
        check_str = u"\t检验出错数据包: %s \r\n" % (pac_err)
        info_str = u"\t理论文件大小:%d 实际文件大小:%d 检验总长度:%d \r\n" % \
            (max_size,int(os.path.getsize(self.f_path)),cnt_size)
        msg_str = info_str + check_str
        r_lcd(msg_str)

    # MP3 格式检测
    def mp3_format_check(self, voice_data):
        if voice_data[0] == 0xFF and voice_data[1] == 0xFB:
            return True
        else:
            return False

    # 转换文件
    def decode(self, r_lcd):
        self.f_path = os.path.abspath("./") + '/VOICE/%s' % (self.f_name)
        cnt_size = 0
        msg_str = ""
        format_err = ""
        f = open(self.f_path, 'wb')
        for item in range(self.start_pos, self.stop_pos+1):
            if item in self.voice_dict:
                wr_data = bytearray(self.voice_dict[item])
                f.write(wr_data)
                cnt_size += len(wr_data)
                if self.mp3_format_check(self.voice_dict[item]) == False:
                    format_err += "[ %3d ]" % item
            else:
                msg_str += "[ %3d ]" % item
        f.close()
        msg_str = u"[ %010u ]:数据记录 文件大小: [ %d ], 发送数据包: [ %d ], 接收数据包: [ %d ]！\r\n" % \
            (self.devid, cnt_size, self.stop_pos+1-self.start_pos, self.pac_cnt)
        msg_str += u"丢包统计：\r\n"
        
        msg_str += u"错帧统计：\r\n"
        msg_str += format_err
        r_lcd(msg_str)
        self.voice_dict.clear()
        self.state = 0

    # 打印提示信息
    def decode_porcess(self, r_lcd, voice_info, vocie_msg):
        if voice_info["FLG"] == 0 and voice_info["POS"] == 1:
            voice_time = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
            self.f_name = "VOICE_%010u_%s.mp3" % (self.devid, voice_time)
            msg_str = u"[ %010u ]:录音开始 :%s！" % (self.devid, self.f_name)
            r_lcd(msg_str)
            # 记录初始数据
            # print voice_info
            self.pac_cnt = 1
            self.start_pos = voice_info["POS"]
            self.voice_dict[voice_info["POS"]] = vocie_msg
            self.state = 1
        else:
            if voice_info["POS"] not in self.voice_dict:
                self.pac_cnt = self.pac_cnt + 1
            self.voice_dict[voice_info["POS"]] = vocie_msg
            if voice_info["FLG"] == 1:
                self.stop_pos = voice_info["POS"]
                # 解码
                self.decode(r_lcd)

class dtq_xes_ht46():
    def __init__(self, r_lcd_hook):
        self.PAC_LEN = 257
        self.r_lcd = r_lcd_hook
        # self.usb_snd = usb_snd
        self.dtqdict = {}
        self.jsq_uid = None
        self.jsq_seq = 0
        self.cmd = None
        self.len = None
        self.data = []
        self.dfu_s = 0
        self.encode_cmds_name = { 
            "ANSWER_INFO": 0x01,
            "ANSWER_ECHO": 0x04,
            "CTL_INFO": 0x05,
            "SET_RFCH": 0x11,
            "GET_DEVINFO": 0x13,
            "CLEAR_SET": 0x14,
            "BIND_START": 0x15,
            "BIND_INFO": 0x16,
            "BIND_STOP": 0x17,
            "RESET_PORT": 0x20,
            "CHECK_WL": 0x21}
        self.decode_cmds_name = {
            0x81: "ANSWER_INFO",
            0x02: "ANSWER",
            0x03: "VOICE",
            0x16: "CARD_ID",
            0x84: "ECHO_IFNO",
            0x85: "CTL_INFO",
            0x91: "SET_RFCH",
            0x93: "DEVICE_INFO",
            0x94: "CLEAR_SET",
            0x95: "BIND_START",
            0x97: "BIND_STOP",
            0xA8: "RESET_PORT",
            0xA1: "CHECK_WL",
            0xB0: "DFU_INFO"
        }
        self.decode_cmds = {
            0x81: self.answer_info_err,
            0x02: self.answer_info_decode,
            0x03: self.answer_voice_update,
            0x16: self.card_id_update,
            0x84: self.echo_info_err,
            0x85: self.ctl_info_err,
            0x91: self.set_rf_ch_err,
            0x93: self.dev_info_msg_update,
            0x94: self.bind_clear_conf_err,
            0xA8: self.port_reset_err,
            0x95: self.bind_start_err,
            0x97: self.bind_stop_err,
            0xA1: self.dev_wl_msg_update,
            0xB0: self.dfu_info_err
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
    def get_dtq(self, devid):
        if devid not in self.dtqdict:
            self.dtqdict[devid] = dtq(devid)
        return self.dtqdict[devid]

    '''
        协议下发指令生成函数
    '''
    # 下发回显指令
    def get_echo_cmd_msg(self, devid, msg):
        echo_msg = []
        dtq = self.get_dtq(devid)
        # 填充设备ID
        uid_arr = self.get_uid_arr_pos(dtq.devid)
        for item in uid_arr:
            echo_msg.append(item)
        # 填充包序号
        dtq.seq_add()
        seq_arr = self.get_seq_hex_arr(dtq.send_seq)
        for item in seq_arr:
            echo_msg.append(item)
        # 设置包指令
        echo_msg.append(self.encode_cmds_name["ANSWER_ECHO"])
        # 添加包内容
        msg = self.get_gbk_hex_arr(msg)
        echo_msg.append(len(msg))
        for item in msg:
            echo_msg.append(item)
        return echo_msg

    # 下发题目指令
    def get_question_cmd_msg(self, devid, q_t, msg):
        que_msg = []
        # 填充设备ID
        uid_arr = self.get_uid_arr_pos(devid)
        for item in uid_arr:
            que_msg.append(item)
        # 填充包序号
        self.jsq_seq = self.jsq_seq + 1
        seq_arr = self.get_seq_hex_arr(self.jsq_seq)
        for item in seq_arr:
            que_msg.append(item)
        que_msg.append(self.encode_cmds_name["ANSWER_INFO"])
        # 添加包内容
        tim_arr = self.get_cur_bcd_time_arr()
        msg = self.get_gbk_hex_arr(msg)
        # 添加长度
        que_msg.append(len(tim_arr)+len(msg)+1)
        # 添加时间
        for item in tim_arr:
            que_msg.append(item)
        # 添加题型
        que_msg.append(q_t)
        # 添加内容
        for item in msg:
            que_msg.append(item)
        return que_msg

    # 下发答题器控制指令
    def get_dtq_ctl_msg(self, devid, led_cn, led_c, beep_cn, motor_cn):
        TIME = [0x00, 0x0C, 0x00]
        ctl_msg = []
        dtq = self.get_dtq(devid)
        # 填充设备ID
        uid_arr = self.get_uid_arr_pos(dtq.devid)
        for item in uid_arr:
            ctl_msg.append(item)
        # 填充包序号
        dtq.seq_add()
        seq_arr = self.get_seq_hex_arr(dtq.send_seq)
        for item in seq_arr:
            ctl_msg.append(item)
        # 设置包指令
        ctl_msg.append(self.encode_cmds_name["CTL_INFO"])
        # 添加包内容
        ctl_msg.append(12)
        ctl_msg.append(led_cn)
        ctl_msg.append(led_c)
        ctl_msg.append(TIME[0])
        ctl_msg.append(TIME[1])
        ctl_msg.append(beep_cn)
        ctl_msg.append(TIME[0])
        ctl_msg.append(TIME[1])
        ctl_msg.append(TIME[2])
        ctl_msg.append(motor_cn)
        ctl_msg.append(TIME[0])
        ctl_msg.append(TIME[1])
        ctl_msg.append(TIME[2])
        return ctl_msg

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

    # 下发查看白名单
    def get_check_wl_msg(self):
        return self.get_jsq_cmd_init("CHECK_WL")

    # 下发题目指令操作结果返回
    def answer_info_err(self, uid_dict, dtq, msg):
        self.r_lcd(u"R: 发送题目 : ERR: %d " % (msg[0]))

    # 下发回显指令操作结果返回
    def echo_info_err(self, uid_dict, dtq, msg):
        self.r_lcd(u"R: 发送回显 : ERR: %d " % (msg[0]))
        # print u"R: 发送回显 : ERR: %d " % (msg[0]

    # 发送控制参数操作结果返回
    def ctl_info_err(self, uid_dict, dtq, msg):
        self.r_lcd(u"R: 答题器控制 : ERR: %d " % (msg[0]))

    # 复位端口指令
    def port_reset_err(self, uid_dict, dtq, msg):
        self.r_lcd(u"R: 复位端口 : ERR: %d " % (msg[0]))

    # 复位端口指令
    def set_rf_ch_err(self, uid_dict, dtq, msg):
        self.r_lcd(u"R: 修改信道 : ERR: %d " % (msg[0]))

    # 开始绑定指令
    def bind_start_err(self, uid_dict, dtq, msg):
        self.r_lcd(u"R: 开始绑定 : ERR: %d " % (msg[0]))

    # 停止绑定指令
    def bind_stop_err(self, uid_dict, dtq, msg):
        self.r_lcd(u"R: 停止绑定 : ERR: %d " % (msg[0]))

    # 清除配置
    def bind_clear_conf_err(self, uid_dict, dtq, msg):
        self.r_lcd(u"R: 清除配置 : ERR: %d " % (msg[0]))

    # DFU开始指令
    def dfu_info_err(self, uid_dict, dtq, msg):
        self.r_lcd(u"R: 建立连接成功...")
        self.dfu_s = 1

    # 下发复位端口指令
    def get_reset_port_msg(self, port):
        cof_msg = [0x00, 0x00, 0x00, 0x00]
        # 填充包序号
        self.jsq_seq = self.jsq_seq + 1
        seq_arr = self.get_seq_hex_arr(self.jsq_seq)
        for item in seq_arr:
            cof_msg.append(item)
        cof_msg.append(self.encode_cmds_name["RESET_PORT"])
        # 添加包内容
        cof_msg.append(1)
        cof_msg.append(port)
        return cof_msg
    
    def get_dfu_msg(self, cmd, image_info):
        soh_msg = [0x00, 0x00, 0x00, 0x00]
        # 填充包序号
        self.jsq_seq = self.jsq_seq + 1
        seq_arr = self.get_seq_hex_arr(self.jsq_seq)
        for item in seq_arr:
            soh_msg.append(item)
        soh_msg.append(cmd)
        # 添加包内容
        soh_msg.append(len(image_info))
        for item in image_info:
            soh_msg.append(item)
        return soh_msg

    '''
        协议上报解析函数
    '''
    # 上报答案格式解析
    def answer_info_decode(self, uid_dict, dtq, msg):
        rpos = 0
        tree_dict = {}
        show_msg = "R: [ %010u ] RSSI: -%3d, " % (dtq.devid, msg[rpos: rpos+1][0])
        rpos = rpos + 1  # RSSI
        rpos = rpos + 9  # TIME
        show_msg += "POWER:%6d, " %  msg[rpos: rpos+1][0]
        rpos = rpos + 4  # POWER
        show_msg += "PRESS:%6d, " % self.uid_pos_code(msg[rpos: rpos+4])
        rpos = rpos + 4  # PRESS
        show_msg += "KEY:%6d, " % self.uid_pos_code(msg[rpos: rpos+4])
        rpos = rpos + 4  # KEY
        show_msg += "SEND:%6d, " % self.uid_pos_code(msg[rpos: rpos+4])
        cnt_start = self.uid_pos_code(msg[rpos: rpos+4])
        rpos = rpos + 4  # SEND
        show_msg += "ECHO:%6d, " % self.uid_pos_code(msg[rpos: rpos+4])
        rpos = rpos + 4  # ECHO
        answer_type = msg[rpos: rpos+1][0]
        show_msg += "TYPE:%x, " % answer_type
        rpos = rpos + 1  # TYPE
        if (answer_type < 4) or (answer_type > 5):
            show_msg += "ANSWERS:%x " % (msg[rpos: rpos+1][0])
        else:
            show_msg += "ANSWERS:%s " % (u"{0}".format(msg[rpos: rpos+16]))
        self.r_lcd(show_msg)
        # print show_msg
        dtq.answer_cnt = dtq.answer_cnt + 1
        tree_dict["UID"] = dtq.devid
        tree_dict["ANSWER"] = dtq.answer_cnt
        tree_dict["CMD"] = "ANSWER"
        if "cnt_r" not in uid_dict:
            uid_dict["cnt_r"] = {}
            uid_dict["cnt_s0"] = {}
            uid_dict["cnt_s1"] = {}
            uid_dict["cnt_r"][dtq.devid] = dtq.answer_cnt
            uid_dict["cnt_s0"][dtq.devid] = cnt_start-1
            uid_dict["cnt_s1"][dtq.devid] = cnt_start - uid_dict["cnt_s0"][dtq.devid]
        else:
            if dtq.devid not in uid_dict["cnt_r"]:
                uid_dict["cnt_r"][dtq.devid] = dtq.answer_cnt
                uid_dict["cnt_s0"][dtq.devid] = cnt_start-1
                uid_dict["cnt_s1"][dtq.devid] = cnt_start - uid_dict["cnt_s0"][dtq.devid]
            else:
                uid_dict["cnt_r"][dtq.devid] = dtq.answer_cnt
                uid_dict["cnt_s1"][dtq.devid] = cnt_start - uid_dict["cnt_s0"][dtq.devid]
        return tree_dict

    # 上报语音格式解析
    def answer_voice_update(self, uid_dict, dtq, msg):
        voice_msg = {}
        tree_dict = {}
        rpos = 0
        voice_msg["RSSI"] = msg[rpos:rpos+1][0]
        rpos = rpos + 1     # RSSI
        voice_msg["FLG"] = msg[rpos:rpos+1][0]
        rpos = rpos + 1     # FLG
        pac_num = msg[rpos:rpos+2]
        voice_msg["POS"] = (pac_num[0] << 8 | pac_num[1])
        # print "POS = %d " % voice_msg["POS"]
        rpos = rpos + 2     # PAC_NUM
        voice_data = msg[rpos:rpos+208]
        # debug_str = "R: "
        # for item in voice_data:
        #    debug_str += " %02X" % (item)
        # print debug_str
        rpos = rpos + 208   # PAC_VOICE
        # print msg[rpos:]
        dtq.decode_porcess(self.r_lcd, voice_msg, voice_data)
        # 返回处理结果
        tree_dict["UID"] = dtq.devid
        tree_dict["VOICE_FLG"] = voice_msg["FLG"]
        tree_dict["VOICE"] = dtq.pac_cnt
        tree_dict["CMD"] = "VOICE"
        return tree_dict

   # 上报刷卡格式解析
    def card_id_update(self, uid_dict, dtq, msg):
        rpos = 0
        tree_dict = {}
        uid = self.uid_neg_code(msg[rpos:rpos+4])
        devid = self.uid_pos_code(msg[rpos:rpos+4])
        rpos = rpos + 4
        rep_uid = self.uid_neg_code(msg[rpos:rpos+4])
        # 返回处理结果
        show_msg = u"R: CARD_INFO: UID: [ %010u ] REP_UID:[ %10u ] " % (uid, rep_uid)
        self.r_lcd(show_msg)
        if "uid_list" in uid_dict:
            if uid not in uid_dict["uid_list"]:
                uid_dict["uid_list"].append(uid)
        else:
            uid_dict["uid_list"] = []
            uid_dict["uid_list"].append(uid)
        cur_dtq = self.get_dtq(devid)
        cur_dtq.card_cnt = cur_dtq.card_cnt + 1
        tree_dict["UID"] = uid
        tree_dict["CARD_ID"] = cur_dtq.card_cnt
        tree_dict["CMD"] = "CARD_ID"
        return tree_dict

    def dev_info_msg_update(self, uid_dict, dtq, msg):
        rpos = 0
        dev_id = self.uid_neg_code(msg[rpos:rpos+4])
        rpos = rpos + 4
        sf_version = "v%d.%d.%d" % (msg[rpos], msg[rpos+1], msg[rpos+2])
        rpos = rpos + 3   # SF_VERSION
        rpos = rpos + 15  # HW_VERSION
        rpos = rpos + 8   # COMPLANY
        rf_ch = msg[rpos:rpos+1][0]
        rpos = rpos + 1   # RF_CH
        tx_power = msg[rpos:rpos+1][0]
        # 返回处理结果
        show_msg = u"R: 查看设备信息 : DEVICE_ID:[ %10u ] SF_VERSION: %s, RF_CH: %d,  RF_TX_POWER: %d " % \
            (dev_id, sf_version, rf_ch, tx_power)
        self.r_lcd(show_msg)

    def dev_port_wl_msg_update( self, uid_dict, msg, port):
        str_msg = "PORT%d: "% port
        rpos = 0
        port_name = "PORT%d" % port
        uid_dict[port_name] = {}
        uid_dict[port_name]["addr"] = msg[rpos:rpos+4]
        rpos = rpos + 4
        for item in uid_dict[port_name]["addr"]:
            str_msg += "%02X" % item
        uid_dict[port_name]["rf_rx"] = msg[rpos:rpos+1][0]
        str_msg += " RX:%3d" % uid_dict[port_name]["rf_rx"]
        rpos = rpos + 1
        uid_dict[port_name]["rf_tx"] = msg[rpos:rpos+1][0]
        str_msg += " TX:%3d UID:" % uid_dict[port_name]["rf_tx"]
        rpos = rpos + 1
        port1_uid = msg[rpos:]
        rpos = 0
        while rpos < 40: 
            uid = self.uid_neg_code(port1_uid[rpos: rpos+4])
            if uid:
                if uid not in uid_dict["uid_list"]:
                    uid_dict["uid_list"].append(uid)
                    str_msg += " [ %010u ]" % uid
            rpos = rpos + 4
        str_msg += "\r\n"
        return str_msg

    def dev_wl_msg_update(self, uid_dict, dtq, msg):
        uid_dict["uid_list"] = []
        show_msg = u"R: 查看白名单 :\r\n"
        show_msg += self.dev_port_wl_msg_update(uid_dict, msg[0:50], 0)
        show_msg += self.dev_port_wl_msg_update(uid_dict, msg[50:100], 1)
        show_msg += self.dev_port_wl_msg_update(uid_dict, msg[100:150], 2)
        show_msg += self.dev_port_wl_msg_update(uid_dict, msg[150:200], 3)
        self.r_lcd(show_msg)

    '''
        协议上报指令解析函数
    '''
    def answer_cmd_decode(self, uid_dict, msg):
        if msg:
            tree_dict = {}
            rpos = 1
            uid = self.uid_neg_code(msg[rpos:rpos+4])
            if uid != 0:
                if "uid_list" not in uid_dict:
                    uid_dict["uid_list"] = []
                    uid_dict["uid_list"].append(uid)
                else:
                    if uid not in uid_dict["uid_list"]:
                        uid_dict["uid_list"].append(uid)
            dtq = self.get_dtq(uid)
            rpos = rpos + 4  # UID
            rpos = rpos + 4  # SEQ
            r_cmd = msg[rpos:rpos+1][0]
            rpos = rpos + 1  # CMD
            r_len = msg[rpos:rpos+1][0]
            rpos = rpos + 1  # LEN
            if r_cmd in self.decode_cmds:
                tree_dict = self.decode_cmds[r_cmd](uid_dict, dtq, msg[rpos: rpos+r_len])
                return tree_dict
            else:
                str_msg = "R: UNKONW CMD!"
                for item in msg:
                    str_msg += " %02X" % item
                self.r_lcd(str_msg)
                return

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
