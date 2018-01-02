# -*- coding: utf-8 -*-
"""
Created on Sat Apr 22 10:59:35 2017

@author: john
"""
import string
import time
import os
import sys
import platform
import logging
import random
from PyQt4.QtCore import *
from PyQt4.QtGui  import *
from XesCmdDecode import *

# 根据系统 引用不同的库
if platform.system() == "Windows":
    import pywinusb.hid as hid
    from  serial.tools import list_ports
else:
    import usb.core
    from Utils.UsbHelper import usbHelper
    import glob, os, re

LOGTIMEFORMAT = '%Y%m%d%H'
log_time      = time.strftime( LOGTIMEFORMAT,time.localtime(time.time()))
log_name      = "log-%s.txt" % log_time
CH_TEST       = 1

logging.basicConfig ( # 配置日志输出的方式及格式
    level = logging.DEBUG,
    filename = log_name,
    filemode = 'a',
    format = u'[%(asctime)s] %(message)s',
)

class UsbHidMontior(QThread):
    def __init__(self,uid_list,parent=None):
        super(UsbHidMontior,self).__init__(parent)
        self.working = True
        self.new_msg = None
        self.cmd_decode = XesCmdDecode(uid_list)

    def __del__(self):
        self.working = False
        self.wait()

    def run(self):
        while self.working == True:
            if self.new_msg:
                str_msg = self.cmd_decode.xes_cmd_decode(self.new_msg)
                if str_msg != None:
                    self.emit(SIGNAL('usb_r_msg(QString)'),str_msg)
                self.new_msg = None

