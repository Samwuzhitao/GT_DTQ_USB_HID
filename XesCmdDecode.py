
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
        self.cur_seq  = None
        self.cur_cmd  = None
        self.old_pac_num_dict = {}
        self.wl_list = uid_list
        self.wl_dict = {}
        self.answer_update_dict = {}
        self.card_update_dict   = {}
        self.test_pra_dict      = {}
        self.par_c_dict     = {}
        self.cmd_arr = {}
        self.echo_cmd_list = []
        self.card_cmd_list = []
        self.ReviceFunSets = {
            0x93 : self.get_device_info,
            0x95 : self.bind_msg_err,
            0x97 : self.bind_msg_err,
            0x83 : self.echo_msg_err,
            0x91 : self.bind_msg_err,
            0x81 : self.bind_msg_err,
            0x94 : self.bind_msg_err,
            0x16 : self.update_card_info,
            0x02 : self.update_answer_info,
            0x98 : self.check_wl_info
        }

    def check_wl_info(self,data):
        pack_len = len(data)
        i = 0
        show_str = "WL: WL_LEN = %d " % (pack_len/4)
        while i < pack_len/4:
            tmp_uid = ((data[4*i+0] << 24)| (data[1+4*i]<<16) | (data[2+4*i] << 8) | data[3+4*i] )
            i = i + 1
            if tmp_uid not in self.wl_list:
                self.wl_list.append(tmp_uid)
            show_str += " uID:%010d " % self.uid_negative(tmp_uid)
        return show_str

    def get_dec_uid(self,uid_arr):
        return ((uid_arr[0] << 24)| (uid_arr[1]<<16) |
               (uid_arr[2] << 8) | uid_arr[3] )

    def uid_negative(self,uid):
        return (((uid & 0xFF000000)>>24) | ((uid & 0x00FF0000)>>8) |
                ((uid & 0x0000FF00)<<8)  | ((uid & 0x000000FF)<<24))

    def list_export(self,data):
        str_data = ""
        for item in data:
            str_data += "%02X " % item
        return str_data

    def msg_same_check(self,new_data,old_data):
        data_str = ""
        for item in new_data:
            data_str += " %02X" % item
        print "NEW_DATA: %s" % data_str

        data_str = ""
        for item in old_data:
            data_str += " %02X" % item
        print "OLD_DATA: %s" % data_str

        for i in range(len(new_data)):
            if new_data[i] != old_data[i]:
                print "NOT SAME",
                return 1
        print "SAME",
        return 0

    def msg_pack_is_same(self,data_msg):
        str_data = ""
        cmd = data_msg[CMD]
        cmd_str = "CMD : %02X" % cmd
        print cmd_str,

        not_same_pack = 1

        if cmd == 0x02:
            uid = ((data_msg[16]<<24) | (data_msg[17]<<16) | (data_msg[18] << 8) | data_msg[19])
            if self.answer_update_dict.has_key(uid):
                str_1 = "uID:%10u " % self.uid_negative(uid)
                print str_1
                not_same_pack = self.msg_same_check(data_msg,self.answer_update_dict[uid])
                if not_same_pack == 1:
                    self.answer_update_dict[uid] = []
                    for item in data_msg:
                        self.answer_update_dict[uid].append(item)
            else:
                self.answer_update_dict[uid] = []
                for item in data_msg:
                    self.answer_update_dict[uid].append(item)
                not_same_pack = 1

        if cmd == 0x16:
            uid = ((data_msg[6]<<24) | (data_msg[7]<<16) | (data_msg[8] << 8) | data_msg[9])
            if self.card_update_dict.has_key(uid):
                str_1 = "uID:%10u " % self.uid_negative(uid)
                print str_1
                not_same_pack = self.msg_same_check(data_msg,self.card_update_dict[uid])
                if not_same_pack == 1:
                    self.card_update_dict[uid] = []
                    for item in data_msg:
                        self.card_update_dict[uid].append(item)
            else:
                self.card_update_dict[uid] = []
                for item in data_msg:
                    self.card_update_dict[uid].append(item)
                not_same_pack = 1

        return not_same_pack

    def xes_cmd_comp(self,data_msg):
        value_msg = data_msg[DATA_S:DATA_S+data_msg[LEN]]
        self.cmd_arr[data_msg[INDEX]] = []
        for item in value_msg:
            self.cmd_arr[data_msg[INDEX]].append(item)
        if data_msg[NUM] == len(self.cmd_arr):
            cmd_arr = []
            for arr_index in range(1,len(self.cmd_arr)+1):
                print arr_index,
                print self.cmd_arr[arr_index]
                for item in self.cmd_arr[arr_index]:
                    cmd_arr.append(item)
            return cmd_arr

    def xes_cmd_decode(self,data_msg):
        self.cur_seq = data_msg[SEQ]
        self.cur_cmd = data_msg[CMD]
        if self.msg_pack_is_same( data_msg ) == 1:
            print "NEW_PACK"
            if self.ReviceFunSets.has_key(data_msg[CMD]):
                value_msg = data_msg[DATA_S:DATA_S+data_msg[LEN]]
                if data_msg[NUM] == 1:
                    # print "NUM:%d INDEX:%d " % (data_msg[NUM],data_msg[INDEX])
                    # print value_msg
                    str_msg = self.ReviceFunSets[data_msg[CMD]]( value_msg )
                    return str_msg
                else:
                    # print "NUM:%d INDEX:%d " % (data_msg[NUM],data_msg[INDEX])
                    cmd = self.xes_cmd_comp( data_msg )
                    if cmd:
                        str_msg = self.ReviceFunSets[data_msg[CMD]](cmd)
                        self.cmd_arr = {}
                        if str_msg:
                            return str_msg
        else:
            print "OLD_PACK "


    def get_device_info(self,data):
        # print data
        show_str  = "uID  = %d "  % (self.uid_negative(self.get_dec_uid(data[0:4])))
        show_str  += " SW  = %d.%d.%d " % (data[4],data[5],data[6])
        show_str  += " RF_CH  = %d " % (data[7+15+8])
        show_str  += " TX_POWER  = %d" % (data[7+15+8+1])
        return show_str

    def echo_msg_err(self,data):
        str_err = ""
        if data[0] == 0:
            str_err = u"OK!"
        if data[0] == 2:
            str_err = u"未知设备,请先绑定！"
        if data[0] == 1:
            str_err = u"指令长度非法"
        show_str  = u"ECHO_ERR = %s"  % str_err
        return show_str

    def bind_msg_err(self,data):
        # print data
        if data[0] == 0:
            str_err = u"OK!"
        else:
            str_err = u"FIAL!"
        show_str  = "Err  = %s"  % str_err
        return show_str

    def update_card_info(self,data):
        uid    = ((data[0]<<24) | (data[1]<<16) | (data[2] << 8) | data[3])
        rep_id = ((data[4]<<24) | (data[5]<<16) | (data[6] << 8) | data[7])
        show_str  = "UID  = %08X CARD_ID = %010d REP_ID = %010d"  % \
                            (uid,self.uid_negative(uid),self.uid_negative(rep_id))

        cur_cmd_dict = {}
        cur_cmd_dict[u"uid"]     = uid
        cur_cmd_dict[u"rep_uid"] = rep_id
        self.card_cmd_list.append(cur_cmd_dict)

        if uid not in self.wl_list:
            self.wl_list.append(uid)
        return show_str

    def update_answer_info(self,data):
        uid = ((data[10]<<24) | (data[11]<<16) | (data[12] << 8) | data[13])

        show_str = "[%02X%02X-%02X-%02X %02X:%02X:%02X,%X%02X] " % \
           (data[1],data[2],data[3],data[4],data[5],data[6],data[7],data[8],data[9])

        show_str  += "RSSI:%3d uID:%010d "  % (data[0],self.uid_negative(uid))

        press_cnt    = ((data[17]<<24) | (data[16]<<16) | (data[15] << 8) | data[14])
        press_ok_cnt = ((data[21]<<24) | (data[20]<<16) | (data[19] << 8) | data[18])
        key_cnt      = ((data[25]<<24) | (data[24]<<16) | (data[23] << 8) | data[22])
        echo_cnt     = ((data[29]<<24) | (data[28]<<16) | (data[27] << 8) | data[26])
        show_str  += "PRESS_CNT:%d PRESS_OK_CNT:%d KEY_CNT:%d ECHO_CNT:%d "  % (press_cnt,press_ok_cnt,key_cnt,echo_cnt)
        LOST_str = ""
        if self.wl_dict.has_key(uid):
            if self.wl_dict[uid] + 1 != key_cnt:
                LOST_str = " LOST PACK! "


        cur_cmd_dict = {}
        cur_cmd_dict[u"uid"] = uid

        if key_cnt == 1:
            self.wl_dict[uid] = 1
        else:
            if self.wl_dict.has_key(uid):
                self.wl_dict[uid] = self.wl_dict[uid] + 1
            else:
                pra_s_dict = {}
                self.wl_dict[uid] = key_cnt
                # self.cal_press_dict[uid] = key_cnt
                pra_s_dict[u"uid"]   = uid
                pra_s_dict[u"r_s"]   = key_cnt
                pra_s_dict[u"k_s"]   = key_cnt
                pra_s_dict[u"e_s"]   = echo_cnt
                pra_s_dict[u"p_s"]   = press_cnt
                pra_s_dict[u"p_o_s"] = press_ok_cnt
                self.test_pra_dict[uid] = pra_s_dict


        show_str = show_str + "TYPE:%02X ANSWER: " % data[30]

        answer_code = data[31:]
        for item in answer_code:
            if item != 0:
                show_str = show_str + "%02x " % item

        # if key_cnt - self.wl_dict[uid] != 1:
        show_str += LOST_str

        cur_cmd_dict[u"p_c"]   = press_cnt
        cur_cmd_dict[u"p_o_c"] = press_ok_cnt
        cur_cmd_dict[u"r_c"]   = self.wl_dict[uid]
        cur_cmd_dict[u"k_c"]   = key_cnt
        cur_cmd_dict[u"e_c"]   = echo_cnt
        cur_cmd_dict[u"pra_s"] = self.test_pra_dict[uid]

        self.par_c_dict[uid] = key_cnt
        self.echo_cmd_list.append(cur_cmd_dict)

        self.cal_ok()

        return show_str

    def cal_ok(self):
        rev_sum = 1
        key_sum = 1
        show_str = ""
        for item in self.wl_dict:
            cal_r = self.wl_dict[item]    - self.test_pra_dict[item][u"r_s"]
            cal_k = self.par_c_dict[item] - self.test_pra_dict[item][u"k_s"]
            cal_str = u"uID:%010u R:%d K:%d \r\n" % ( self.uid_negative(item), cal_r, cal_k )
            show_str = show_str + cal_str
            rev_sum = rev_sum + cal_r
            key_sum = key_sum + cal_k
        show_str = show_str + u"按键成功率: KEY_SUM=%-10d  R_SUM=%-10d  成功率：%f%% \r\n" % ( rev_sum, key_sum, rev_sum * 100/ key_sum)
        return show_str

