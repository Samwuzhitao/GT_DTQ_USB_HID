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
    def __init__(self,parent=None):
        super(UsbHidMontior,self).__init__(parent)
        self.working = True
        self.new_msg = None
        self.cmd_decode = XesCmdDecode()

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
        self.send_cnt = 0
        self.alive    = False
        # self.xes_decode = XesCmdDecode()
        self.xes_encode = XesCmdEncode()
        self.setWindowTitle(u"USB HID压力测试工具v1.0")
        self.com_combo=QComboBox(self)
        self.com_combo.setFixedSize(100, 20)
        self.usb_hid_scan()
        self.open_button= QPushButton(u"打开USB设备")
        self.clear_button=QPushButton(u"清空数据")
        self.test_button=QPushButton(u"开始压力测试")
        self.bind_button=QPushButton(u"开始绑定")
        e_hbox = QHBoxLayout()
        e_hbox.addWidget(self.com_combo)
        e_hbox.addWidget(self.open_button)
        # e_hbox.addWidget(self.bind_button)
        e_hbox.addWidget(self.test_button)
        e_hbox.addWidget(self.clear_button)

        self.ch_label=QLabel(u"设置信道：")
        self.ch_lineedit = QLineEdit(u'1')
        self.ch_lineedit.setFixedWidth(30)
        self.ch_button=QPushButton(u"修改信道")

        self.cmd_label=QLabel(u"DTQ回显:")
        self.cmd_lineedit = QLineEdit(u'很抱歉！答错了')
        self.change_button=QPushButton(u"发送数据")
        c_hbox = QHBoxLayout()

        c_hbox.addWidget(self.ch_label)
        c_hbox.addWidget(self.ch_lineedit)
        c_hbox.addWidget(self.ch_button)
        c_hbox.addWidget(self.bind_button)

        c_hbox.addWidget(self.cmd_label)
        c_hbox.addWidget(self.cmd_lineedit)
        c_hbox.addWidget(self.change_button)

        self.browser = QTextBrowser ()
        box = QVBoxLayout()
        box.addLayout(e_hbox)
        box.addLayout(c_hbox)
        box.addWidget(self.browser)
        self.setLayout(box)
        self.resize(600, 400 )
        self.open_button.clicked.connect(self.btn_event_callback)
        self.clear_button.clicked.connect(self.btn_event_callback)
        self.test_button.clicked.connect(self.btn_event_callback)
        self.change_button.clicked.connect(self.btn_event_callback)
        self.bind_button.clicked.connect(self.btn_event_callback)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)

    def update_time(self):
        self.send_cnt =self.send_cnt + 1
        self.send_msg = u"测试次数：%d" % self.send_cnt
        self.usb_hid_echo_data()

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

        if button_str == u"发送数据":
            '''
            改变发送数据的内容
            '''
            cur_msg   = unicode(self.cmd_lineedit.text())
            if cur_msg:
                self.send_msg = cur_msg
            self.usb_hid_echo_data()

        if button_str == u"开始绑定":
            '''
            发送开始绑定指令
            '''
            if self.alive:
                self.send_msg = u"绑定开始！请将需要测试的答题器刷卡绑定！"
                self.usb_hid_send_msg(self.xes_encode.bind_start_msg)
                self.bind_button.setText(u"停止绑定")
                self.browser.append(u"S :BIND_START: %s " % ( self.send_msg ))

        if button_str == u"停止绑定":
            '''
            发送开始绑定指令
            '''
            if self.alive:
                self.send_msg = u"绑定结束！此时刷卡无效"
                self.usb_hid_send_msg(self.xes_encode.bind_stop_msg)
                self.bind_button.setText(u"开始绑定")
                self.browser.append(u"S :BIND_STOP: %s " % ( self.send_msg ))

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
                self.usbhidmonitor = UsbHidMontior()
                self.connect(self.usbhidmonitor,SIGNAL('usb_r_msg(QString)'),self.usb_cmd_decode)
                # print self.dev_dict[usb_port]
                self.usbhidmonitor.start()
                self.browser.append(u"打开设备成功！")
                self.open_button.setText(u"关闭USB设备")
                self.usb_hid_send_msg(self.xes_encode.get_device_info_msg)

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

    def usb_hid_scan(self):
        self.usb_list  = hid.find_all_hid_devices()
        if self.usb_list  :
            for device in self.usb_list:
                device_name = unicode("{0.product_name}").format(device)
                self.com_combo.addItem(device_name)
                self.dev_dict[device_name] = device

    def usb_cmd_decode(self,data):
        if self.usbhidmonitor:
            if self.usbhidmonitor.cmd_decode.new_uid:
                self.usb_hid_send_msg(self.xes_encode.update_card_id_ack)
                if self.usbhidmonitor.cmd_decode.new_uid not in self.uid_list:
                    self.uid_list.append(self.usbhidmonitor.cmd_decode.new_uid)
                    print self.uid_list
                self.usbhidmonitor.cmd_decode.new_uid = None
        self.browser.append(u"R : {0}".format(data))
        logging.debug(u"接收数据：R : {0}".format(data))

    def usb_show_hook(self,data):
        self.usbhidmonitor.new_msg = data

    def usb_hid_echo_data(self):
        if self.uid_list:
            for item in self.uid_list:
                msg = self.xes_encode.get_echo_cmd_msg( item, self.send_msg )
                self.usb_hid_send_msg( msg )
                self.browser.append(u"S :ECHO: uID:[%08X] str:%s" % ( item, self.send_msg ))

    def usb_hid_send_msg(self,msg):
        print msg

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

        for item in tmp_msg:
            str_msg = str_msg + "%02X " % item

        print str_msg
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