class DtqUsbHidDebuger(QWidget):
    def __init__(self, parent=None):
        super(DtqUsbHidDebuger, self).__init__(parent)
        self.test_rf_ch = 1
        self.dev_dict = {}
        self.uid_list = []
        self.report   = None
        self.send_msg = u"恭喜你！答对了"
        self.send_cnt = {}
        self.qtree_dict = {}
        self.card_cnt_dict = {}
        self.alive    = False
        self.pp_test_flg = False
        self.xes_encode = XesCmdEncode()
        self.setWindowTitle(u"USB HID压力测试工具v1.6.6")
        self.com_combo=QComboBox(self)
        self.usb_hid_scan()
        self.open_button= QPushButton(u"打开USB设备")
        self.clear_button=QPushButton(u"清空数据")
        self.test_button=QPushButton(u"开始回显压测")
        self.pp_test_button=QPushButton(u"开始单选乒乓")
        self.bind_button=QPushButton(u"开始绑定")
        self.check_conf_button=QPushButton(u"查看配置")
        self.clear_conf_button=QPushButton(u"清除配置")
        self.check_wl_button=QPushButton(u"查看白名单")

        e_hbox = QHBoxLayout()
        e_hbox.addWidget(self.com_combo)
        e_hbox.addWidget(self.open_button)
        e_hbox.addWidget(self.test_button)
        e_hbox.addWidget(self.pp_test_button)
        e_hbox.addWidget(self.clear_button)

        c_hbox = QHBoxLayout()
        self.ch_label=QLabel(u"设置信道：")
        self.ch_lineedit = QLineEdit(u'1')
        self.ch_button=QPushButton(u"修改信道")
        self.cmd_label=QLabel(u"回显功能：")
        self.cmd_lineedit = QLineEdit(u'恭喜你！答对了')
        self.change_button=QPushButton(u"发送数据")
        c_hbox.addWidget(self.ch_label)
        c_hbox.addWidget(self.ch_lineedit)
        c_hbox.addWidget(self.ch_button)
        c_hbox.addWidget(self.bind_button)
        c_hbox.addWidget(self.check_conf_button)
        c_hbox.addWidget(self.clear_conf_button)
        c_hbox.addWidget(self.check_wl_button)

        k_hbox = QHBoxLayout()
        self.k_sum_label=QLabel(u"按键总和:")
        self.k_sum_label.setFont(QFont("Roman times",15,QFont.Bold))
        self.k_sum_lineedit = QLineEdit(u'0')
        self.k_sum_lineedit.setFont(QFont("Roman times",15,QFont.Bold))
        self.r_sum_label=QLabel(u"接收总和:")
        self.r_sum_label.setFont(QFont("Roman times",15,QFont.Bold))
        self.r_sum_lineedit = QLineEdit(u'0')
        self.r_sum_lineedit.setFont(QFont("Roman times",15,QFont.Bold))
        self.k_rate_label=QLabel(u"成功率:")
        self.k_rate_label.setFont(QFont("Roman times",15,QFont.Bold))
        self.k_rate_lineedit = QLineEdit(u'0%')
        self.k_rate_lineedit.setFont(QFont("Roman times",15,QFont.Bold))

        k_hbox.addWidget(self.k_sum_label)
        k_hbox.addWidget(self.k_sum_lineedit)
        k_hbox.addWidget(self.r_sum_label)
        k_hbox.addWidget(self.r_sum_lineedit)
        k_hbox.addWidget(self.k_rate_label)
        k_hbox.addWidget(self.k_rate_lineedit)

        t_hbox = QHBoxLayout()
        t_hbox.addWidget(self.cmd_label)
        t_hbox.addWidget(self.cmd_lineedit)
        t_hbox.addWidget(self.change_button)

        self.q_label=QLabel(u"答题功能：")
        self.q_combo=QComboBox(self)
        self.q_combo.setFixedSize(105, 20)
        self.q_combo.addItem(u"单题单选:0x01")
        self.q_combo.addItem(u"是非判断:0x02")
        self.q_combo.addItem(u"抢红包  :0x03")
        self.q_combo.addItem(u"单题多选:0x04")
        self.q_combo.addItem(u"多题单选:0x05")
        self.q_combo.addItem(u"通用题型:0x06")
        self.q_combo.addItem(u"6键单选 :0x07")
        self.q_combo.addItem(u"停止作答:0x80")
        self.q_lineedit = QLineEdit(u'发送题目测试')
        self.q_button=QPushButton(u"发送题目")

        q_hbox = QHBoxLayout()
        q_hbox.addWidget(self.q_label)
        q_hbox.addWidget(self.q_combo)
        q_hbox.addWidget(self.q_lineedit)
        q_hbox.addWidget(self.q_button)

        self.browser = QTextBrowser ()
        self.browser.setFixedHeight(80)
        self.conf_browser = QTextBrowser ()
        self.conf_browser.setFixedHeight(40)

        self.tree_com = QTreeWidget()
        self.tree_com.setFont(QFont(u"答题器数据统计", 8, False))
        self.tree_com.setColumnCount(9)
        self.tree_com.setHeaderLabels([u'序号',u'uID',u'按键次数',
            u'接收次数',u'回显次数',u'计数初值',u'当前计数值',u'刷卡次数',u'重启次数'])
        self.tree_com.setColumnWidth(0, 50)
        self.tree_com.setColumnWidth(1, 80)
        self.tree_com.setColumnWidth(2, 70)
        self.tree_com.setColumnWidth(3, 70)
        self.tree_com.setColumnWidth(4, 70)
        self.tree_com.setColumnWidth(5, 70)
        self.tree_com.setColumnWidth(6, 70)
        self.tree_com.setColumnWidth(7, 70)
        self.tree_com.setColumnWidth(8, 70)

        box = QVBoxLayout()
        box.addLayout(e_hbox)
        box.addLayout(c_hbox)
        box.addLayout(q_hbox)
        box.addLayout(t_hbox)
        box.addWidget(self.conf_browser)
        box.addWidget(self.browser)
        box.addWidget(self.tree_com)
        box.addLayout(k_hbox)

        self.setLayout(box)
        self.resize(650, 600 )
        self.open_button.clicked.connect(self.btn_event_callback)
        self.clear_button.clicked.connect(self.btn_event_callback)
        self.test_button.clicked.connect(self.btn_event_callback)
        self.change_button.clicked.connect(self.btn_event_callback)
        self.bind_button.clicked.connect(self.btn_event_callback)
        self.ch_button.clicked.connect(self.btn_event_callback)
        self.q_button.clicked.connect(self.btn_event_callback)
        self.check_conf_button.clicked.connect(self.btn_event_callback)
        self.clear_conf_button.clicked.connect(self.btn_event_callback)
        self.check_wl_button.clicked.connect(self.btn_event_callback)
        self.pp_test_button.clicked.connect(self.btn_event_callback)
        self.q_combo.currentIndexChanged.connect(self.update_q_lineedit)
        self.timer = QTimer()
        self.timer.timeout.connect(self.usb_hid_echo_data)

    def update_q_lineedit(self):
        q_type_str = ""
        q_type =  unicode(self.q_combo.currentText())
        if q_type == u"单题单选:0x01":
            q_type_str = u"单题单选"
        if q_type == u"是非判断:0x02":
            q_type_str = u"是非判断"
        if q_type == u"抢红包  :0x03":
            q_type_str = u"抢红包"
        if q_type == u"单题多选:0x04":
            q_type_str = u"单题多选"
        if q_type == u"多题单选:0x05":
            q_type_str = u"多题单选"
        if q_type == u"通用题型:0x06":
            q_type_str = u"通用题型"
        if q_type == u"6键单选 :0x07":
            q_type_str = u"6键单选"
        if q_type == u"停止作答:0x80":
            q_type_str = u"停止作答"
        self.q_lineedit.setText(q_type_str)

    def btn_event_callback(self):
        button = self.sender()
        if button is None or not isinstance(button, QPushButton):
            return
        button_str = button.text()
        if button_str == u"开始回显压测":
            '''
            开始回显压测
            '''
            if self.alive:
                self.test_button.setText(u"停止回显压测")
                self.timer.start(300)

        if button_str == u"停止回显压测":
            '''
            停止回显压测
            '''
            if self.alive:
                self.test_button.setText(u"开始回显压测")
                self.timer.stop()


        if button_str == u"清空数据":
            '''
            清除缓存显示
            '''
            self.browser.clear()

        if button_str == u"发送数据":
            '''
            改变发送数据的内容
            '''
            if self.uid_list:
                for item in self.uid_list:
                    if self.send_cnt.has_key(item):
                        self.send_cnt[item] =self.send_cnt[item] + 1
                    else:
                        self.send_cnt[item] = 1
                    cur_msg   = unicode(self.cmd_lineedit.text())
                    if cur_msg:
                        self.send_msg = cur_msg
                    else:
                        self.send_msg = u"uID:%010d  S_CNT：%d" % (self.xes_encode.uid_negative(item),self.send_cnt[item])
                    msg = self.xes_encode.get_echo_cmd_msg( item, self.send_msg )
                    self.usb_hid_send_msg( msg )

        if button_str == u"发送题目":
            '''
            改变发送数据的内容
            '''
            que_t = 1
            q_type =  unicode(self.q_combo.currentText())
            if q_type == u"单题单选:0x01":
                que_t = 0x01
            if q_type == u"是非判断:0x02":
                que_t = 0x02
            if q_type == u"抢红包  :0x03":
                que_t = 0x03
            if q_type == u"单题多选:0x04":
                que_t = 0x04
            if q_type == u"多题单选:0x05":
                que_t = 0x05
            if q_type == u"通用题型:0x06":
                que_t = 0x06
            if q_type == u"6键单选 :0x07":
                que_t = 0x07
            if q_type == u"停止作答:0x80":
                que_t = 0x80

            if self.alive:
                self.browser.clear()
                cur_msg   = unicode(self.q_lineedit.text())
                msg = self.xes_encode.get_question_cmd_msg( que_t, cur_msg )
                self.usb_hid_send_msg( msg )
                self.browser.append(u"S : 发送题目 : %s : %s " % ( q_type, cur_msg ))

        if button_str == u"开始绑定":
            '''
            发送开始绑定指令
            '''
            if self.alive:
                self.send_msg = u"绑定开始！请将需要测试的答题器刷卡绑定！"
                self.usb_hid_send_msg(self.xes_encode.bind_start_msg)
                self.bind_button.setText(u"停止绑定")
                self.browser.append(u"S : BIND_START: %s " % ( self.send_msg ))

        if button_str == u"停止绑定":
            '''
            发送开始绑定指令
            '''
            if self.alive:
                self.send_msg = u"绑定结束！此时刷卡无效"
                self.usb_hid_send_msg(self.xes_encode.bind_stop_msg)
                self.bind_button.setText(u"开始绑定")
                self.browser.append(u"S : BIND_STOP: %s " % ( self.send_msg ))

        if button_str == u"修改信道":
            if self.alive:
                ch = int(str(self.ch_lineedit.text()))
                self.send_msg = u"修改信道"
                self.usb_hid_send_msg(self.xes_encode.get_ch_cmd_msg(ch))
                self.bind_button.setText(u"开始绑定")
                self.browser.append(u"S : SET_CH: %d %s " % (ch,self.send_msg ))

        if button_str == u"打开USB设备":
            usb_port = str(self.com_combo.currentText())
            if usb_port:
                self.dev_dict[usb_port].open()
                self.dev_dict[usb_port].set_raw_data_handler(self.usb_show_hook)
                self.report = self.dev_dict[usb_port].find_output_reports()
                self.alive  = True
                self.usbhidmonitor = UsbHidMontior(self.uid_list)
                self.connect(self.usbhidmonitor,SIGNAL('usb_r_msg(QString)'),self.usb_cmd_decode)
                self.usbhidmonitor.start()
                self.browser.append(u"打开设备:[ %s ] 成功！" % usb_port )
                self.open_button.setText(u"关闭USB设备")

        if button_str == u"关闭USB设备":
            usb_port = str(self.com_combo.currentText())
            self.alive = False
            if self.dev_dict[usb_port]:
                self.dev_dict[usb_port].close()
                self.report = None
                self.browser.append(u"关闭设备成功！")
            self.open_button.setText(u"打开USB设备")

        if button_str == u"查看配置":
            if self.alive:
                self.send_msg = u"查看设备信息"
                self.usb_hid_send_msg(self.xes_encode.get_device_info_msg)
                self.browser.append(u"S : GET_DEVICE_INFO: %s " % ( self.send_msg ))

        if button_str == u"清除配置":
            if self.alive:
                self.send_msg = u"清除配置信息"
                self.usb_hid_send_msg(self.xes_encode.clear_dev_info_msg)
                self.browser.append(u"S : CLEAR_DEV_INFO: %s " % ( self.send_msg ))
                self.usbhidmonitor.cmd_decode.wl_list = []

        if button_str == u"查看白名单":
            if self.alive:
                self.send_msg = u"查看白名单"
                self.usb_hid_send_msg(self.xes_encode.check_wl)
                self.browser.append(u"S : CHECK_WL: %s " % ( self.send_msg ))

        if button_str == u"开始单选乒乓":
            if self.alive:
                self.pp_test_flg = True
                msg = self.xes_encode.get_question_cmd_msg( 0x01, "" )
                self.usb_hid_send_msg( msg )
                self.pp_test_button.setText(u"停止单选乒乓")

        if button_str == u"停止单选乒乓":
            if self.alive:
                self.pp_test_flg = False
                self.pp_test_button.setText(u"开始单选乒乓")

    def usb_hid_scan(self):
        self.usb_list  = hid.find_all_hid_devices()
        if self.usb_list  :
            for device in self.usb_list:
                device_name = unicode("{0.product_name}").format(device)
                serial_number = unicode("{0.serial_number}").format(device)
                self.com_combo.addItem(device_name+"_"+serial_number)
                self.dev_dict[device_name+"_"+serial_number] = device

    def usb_cmd_decode(self,data):
        if self.usbhidmonitor:
            if self.usbhidmonitor.cmd_decode.conf_log == True:
                self.conf_browser.setText(u"R : {0}".format(data))
            else:
                self.browser.setText(u"R : {0}".format(data))
        key_sum,rev_sum = self.usbhidmonitor.cmd_decode.sum_cal_key_rate()
        self.k_sum_lineedit.setText("%d" % key_sum)
        self.r_sum_lineedit.setText("%d" % rev_sum)
        if key_sum > 0:
             self.k_rate_lineedit.setText("%f" % (rev_sum*100.0/key_sum))
        logging.debug(u"接收数据：R : {0}".format(data))

        if self.usbhidmonitor:
            if len(self.usbhidmonitor.cmd_decode.card_cmd_list) > 0:
                card_id_ack  = [0x01, 0x01, 0x01, 0x96, 0x00]
                card_id_ack[0] = self.usbhidmonitor.cmd_decode.cur_seq
                card_id_ack.append(self.xes_encode.cal_crc(card_id_ack))
                self.usb_hid_send_msg(card_id_ack)

                mg_dict = self.usbhidmonitor.cmd_decode.card_cmd_list.pop(0)
                if self.send_cnt.has_key(mg_dict[u"uid"]):
                    self.send_cnt[mg_dict[u"uid"]] = 1
                self.send_msg = u"uID: %010u" % self.xes_encode.uid_negative(mg_dict[u"uid"])
                tmp_msg = self.xes_encode.get_echo_cmd_msg( mg_dict[u"uid"], self.send_msg )
                tmp_msg.append(self.xes_encode.cal_crc(tmp_msg))
                self.usb_hid_send_msg( tmp_msg )

                if mg_dict[u"uid"] > 0:
                    if self.qtree_dict.has_key(mg_dict[u"uid"]):
                        self.card_cnt_dict[mg_dict[u"uid"]] = self.card_cnt_dict[mg_dict[u"uid"]] + 1
                        self.qtree_dict[mg_dict[u"uid"]].setText(7, str(self.card_cnt_dict[mg_dict[u"uid"]]))
                    else:
                        self.card_cnt_dict[mg_dict[u"uid"]] = 1
                        self.qtree_dict[mg_dict[u"uid"]] = QTreeWidgetItem(self.tree_com)
                        self.qtree_dict[mg_dict[u"uid"]].setText(0, str(len(self.qtree_dict)))
                        uid_str = "%010d" % self.xes_encode.uid_negative(mg_dict[u"uid"])
                        self.qtree_dict[mg_dict[u"uid"]].setText(1, str(uid_str))
                        # self.qtree_dict[mg_dict[u"uid"]].setText(7, str(mg_dict[u"k_c"]))

            if len(self.usbhidmonitor.cmd_decode.echo_cmd_list) > 0:
                answer_ack  = [0x01, 0x01, 0x01, 0x82, 0x00]
                answer_ack[0] = self.usbhidmonitor.cmd_decode.cur_seq
                answer_ack.append(self.xes_encode.cal_crc(answer_ack))
                self.usb_hid_send_msg(answer_ack)

                mg_dict = self.usbhidmonitor.cmd_decode.echo_cmd_list.pop(0)
                self.send_msg  = u"R: %-6d %-6d" % ((mg_dict[u"pra_s"][u"r_s"] % 1000000),(mg_dict[u"r_c"] % 1000000))
                self.send_msg += u"K: %-6d %-6d" % ((mg_dict[u"pra_s"][u"k_s"] % 1000000),(mg_dict[u"k_c"] % 1000000))
                rand_str = ""
                for i in range(8):
                    rand_str = rand_str + "%s" % self.get_rand_gp2312()
                self.send_msg += rand_str
                # self.send_msg += u"E: %-6d %-6d" % ((mg_dict[u"pra_s"][u"e_s"] % 1000000),(mg_dict[u"e_c"] % 1000000))
                tmp_msg = self.xes_encode.get_echo_cmd_msg( mg_dict[u"uid"], self.send_msg )
                tmp_msg.append(self.xes_encode.cal_crc(tmp_msg))
                self.usb_hid_send_msg( tmp_msg )

                if self.pp_test_flg == True:
                    q_msg = self.xes_encode.get_question_cmd_msg( 0x01, u"发送题目乒乓测试" )
                    self.usb_hid_send_msg( q_msg )

                if mg_dict[u"uid"] > 0:
                    if self.qtree_dict.has_key(mg_dict[u"uid"]):
                        self.qtree_dict[mg_dict[u"uid"]].setText(2, str(mg_dict[u"k_c"] - mg_dict[u"pra_s"][u"k_s"]))
                        self.qtree_dict[mg_dict[u"uid"]].setText(3, str(mg_dict[u"r_c"] - mg_dict[u"pra_s"][u"r_s"]))
                        self.qtree_dict[mg_dict[u"uid"]].setText(4, str(mg_dict[u"e_c"] - mg_dict[u"pra_s"][u"e_s"]))
                        self.qtree_dict[mg_dict[u"uid"]].setText(5, str(mg_dict[u"pra_s"][u"k_s"]))
                        self.qtree_dict[mg_dict[u"uid"]].setText(6, str(mg_dict[u"k_c"]))
                        self.qtree_dict[mg_dict[u"uid"]].setText(8, str(mg_dict[u"rst_c"]))
                    else:
                        if mg_dict[u"k_c"] > 0:
                            self.card_cnt_dict[mg_dict[u"uid"]] = 0
                            self.qtree_dict[mg_dict[u"uid"]] = QTreeWidgetItem(self.tree_com)
                            self.qtree_dict[mg_dict[u"uid"]].setText(0, str(len(self.qtree_dict)))
                            uid_str = "%010d" % self.xes_encode.uid_negative(mg_dict[u"uid"])
                            self.qtree_dict[mg_dict[u"uid"]].setText(1, str(uid_str))
                            self.qtree_dict[mg_dict[u"uid"]].setText(2, str(mg_dict[u"k_c"] - mg_dict[u"pra_s"][u"k_s"]))
                            self.qtree_dict[mg_dict[u"uid"]].setText(3, str(mg_dict[u"r_c"] - mg_dict[u"pra_s"][u"r_s"]))
                            self.qtree_dict[mg_dict[u"uid"]].setText(4, str(mg_dict[u"e_c"] - mg_dict[u"pra_s"][u"e_s"]))
                            self.qtree_dict[mg_dict[u"uid"]].setText(7, str(self.card_cnt_dict[mg_dict[u"uid"]]))
                            self.qtree_dict[mg_dict[u"uid"]].setText(8, str(0))

    def usb_show_hook(self,data):
        self.usbhidmonitor.new_msg = data

    def get_rand_gp2312(self):
        head = random.randint(0xb0, 0xf7)
        # 在head区号为55的那一块最后5个汉字是乱码,为了方便缩减下范围
        body = random.randint(0xa1, 0xf9)
        val = (head<<8)|body
        str = "%x" % val
        str_gb2312 = str.decode('hex').decode('gb2312')
        return str_gb2312

    def usb_hid_echo_data(self):
        if self.uid_list:
            for item in self.uid_list:
                if self.send_cnt.has_key(item):
                    self.send_cnt[item] =self.send_cnt[item] + 1
                else:
                    self.send_cnt[item] = 1
                self.send_msg = u"uID:%010d  S_CNT：%-8d" % (self.xes_encode.uid_negative(item),self.send_cnt[item])
                rand_str = ""
                for i in range(8):
                    rand_str = rand_str + "%s" % self.get_rand_gp2312()
                self.send_msg = self.send_msg + rand_str
                msg = self.xes_encode.get_echo_cmd_msg( item, self.send_msg )
                self.usb_hid_send_msg( msg )
                # self.browser.append(u"S : ECHO: CARD_ID:[%010d] str:%s" % ( self.xes_encode.uid_negative(item), self.send_msg ))

    def usb_hid_echo_test(self):
        if self.uid_list:
            for item in self.uid_list:
                msg = self.xes_encode.get_echo_cmd_msg( item, self.send_msg )
                self.usb_hid_send_msg( msg )
                self.browser.append(u"S : ECHO: CARD_ID:[%010d] str:%s" % ( self.xes_encode.uid_negative(item), self.send_msg ))

    def usb_hid_send_msg(self,msg):
        tmp_msg = []
        for item in msg:
            tmp_msg.append(item)

        tmp_msg.insert(0, 0x00)
        datalen = len(tmp_msg)
        i = 0

        str_msg = ""
        for i in range(65):
            if i >= datalen:
                tmp_msg.append(0x00)
        if self.report:
            self.report[0].set_raw_data(tmp_msg)
            self.report[0].send()
            tmp_msg = self.usbhidmonitor.cmd_decode.list_export(tmp_msg)
            logging.debug(u"发送数据：S : {0}".format(tmp_msg))

if __name__=='__main__':
    app = QApplication(sys.argv)
    datburner = DtqUsbHidDebuger()
    datburner.show()
    app.exec_()

