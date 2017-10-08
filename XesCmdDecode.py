
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 22 10:59:35 2017

@author: john
"""
import string

SEQ    = 1
NUM    = 2
INDEX  = 3
CMD    = 4
LEN    = 5
DATA_S = 6

class XesCmdDecode():
    def __init__(self):
        self.ReviceFunSets = {
            0x93 : self.get_device_info
        }

    def list_export(self,data):
        str_data = ""
        for item in data:
            str_data += "%02X " % item
        return str_data

    def xes_cmd_decode(self,data_msg):
        # print "cmd decode"
        # print "%02X " % data_msg[CMD]
        # print "SRC_MS  :%s" %  self.list_export(data_msg)
        value_msg = data_msg[DATA_S:DATA_S+data_msg[LEN]]
        # print "VALUE_MS:%s" %  self.list_export(value_msg)
        str_msg = self.ReviceFunSets[data_msg[CMD]](value_msg)
        return str_msg

    def get_device_info(self,data):
        show_str  = " ID  = %02x%02x%02x%02x"  % (data[0],data[1],data[2],data[3])
        show_str  += " SW  = %d.%d%d" % (data[4],data[5],data[6])
        # show_str  += " HW  = " + ",".join(data[7:7+15])
        # print show_str
        return show_str





class XesCmdEncode():
    def __init__(self):
        self.get_device_info_msg = [0x01, 0x01, 0x01, 0x13, 0x00, 0x12]
        self.bind_start_msg      = [0x01, 0x01, 0x01, 0x15, 0x00, 0x14]
        self.bind_stop_msg       = [0x01, 0x01, 0x01, 0x17, 0x00, 0x16]
        self.s_cmd_fun = {
            u"查看设备信息" : self.get_device_info_msg,
            u"绑定开始指令" : self.bind_start_msg,
            u"绑定结束指令" : self.bind_stop_msg,
        }

    def get_echo_cmd_msg(self,uid,msg):
        self.echo_msg = [0x01, 0x01, 0x01, 0x03, 0x34]
