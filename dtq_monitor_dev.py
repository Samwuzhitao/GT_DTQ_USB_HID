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

class monitor_cmd_decode():
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
            return

        if self.sts == 1:
            self.cmd.append(char)
            self.sts = 2
            self.cnt = 2
            return

        if self.sts == 2:
            self.cmd.append(char)
            self.cnt = self.cnt - 1
            if self.cnt == 0:
                self.sts = 3
                self.cnt = (self.cmd[2]  & 0xFF ) | ((self.cmd[3] << 8) & 0xFF00)
            return

        if self.sts == 3:
            self.cmd.append(char)
            self.cnt = self.cnt - 1
            if self.cnt == 0:
                self.sts = 4
            return

        if self.sts == 4:
            self.cmd.append(char)
            if char == 0x21:
                self.sts = 0
                print self.cmd
                return self.cmd
            else:
                self.cmd = []
                return


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
                    print self.cmd
                    return self.cmd
            return


class dtq_monitor_dev():
    def __init__(self):
        self.PAC_LEN = 252
        self.decode_cmds = {}

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
    def get_dev_info_msg(self):
        cmd = "61 30 00 00 21"
        cmd = str(cmd.replace(' ',''))
        cmd = cmd.decode("hex")
        return cmd
    # 设置端口指令
    def get_rf_set_msg(self, addr, rx_ch, tx_ch, esb_mode):
        cmd = "61 01 07 00"
        cmd += "%02X" % addr[0]
        cmd += "%02X" % addr[1]
        cmd += "%02X" % addr[2]
        cmd += "%02X" % addr[3]
        cmd += "%02X" % rx_ch
        cmd += "%02X" % tx_ch
        cmd += "%02X" % esb_mode
        cmd += "21"
        cmd = str(cmd.replace(' ',''))
        cmd = cmd.decode("hex")
        return cmd
    # 发送数据指令
    def send_data_cmd(self, arr_msg):
        cmd = "61 10"
        cmd += "%02X" % (len(arr_msg) & 0xFF)
        cmd += "%02X" % (((len(arr_msg) & 0xFF00) >> 8) & 0xFF)
        for item in arr_msg:
            cmd += "%02X" % (item)
        cmd += "21"
        cmd = str(cmd.replace(' ',''))
        cmd = cmd.decode("hex")
        return cmd
        

