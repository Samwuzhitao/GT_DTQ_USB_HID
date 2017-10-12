
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
    def __init__(self,uid_list):
        self.new_uid = None
        self.cur_seq = None
        self.cur_cmd = None
        self.wl_list = uid_list
        self.cmd_arr = []
        self.ReviceFunSets = {
            0x93 : self.get_device_info,
            0x95 : self.bind_msg_err,
            0x97 : self.bind_msg_err,
            0x83 : self.echo_msg_err,
            0x16 : self.update_card_info,
            0x02 : self.update_answer_info,
            0x98 : self.check_wl_info
        }

    def check_wl_info(self,data):
        # check_wl_info
        pack_len = len(data)
        i = 0
        show_str = "WL: WL_LEN = %d " % (pack_len/4)
        while i < pack_len/4:
            tmp_uid = ((data[4*i+0] << 24)| (data[1+4*i]<<16) | (data[2+4*i] << 8) | data[3+4*i] )
            i = i + 1
            if tmp_uid not in self.wl_list:
                self.wl_list.append(tmp_uid)
                show_str += " uID:%010d " % self.uid_negative(tmp_uid)
        print show_str
        return show_str

    def get_dec_uid(self,uid_arr):
        return ((uid_arr[0] << 24)| (uid_arr[1]<<16) |
               (uid_arr[2] << 8) | uid_arr[3] )

    def uid_negative(self,uid):
        return (((uid & 0xFF000000)>>24) |
               ((uid & 0x00FF0000)>>8)  |
               ((uid & 0x0000FF00)<<8)  |
               ((uid & 0x000000FF)<<24))

    def list_export(self,data):
        str_data = ""
        for item in data:
            str_data += "%02X " % item
        return str_data

    def xes_cmd_decode(self,data_msg):
        # print "cmd decode"
        self.cur_seq = data_msg[SEQ]
        self.cur_cmd = data_msg[CMD]

        print "SEQ:%02x CMD:%02X" % ( self.cur_seq, data_msg[CMD] )
        str_data = ""
        for item in data_msg:
            str_data += "%02X " % item
        print str_data
        # print "SRC_MS  :%s" %  self.list_export(data_msg)
        value_msg = data_msg[DATA_S:DATA_S+data_msg[LEN]]
        for item in value_msg:
            self.cmd_arr.append(item)
        # print "VALUE_MS:%s" %  self.list_export(value_msg)
        if self.ReviceFunSets.has_key(data_msg[CMD]):
            if data_msg[NUM] == data_msg[INDEX]:
                # self.cmd_arr
                str_msg = self.ReviceFunSets[data_msg[CMD]](self.cmd_arr)
                self.cmd_arr = []
                return str_msg

    def get_device_info(self,data):
        show_str  = "uID  = %d "  % (self.uid_negative(self.get_dec_uid(data[0:4])))
        show_str  += " SW  = %d.%d.%d " % (data[4],data[5],data[6])
        # show_str  += " HW  = " + ",".join(data[7:7+15])
        show_str  += " RF_CH  = %d " % (data[7+15+8])
        show_str  += " TX_POWER  = %d" % (data[7+15+8+1])
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
        show_str  = "Err  = %s"  % str_err
        return show_str

    def bind_msg_err(self,data):
        print data
        if data[0] == 0:
            str_err = u"OK!"
        else:
            str_err = u"FIAL!"
        show_str  = "Err  = %s"  % str_err
        return show_str

    def update_card_info(self,data):
        # update_card_id_ack
        print data
        uid = ((data[0]<<24) | (data[1]<<16) |
               (data[2] << 8) | data[3])
        rep_id = ((data[4]<<24) | (data[5]<<16) |
               (data[6] << 8) | data[7])
        show_str  = "UID  = %08X CARD_ID = %010d REP_ID = %010d"  % (uid,self.uid_negative(uid),self.uid_negative(rep_id))
        self.new_uid = uid
        # if uid not in self.wl_list:
        #     self.wl_list.append(uid)
        return show_str

    def update_answer_info(self,data):
        # update_card_id_ack
        show_str = update_time = "[%02X%02X-%02X-%02X %02X:%02X:%02X,%X%02X] " % (data[1],data[2],data[3],data[4],data[5],data[6],data[7],data[8],data[9])
        uid = ((data[10]<<24) | (data[11]<<16) |
               (data[12] << 8) | data[13])
        show_str  += "RSSI = %3d CARD_ID = %010d "  % (data[0],self.uid_negative(uid))
        if data[14] == 1:
            q_type = u"单题单选"
        if data[14] == 2:
            q_type = u"是非判断"
        if data[14] == 3:
            q_type = u"抢红包"
        if data[14] == 4:
            q_type = u"单题多选"
        if data[14] == 5:
            q_type = u"多题单选"
        if data[14] == 6:
            q_type = u"通用题型"
        show_str = show_str + "TYPE =  %s ANSWER: " % q_type

        answer_code = data[15:]
        for item in answer_code:
            if item != 0:
                show_str = show_str + "%02x " % item
        self.new_uid = uid
        return show_str

class XesCmdEncode():
    def __init__(self):
        self.s_seq = 1
        self.get_device_info_msg = [0x01, 0x01, 0x01, 0x13, 0x00, 0x12]
        self.bind_start_msg      = [0x01, 0x01, 0x01, 0x15, 0x00, 0x14]
        self.bind_stop_msg       = [0x01, 0x01, 0x01, 0x17, 0x00, 0x16]
        self.update_card_id_ack  = [0x01, 0x01, 0x01, 0x96, 0x00]
        self.check_wl            = [0x01, 0x01, 0x01, 0x18, 0x00, 0x19]
        self.s_cmd_fun = {
            u"查看设备信息" : self.get_device_info_msg,
            u"绑定开始指令" : self.bind_start_msg,
            u"绑定结束指令" : self.bind_stop_msg,
        }

    def uid_negative(self,uid):
        return (((uid & 0xFF000000)>>24) |
               ((uid & 0x00FF0000)>>8)  |
               ((uid & 0x0000FF00)<<8)  |
               ((uid & 0x000000FF)<<24))

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

    def seq_add(self):
        self.s_seq = (self.s_seq + 1 ) % 255
        if self.s_seq == 0:
            self.s_seq = 1

    def get_ch_cmd_msg(self,ch):
        ch_msg = [0x01, 0x01, 0x01, 0x11, 0x01]
        self.seq_add()
        ch_msg[0] = self.s_seq
        if ch <= 50:
            ch_msg.append(ch)
        ch_msg.append(self.cal_crc(ch_msg))
        return ch_msg

    def get_echo_cmd_msg(self,uid,msg):
        echo_msg = [0x01, 0x01, 0x01, 0x03, 0x34]
        self.seq_add()
        echo_msg[0] = self.s_seq
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

    def get_question_cmd_msg(self,q_t,msg):
        que_msg = [0x01, 0x01, 0x01, 0x01, 0x1A, 0x20, 0x17, 0x08, 0x28, 0x17, 0x53, 0x35, 0x06, 0x00]
        self.seq_add()
        que_msg[0] = self.s_seq
        que_msg.append(q_t)
        msg_arr  = self.get_gbk_hex_arr(msg)
        for item in msg_arr:
            que_msg.append(item)
        for i in range(32):
            if i > len(que_msg):
                que_msg.append(0x00)
        que_msg.append(self.cal_crc(que_msg))
        return que_msg

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

