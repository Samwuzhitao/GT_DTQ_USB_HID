
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
        self.new_uid = None
        self.ReviceFunSets = {
            0x93 : self.get_device_info,
            0x95 : self.bind_msg_err,
            0x97 : self.bind_msg_err,
            0x83 : self.echo_msg_err,
            0x16 : self.update_card_info
        }

    def get_dec_uid(self,uid_arr):
        return ((uid_arr[0]<<24) | (uid_arr[1]<<16) |
               (uid_arr[2] << 8) | uid_arr[3])

    def list_export(self,data):
        str_data = ""
        for item in data:
            str_data += "%02X " % item
        return str_data

    def xes_cmd_decode(self,data_msg):
        # print "cmd decode"
        print "%02X " % data_msg[CMD]
        # print "SRC_MS  :%s" %  self.list_export(data_msg)
        value_msg = data_msg[DATA_S:DATA_S+data_msg[LEN]]
        # print "VALUE_MS:%s" %  self.list_export(value_msg)
        if self.ReviceFunSets.has_key(data_msg[CMD]):
            str_msg = self.ReviceFunSets[data_msg[CMD]](value_msg)
            return str_msg

    def get_device_info(self,data):
        show_str  = " uID  = %d"  % (self.get_dec_uid(data[0:4]))
        show_str  += " SW  = %d.%d.%d" % (data[4],data[5],data[6])
        # show_str  += " HW  = " + ",".join(data[7:7+15])
        # print show_str
        return show_str

    def echo_msg_err(self,data):
        # print data
        if data[0] == 0:
            str_err = u"OK!"
        if data[0] == 2:
            str_err = u"未知设备,请先绑定！"
        if data[0] == 1:
            str_err = u"指令长度非法"
        show_str  = " Err  = %s"  % str_err
        return show_str

    def bind_msg_err(self,data):
        print data
        if data[0] == 0:
            str_err = u"OK!"
        else:
            str_err = u"FIAL!"
        show_str  = " Err  = %s"  % str_err
        return show_str

    def update_card_info(self,data):
        uid = ((data[0]<<24) | (data[1]<<16) |
               (data[2] << 8) | data[3])
        show_str  = " UID  = %08X"  % uid
        self.new_uid = uid
        return show_str

class XesCmdEncode():
    def __init__(self):
        self.get_device_info_msg = [0x01, 0x01, 0x01, 0x13, 0x00, 0x12]
        self.bind_start_msg      = [0x01, 0x01, 0x01, 0x15, 0x00, 0x14]
        self.bind_stop_msg       = [0x01, 0x01, 0x01, 0x17, 0x00, 0x16]
        self.update_card_id_ack  = [0x01, 0x01, 0x01, 0x96, 0x00, 0x97]
        self.s_cmd_fun = {
            u"查看设备信息" : self.get_device_info_msg,
            u"绑定开始指令" : self.bind_start_msg,
            u"绑定结束指令" : self.bind_stop_msg,
        }

    def get_gbk_hex_arr(self,msg):
        msg_arr = []
        imsg = msg.encode("gbk")
        for item in imsg:
            msg_arr.append(ord(item))
        # print u"gbk_to_arr:{0}".format(msg_arr)
        return msg_arr

    def get_uid_hex_arr(self,uid):
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

    def cal_crc(self,arr_msg):
        crc = 0
        for item in arr_msg:
            crc = crc^item
        return crc

    def get_echo_cmd_msg(self,uid,msg):
        echo_msg = [0x01, 0x01, 0x01, 0x03, 0x34]
        uid_arr  = self.get_uid_hex_arr(uid)
        for item in uid_arr:
            echo_msg.append(item)
        msg_arr  = self.get_gbk_hex_arr(msg)
        for item in msg_arr:
            echo_msg.append(item)
        for i in range(58):
            if i > len(echo_msg):
                echo_msg.append(0x00)

        echo_msg.append(self.cal_crc(echo_msg))

        return echo_msg

if __name__=='__main__':
    uid_arr = [0x01,0x02,0x03,0x04]
    xes_decode = XesCmdDecode()
    xes_encode = XesCmdEncode()
    print "src       :",
    print uid_arr
    uid_dec = xes_decode.get_dec_uid(uid_arr)
    print "Arr to dec:",
    print uid_dec
    print "Dec to arr:",
    print xes_encode.get_uid_hex_arr(uid_dec)
    print u"输入回下参数：%d %s" %  (uid_dec, u"测试")
    echo_arr = xes_encode.get_echo_cmd_msg( 0x061D942D,u"恭喜你！答对了")
    print u"输出指令数组：",
    echo_arr_str = ""
    for item in echo_arr:
        echo_arr_str += "%02X " % item
    print echo_arr_str

