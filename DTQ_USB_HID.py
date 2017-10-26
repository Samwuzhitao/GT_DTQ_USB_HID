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
from PyQt4.QtCore import *
from PyQt4.QtGui  import *
from XesCmdDecode import *

# 根据系统 引用不同的库
if platform.system() == "Windows":
    import pywinusb.hid as hid
    # from Utils.WinUsbHelper import hidHelper
    from  serial.tools import list_ports
else:
    import usb.core
    from Utils.UsbHelper import usbHelper
    import glob, os, re

LOGTIMEFORMAT = '%Y%m%d%H'
log_time      = time.strftime( LOGTIMEFORMAT,time.localtime(time.time()))
log_name      = "log-%s.txt" % log_time

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
                if str_msg:
                    self.emit(SIGNAL('usb_r_msg(QString)'),str_msg)
                self.new_msg = None

class DtqUsbHidDebuger(QWidget):
    def __init__(self, parent=None):
        super(DtqUsbHidDebuger, self).__init__(parent)
        self.dev_dict = {}
        # self.usb_list = []
        self.uid_list = []
        self.report   = None
        self.send_msg = u"恭喜你！答对了"
        self.send_cnt = {}
        self.alive    = False
        # self.xes_decode = XesCmdDecode()
        self.xes_encode = XesCmdEncode()
        self.setWindowTitle(u"USB HID压力测试工具v1.5")
        self.com_combo=QComboBox(self)
        self.com_combo.setFixedSize(100, 20)
        self.usb_hid_scan()
        self.open_button= QPushButton(u"打开USB设备")
        self.clear_button=QPushButton(u"清空数据")
        self.test_button=QPushButton(u"开始压力测试")
        self.bind_button=QPushButton(u"开始绑定")

        self.check_conf_button=QPushButton(u"查看配置")
        self.clear_conf_button=QPushButton(u"清除配置")
        self.check_wl_button=QPushButton(u"查看白名单")

        e_hbox = QHBoxLayout()
        e_hbox.addWidget(self.com_combo)
        e_hbox.addWidget(self.open_button)
        e_hbox.addWidget(self.test_button)
        e_hbox.addWidget(self.clear_button)

        self.ch_label=QLabel(u"设置信道：")
        self.ch_lineedit = QLineEdit(u'1')
        self.ch_button=QPushButton(u"修改信道")

        self.cmd_label=QLabel(u"回显功能：")
        self.cmd_lineedit = QLineEdit(u'恭喜你！答对了')
        self.change_button=QPushButton(u"发送数据")
        c_hbox = QHBoxLayout()

        c_hbox.addWidget(self.ch_label)
        c_hbox.addWidget(self.ch_lineedit)
        c_hbox.addWidget(self.ch_button)
        c_hbox.addWidget(self.bind_button)
        c_hbox.addWidget(self.check_conf_button)
        c_hbox.addWidget(self.clear_conf_button)
        c_hbox.addWidget(self.check_wl_button)

        t_hbox = QHBoxLayout()
        t_hbox.addWidget(self.cmd_label)
        t_hbox.addWidget(self.cmd_lineedit)
        t_hbox.addWidget(self.change_button)

        self.q_label=QLabel(u"答题功能：")
        self.q_combo=QComboBox(self)
        self.q_combo.setFixedSize(105, 20)
        # self.usb_hid_scan()
        self.q_combo.addItem(u"单题单选:0x01")
        self.q_combo.addItem(u"是非判断:0x02")
        self.q_combo.addItem(u"抢红包  :0x03")
        self.q_combo.addItem(u"单题多选:0x04")
        self.q_combo.addItem(u"多题单选:0x05")
        self.q_combo.addItem(u"通用题型:0x06")
        self.q_combo.addItem(u"停止作答:0x80")
        self.q_lineedit = QLineEdit(u'单题单选测试1')
        self.q_button=QPushButton(u"发送题目")

        q_hbox = QHBoxLayout()

        q_hbox.addWidget(self.q_label)
        q_hbox.addWidget(self.q_combo)
        q_hbox.addWidget(self.q_lineedit)
        q_hbox.addWidget(self.q_button)

        self.browser = QTextBrowser ()
        # self.browser.document().setMaximumBlockCount (500);
        box = QVBoxLayout()

        box.addLayout(e_hbox)

        box.addLayout(c_hbox)
        box.addLayout(q_hbox)
        box.addLayout(t_hbox)
        box.addWidget(self.browser)
        self.setLayout(box)
        self.resize(600, 400 )
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

        self.q_combo.currentIndexChanged.connect(self.update_q_lineedit)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)

    def update_time(self):
        self.usb_hid_echo_data()

    def update_q_lineedit(self):
        q_type =  unicode(self.q_combo.currentText())
        self.q_lineedit.setText(q_type)

    def btn_event_callback(self):
        button = self.sender()
        if button is None or not isinstance(button, QPushButton):
            return
        button_str = button.text()
        if button_str == u"开始压力测试":
            '''
            开始压力测试
            '''
            if self.alive:
                self.test_button.setText(u"停止压力测试")
                self.timer.start(1000)

        if button_str == u"停止压力测试":
            '''
            停止压力测试
            '''
            if self.alive:
                self.test_button.setText(u"开始压力测试")
                self.timer.stop()


        if button_str == u"清空数据":
            '''
            清除缓存显示
            '''
            self.browser.clear()
            self.browser.append(u"============================================================")
            self.browser.append(self.usbhidmonitor.cmd_decode.cal_ok())
            self.browser.append(u"============================================================")

        if button_str == u"发送数据":
            '''
            改变发送数据的内容
            '''
            cur_msg   = unicode(self.cmd_lineedit.text())
            if cur_msg:
                self.send_msg = cur_msg
            self.usb_hid_echo_data()

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
            if q_type == u"停止作答:0x80":
                que_t = 0x80

            if self.alive:
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
            '''
            关闭HID设备
            '''
            if self.alive:
                ch = int(str(self.ch_lineedit.text()))
                self.send_msg = u"修改信道"
                self.usb_hid_send_msg(self.xes_encode.get_ch_cmd_msg(ch))
                self.bind_button.setText(u"开始绑定")
                self.browser.append(u"S : SET_CH: %d %s " % (ch,self.send_msg ))

        if button_str == u"打开USB设备":
            '''
             打开HID设备
            '''
            usb_port = str(self.com_combo.currentText())
            if usb_port:
                self.dev_dict[usb_port].open()
                self.dev_dict[usb_port].set_raw_data_handler(self.usb_show_hook)
                self.report = self.dev_dict[usb_port].find_output_reports()
                self.alive  = True
                # print self.report
                self.usbhidmonitor = UsbHidMontior(self.uid_list)
                self.connect(self.usbhidmonitor,SIGNAL('usb_r_msg(QString)'),self.usb_cmd_decode)
                # print self.dev_dict[usb_port]
                self.usbhidmonitor.start()
                self.browser.append(u"打开设备成功！")
                self.open_button.setText(u"关闭USB设备")

        if button_str == u"关闭USB设备":
            '''
            关闭HID设备
            '''
            usb_port = str(self.com_combo.currentText())
            self.alive = False
            if self.dev_dict[usb_port]:
                self.dev_dict[usb_port].close()
                self.report = None
                self.browser.append(u"关闭设备成功！")
            self.open_button.setText(u"打开USB设备")


        if button_str == u"查看配置":
            '''
            查看设备信息
            '''
            if self.alive:
                self.send_msg = u"查看设备信息"
                self.usb_hid_send_msg(self.xes_encode.get_device_info_msg)
                self.browser.append(u"S : GET_DEVICE_INFO: %s " % ( self.send_msg ))

        if button_str == u"清除配置":
            '''
            查看设备信息
            '''
            if self.alive:
                self.send_msg = u"清除配置信息"
                self.usb_hid_send_msg(self.xes_encode.clear_dev_info_msg)
                self.browser.append(u"S : CLEAR_DEV_INFO: %s " % ( self.send_msg ))
                self.usbhidmonitor.cmd_decode.wl_list = []

        if button_str == u"查看白名单":
            '''
            查看设备信息
            '''
            if self.alive:
                self.send_msg = u"查看白名单"
                self.usb_hid_send_msg(self.xes_encode.check_wl)
                self.browser.append(u"S : CHECK_WL: %s " % ( self.send_msg ))

    def usb_hid_scan(self):
        self.usb_list  = hid.find_all_hid_devices()
        if self.usb_list  :
            for device in self.usb_list:
                device_name = unicode("{0.product_name}").format(device)
                self.com_combo.addItem(device_name)
                self.dev_dict[device_name] = device

    def usb_cmd_decode(self,data):
        self.browser.append(u"R : {0}".format(data))
        logging.debug(u"接收数据：R : {0}".format(data))

        if self.usbhidmonitor:
            if len(self.usbhidmonitor.cmd_decode.card_cmd_list) > 0:
                card_id_ack  = [0x01, 0x01, 0x01, 0x96, 0x00]
                card_id_ack[0] = self.usbhidmonitor.cmd_decode.cur_seq
                card_id_ack.append(self.xes_encode.cal_crc(card_id_ack))
                self.usb_hid_send_msg(card_id_ack)

                cur_msg_dict = self.usbhidmonitor.cmd_decode.card_cmd_list.pop(0)
                if self.send_cnt.has_key(cur_msg_dict[u"uid"]):
                    self.send_cnt[cur_msg_dict[u"uid"]] = 1
                self.send_msg = u"uID: %010u" % self.xes_encode.uid_negative(cur_msg_dict[u"uid"])
                tmp_msg = self.xes_encode.get_echo_cmd_msg( cur_msg_dict[u"uid"], self.send_msg )
                tmp_msg.append(self.xes_encode.cal_crc(tmp_msg))
                self.usb_hid_send_msg( tmp_msg )

            if len(self.usbhidmonitor.cmd_decode.echo_cmd_list) > 0:
                answer_ack  = [0x01, 0x01, 0x01, 0x82, 0x00]
                answer_ack[0] = self.usbhidmonitor.cmd_decode.cur_seq
                answer_ack.append(self.xes_encode.cal_crc(answer_ack))
                self.usb_hid_send_msg(answer_ack)

                cur_msg_dict = self.usbhidmonitor.cmd_decode.echo_cmd_list.pop(0)
                self.send_msg  = u"R: %-6d %-6d" % ((cur_msg_dict[u"pra_s"][u"r_s"] % 1000000),(cur_msg_dict[u"r_c"] % 1000000))
                self.send_msg += u"K: %-6d %-6d" % ((cur_msg_dict[u"pra_s"][u"k_s"] % 1000000),(cur_msg_dict[u"k_c"] % 1000000))
                self.send_msg += u"E: %-6d %-6d" % ((cur_msg_dict[u"pra_s"][u"e_s"] % 1000000),(cur_msg_dict[u"e_c"] % 1000000))
                tmp_msg = self.xes_encode.get_echo_cmd_msg( cur_msg_dict[u"uid"], self.send_msg )
                tmp_msg.append(self.xes_encode.cal_crc(tmp_msg))
                self.usb_hid_send_msg( tmp_msg )
                self.browser.append(u"S : ECHO: CARD_ID:[%010d] str:%s" % ( self.xes_encode.uid_negative(cur_msg_dict[u"uid"]), self.send_msg ))

    def usb_show_hook(self,data):
        self.usbhidmonitor.new_msg = data

    def usb_hid_echo_data(self):
        if self.uid_list:
            for item in self.uid_list:
                if self.send_cnt.has_key(item):
                    self.send_cnt[item] =self.send_cnt[item] + 1
                else:
                    self.send_cnt[item] = 1
                self.send_msg = u"uID:%010d  S_CNT：%d" % (self.xes_encode.uid_negative(item),self.send_cnt[item])
                msg = self.xes_encode.get_echo_cmd_msg( item, self.send_msg )
                self.usb_hid_send_msg( msg )
                self.browser.append(u"S : ECHO: CARD_ID:[%010d] str:%s" % ( self.xes_encode.uid_negative(item), self.send_msg ))

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