class XesCmdEncode():
    def __init__(self):
        self.s_seq = 1
        self.get_device_info_msg = [0x01, 0x01, 0x01, 0x13, 0x00, 0x12]
        self.bind_start_msg      = [0x01, 0x01, 0x01, 0x15, 0x00, 0x14]
        self.bind_stop_msg       = [0x01, 0x01, 0x01, 0x17, 0x00, 0x16]
        self.check_wl            = [0x01, 0x01, 0x01, 0x18, 0x00, 0x19]
        self.clear_dev_info_msg  = [0x01, 0x01, 0x01, 0x14, 0x00, 0x15]
        self.s_cmd_fun = {
            u"查看设备信息" : self.get_device_info_msg,
            u"绑定开始指令" : self.bind_start_msg,
            u"绑定结束指令" : self.bind_stop_msg,
        }

    def uid_negative(self,uid):
        return (((uid & 0xFF000000)>>24) | ((uid & 0x00FF0000)>>8)  |
                ((uid & 0x0000FF00)<<8)  | ((uid & 0x000000FF)<<24))

    def get_gbk_hex_arr(self,msg):
        msg_arr = []
        imsg = msg.encode("gbk")
        for item in imsg:
            msg_arr.append(ord(item))
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
        ch_msg.append(ch & 0xFF)
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
        # str_msg = ''
        # for item in echo_msg:
        #     str_msg = str_msg + "%02X " % item
        # print "CMD_PACK :   " + str_msg
        return echo_msg

    def get_question_cmd_msg(self,q_t,msg):
        que_msg = [0x01, 0x01, 0x01, 0x01, 0x0A, 0x20, 0x17, 0x08, 0x28, 0x17, 0x53, 0x35, 0x06, 0x00]
        self.seq_add()
        que_msg[0] = self.s_seq
        que_msg.append(q_t)
        msg_arr  = self.get_gbk_hex_arr(msg)
        msg_arr_len = len(msg_arr)
        if msg_arr_len > 0:
            que_msg[4] = 0x1A
            for item in msg_arr:
                que_msg.append(item)
            for i in range(32):
                if i > len(que_msg):
                    que_msg.append(0x00)
        que_msg.append(self.cal_crc(que_msg))
        # print que_msg
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

