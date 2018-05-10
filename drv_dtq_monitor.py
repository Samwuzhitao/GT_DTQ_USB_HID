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

class dtq_cmd_decode():
    def __init__(self):
        self.sts = 0
        self.cnt = 0
        self.cmd = []

    def r_machine(self,x):
        char = ord(x)
        # print "%02X" % char
        if self.sts == 0:
            self.cmd = []
            if char == 0x61:
                self.cmd.append(char)
                self.sts = 1
                self.cnt = 7
            return

        if self.sts == 1:
            self.cmd.append(char)
            self.cnt = self.cnt - 1
            if self.cnt == 0:
                self.cnt = char
                self.sts = 2
            return

        if self.sts == 2:
            self.cmd.append(char)
            self.cnt = self.cnt - 1
            if self.cnt == 0:
                self.sts = 3
                self.cnt = 2
            return

        if self.sts == 3:
            self.cmd.append(char)
            self.cnt = self.cnt - 1
            if self.cnt == 0:
                if char == 0x21:
                    self.sts = 0
                    # print self.cmd
                    return self.cmd
            return


class dtq_monitor_dev():
    def __init__(self):
        self.PAC_LEN = 252
        self.pac_num = 0
        self.decode_cmds = {
            0x7E: self.voice_data_update,
            0x10: self.answer_data_update
        }
        self.seq = 1

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
        return ((uid_arr[0] << 24) | (uid_arr[1] << 16) |
            (uid_arr[2] << 8) | uid_arr[3])

    def uid_neg_code(self, uid_arr):
        return ((uid_arr[3] << 24) | (uid_arr[2] << 16) |
            (uid_arr[1] << 8) | uid_arr[0])

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

    '''
        协议下发指令生成函数
    '''
    # 查询设备信息指令
    def get_stop_esb_msg(self):
        cmd = "61 05 02 11 22 33 44 00 FF 21"
        cmd = str(cmd.replace(' ',''))
        cmd = cmd.decode("hex")
        return cmd
    # 设置端口指令
    def get_start_esb_msg(self, port, addr, rx_ch, tx_ch, esb_mode):
        cmd = "61 05 01 11 22 33 44 08"
        cmd += "%02X" % port
        cmd += "%02X" % addr[0]
        cmd += "%02X" % addr[1]
        cmd += "%02X" % addr[2]
        cmd += "%02X" % addr[3]
        cmd += "%02X" % rx_ch
        cmd += "%02X" % tx_ch
        cmd += "%02X" % esb_mode
        cmd += "FF 21"
        cmd = str(cmd.replace(' ',''))
        cmd = cmd.decode("hex")
        return cmd
    # 发送数据指令
    def get_send_data_msg(self, arr_msg):
        cmd = "61 05 10"
        seq_arr = self.get_uid_arr_pos(self.seq)
        self.seq = self.seq + 1
        for item in seq_arr:
            cmd += "%02X" % (item)
        cmd += "%02X" % (len(arr_msg) & 0xFF)
        for item in arr_msg:
            cmd += "%02X" % (item)
        cmd += "FF 21"
        cmd = str(cmd.replace(' ',''))
        cmd = cmd.decode("hex")
        return cmd

    # 发送语音测试数据
    def get_voice_test_msg(self, uid):
        cmd = "61 05 7E"
        cmdid_arr = self.get_uid_arr_pos(self.seq)
        self.seq = self.seq + 1
        for item in cmdid_arr:
            cmd += "%02X" % (item)
        # len
        cmd += "%02X" % (208+2+1+4+4+1)
        cmd += "00"   # RSSI
        qid = 1
        seq_arr = self.get_uid_arr_pos(qid)
        for item in seq_arr:
            cmd += "%02X" % (item)
        seq_arr = self.get_uid_arr_pos(uid)
        for item in seq_arr:
            cmd += "%02X" % (item)
        cmd += "00"   # FLG
        cmd += "%02X" % (((self.pac_num & 0xFF00) >> 8) & 0xFF)  # FLG
        cmd += "%02X" % (self.pac_num & 0xFF)
        self.pac_num = (self.pac_num + 1) % 100
        # if
        for pos in range(0,208):
            cmd += "%02X" % (pos)
        cmd += "FF 21"
        cmd = str(cmd.replace(' ',''))
        # print cmd
        cmd = cmd.decode("hex")
        return cmd
        
    '''
        协议指令解析
    '''
    def cmd_decode(self, r_lcd, r_cmd):
        r_pos = 1
        dev = r_cmd[r_pos:r_pos+1][0]
        r_pos = r_pos + 1
        cmd = r_cmd[r_pos:r_pos+1][0]
        r_pos = r_pos + 1
        cmd_id = r_cmd[r_pos:r_pos+4]
        r_pos = r_pos + 4
        pac_len = r_cmd[r_pos:r_pos+1][0]
        r_pos = r_pos + 1
        data = r_cmd[r_pos:r_pos+pac_len]
        r_pos = r_pos + pac_len
        # str_msg = "DEV:%d CMD:%02X CMDID: %08x, DATA:" % (dev, cmd, self.uid_pos_code(cmd_id))
        # for item in data:
        #     str_msg += " %02X" % item
        # r_lcd.put(str_msg)
        if cmd in self.decode_cmds:
            self.decode_cmds[cmd](r_lcd, dev, data)

    def voice_data_update(self, r_lcd, dev, msg):
        r_pos = 0
        rssi = msg[r_pos:r_pos+1][0]
        r_pos = r_pos + 1
        qid_arr = msg[r_pos:r_pos+4]
        r_pos = r_pos + 4
        uid_arr = msg[r_pos:r_pos+4]
        r_pos = r_pos + 4
        str_msg = "[ %d ][ %010u ] " % (dev, self.uid_neg_code(uid_arr))
        flg =  msg[r_pos:r_pos+1][0]
        r_pos = r_pos + 1
        pac_num_arr = msg[r_pos:r_pos+2]
        r_pos = r_pos + 2
        pac_num = pac_num_arr[0] << 8 | pac_num_arr[1]
        str_msg += "flg: %d, pac_num: %3d, mp3_check:" % (flg, pac_num)
        mp3_header = msg[r_pos:r_pos+5]
        for item in mp3_header:
            str_msg += " %02X" % item
        r_lcd.put(str_msg)

    def answer_data_update(self, r_lcd, dev, msg):
        r_pos = 0
        rssi = msg[r_pos:r_pos+1][0]
        r_pos = r_pos + 1
        r_cmd = msg[r_pos:r_pos+1][0]
        r_pos = r_pos + 1  # RF_CMD
        r_pos = r_pos + 1  # RF_LEN
        if r_cmd == 0x02:
            qid_arr = msg[r_pos:r_pos+4]
            r_pos = r_pos + 4
            uid_arr = msg[r_pos:r_pos+4]
            r_pos = r_pos + 4
            str_msg = "[ %d ][ %010u ] " % (dev, self.uid_neg_code(uid_arr))

            str_msg += "POWER:%1d, " % msg[r_pos: r_pos+1][0]
            r_pos = r_pos + 4  # POWER
            str_msg += "PRESS:%6d, " % self.uid_pos_code(msg[r_pos: r_pos+4])
            r_pos = r_pos + 4  # PRESS
            str_msg += "KEY:%6d, " % self.uid_pos_code(msg[r_pos: r_pos+4])
            r_pos = r_pos + 4  # KEY
            str_msg += "SEND:%6d, " % self.uid_pos_code(msg[r_pos: r_pos+4])
            r_pos = r_pos + 4  # SEND
            str_msg += "ECHO:%6d, " % self.uid_pos_code(msg[r_pos: r_pos+4])
            r_pos = r_pos + 4  # ECHO
            answer_type = msg[r_pos: r_pos+1][0]
            str_msg += "TYPE:%x, " % answer_type
            r_pos = r_pos + 1  # TYPE
            if (answer_type < 4) or (answer_type > 5):
                str_msg += "ANSWERS:%x " % (msg[r_pos: r_pos+1][0])
            else:
                str_msg += "ANSWERS:%s " % (u"{0}".format(msg[r_pos: r_pos+16]))
            r_lcd.put(str_msg)





