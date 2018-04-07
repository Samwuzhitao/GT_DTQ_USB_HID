# -*- coding: utf-8 -*-
"""
Created on Sat Apr 22 10:59:35 2017

@author: john
"""
import serial
import string
import time
import os
import sys
import logging
import json
from PyQt4.QtCore import *
from PyQt4.QtGui  import *
from led          import *
from dtq_monitor_dev import *
from dtq_ht46_dev  import *
from com_monitor  import *

class tag_ui(QFrame):
    def __init__(self, size, r_lcd, parent=None):
        self.port_name_dict = {}
        self.uart_dict = {}
        self.led_list  = []
        self.r_cmd_process_dict = {}
        self.s_cmd_timer_dict = {}
        self.s_cmd_pro_dict = {}
        self.led_combo_dict = {}
        self.uart_s_cmd_dict = {
            0: self.uart1_uart_s_cmd_fun,
            1: self.uart2_uart_s_cmd_fun,
            2: self.uart3_uart_s_cmd_fun,
            3: self.uart4_uart_s_cmd_fun
        }
        # 数据显示缓存
        self.r_lcd = r_lcd
        self.dev_pro = dtq_monitor_dev()

        super(tag_ui, self).__init__(parent)
        self.led1 = LED(size)
        self.led1_combo = QComboBox(self)
        self.led1_combo.addItems([ u"监测",u"压测"])
        self.led1_bt = QPushButton(u"[0]开始")
        self.led_list.append(self.led1)
        self.led2 = LED(size)
        self.led2_combo = QComboBox(self)
        self.led2_combo.addItems([ u"监测",u"压测"])
        self.led2_bt = QPushButton(u"[1]开始")
        self.led_list.append(self.led2)
        self.led3 = LED(size)
        self.led3_combo = QComboBox(self)
        self.led3_combo.addItems([ u"监测",u"压测"])
        self.led3_bt = QPushButton(u"[2]开始")
        self.led_list.append(self.led3)
        self.led4 = LED(size)
        self.led4_combo = QComboBox(self)
        self.led4_combo.addItems([ u"监测",u"压测"])
        self.led4_bt = QPushButton(u"[3]开始")
        self.led_list.append(self.led4)

        c_gbox = QHBoxLayout()
        c_gbox.addWidget(self.led1      )
        c_gbox.addWidget(self.led1_combo)
        c_gbox.addWidget(self.led1_bt   )
        c_gbox.addWidget(self.led2      )
        c_gbox.addWidget(self.led2_combo)
        c_gbox.addWidget(self.led2_bt   )
        c_gbox.addWidget(self.led3      )
        c_gbox.addWidget(self.led3_combo)
        c_gbox.addWidget(self.led3_bt   )
        c_gbox.addWidget(self.led4      )
        c_gbox.addWidget(self.led4_combo)
        c_gbox.addWidget(self.led4_bt   )

        self.led_combo_dict[0] = self.led1_combo
        self.led_combo_dict[1] = self.led2_combo
        self.led_combo_dict[2] = self.led3_combo
        self.led_combo_dict[3] = self.led4_combo

        self.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        self.setLayout(c_gbox)

        # 按键回调函数
        self.led1_bt.clicked.connect(self.btn_event_callback)
        self.led2_bt.clicked.connect(self.btn_event_callback)
        self.led3_bt.clicked.connect(self.btn_event_callback)
        self.led4_bt.clicked.connect(self.btn_event_callback)

    def uart1_uart_s_cmd_fun(self):
        print "PORT0"
        self.uart_s_cmd_fun(0)

    def uart2_uart_s_cmd_fun(self):
        self.uart_s_cmd_fun(1)

    def uart3_uart_s_cmd_fun(self):
        self.uart_s_cmd_fun(2)

    def uart4_uart_s_cmd_fun(self):
        self.uart_s_cmd_fun(3)

    def uart_s_cmd_fun(self, pos):
        # arr_msg = [0x61, 0x01, 0x07, 0x00, 0x46, 0x82, 0x20, 0xD2, 0x59, 0x5A, 0x00, 0x21]
        arr_msg =[]
        arr_msg = self.s_cmd_pro_dict[pos].get_check_dev_info_msg()
        s_cmd = self.dev_pro.send_data_cmd(arr_msg)
        # s_cmd = self.dev_pro.send_data_cmd(s_cmd)
        r_cmd_str = "S:"
        for item in s_cmd:
            r_cmd_str += " %02X" % ord(item)
        print r_cmd_str
        if self.uart_dict[pos].isOpen() == True:
            self.uart_dict[pos].write(s_cmd)

        # 串口解析数据进程
    def app_port_minitor_init(self, pos):
        self.s_cmd_pro_dict[pos] = dtq_xes_ht46()
        self.s_cmd_timer_dict[pos] = QTimer()
        self.s_cmd_timer_dict[pos].timeout.connect(self.uart_s_cmd_dict[pos])

    # 按键回调函数
    def btn_event_callback(self):
        button = self.sender()
        if button is None or not isinstance(button, QPushButton):
            return
        button_str = button.text()
        pos = int(button_str[1])
        cmd = unicode(button_str[3:])
        print pos,cmd
        if cmd == u"开始":
            if pos in self.port_name_dict:
                try:
                    ser = serial.Serial(self.port_name_dict[pos], 256000)
                    self.uart_dict[pos] = ser
                    button.setText(u"[%d]停止" % pos)
                    addr = [ 0x46, 0x82, 0x20, 0xD2 ]
                    rx_ch = 0x59
                    tx_ch = 0x5A
                    work_mode = unicode(self.led_combo_dict[pos].currentText())
                    if work_mode == u"监测":
                        self.r_cmd_process_dict[pos] = ComMonitor(ser)
                        self.r_cmd_process_dict[pos].start()
                        print " r_cmd_process_dict process start "
                        esb_mode = 1
                        s_cmd = self.dev_pro.get_rf_set_msg(addr, rx_ch, tx_ch, esb_mode)
                        if self.uart_dict[pos].isOpen() == True:
                            self.uart_dict[pos].write(s_cmd)
                    if work_mode == u"压测":
                        esb_mode = 0
                        s_cmd = self.dev_pro.get_rf_set_msg(addr, rx_ch, tx_ch, esb_mode)
                        if self.uart_dict[pos].isOpen() == True:
                            self.uart_dict[pos].write(s_cmd)
                        self.app_port_minitor_init(pos)
                        self.s_cmd_timer_dict[pos].start(200)
                        print " s_cmd_timer_dict process start "
                except serial.SerialException:
                    pass
                
        if cmd == u"停止":
            button.setText(u"[%d]开始" % pos)
            work_mode = unicode(self.led_combo_dict[pos].currentText())
            if work_mode == u"监测":
                self.r_cmd_process_dict[pos].quit()
            if work_mode == u"压测":
                self.s_cmd_timer_dict[pos].stop()
            if self.uart_dict[pos].isOpen() == True:
                self.uart_dict[pos].close()

    # 打开串口
    def uart_scan(self):
        s_cmd = self.dev_pro.get_dev_info_msg()
        ser = None
        port_pos = 0
        for i in range(100):
            try:
                ser = serial.Serial( "COM%d" % i, 256000, timeout = 0.5)
                if ser.isOpen() == True:
                    ser.write(s_cmd)
                    r_cmd = ser.read(12)
                    r_cmd_str = "" 
                    for item in r_cmd:
                        r_cmd_str += "%02X" % ord(item)
                    if r_cmd_str:
                        if r_cmd_str[0:8] == "61B00700": # 打开串口OK
                            self.led_list[port_pos].set_color("blue")
                            self.port_name_dict[port_pos] = "COM%d" % i
                            ser.close()
                            port_pos = port_pos + 1
            except serial.SerialException:
                pass

    # 关闭串口
    def uart_close(self):
        for item in self.port_name_dict:
            if item in self.uart_dict:
                if self.uart_dict[item].isOpen() == True:
                    self.uart_dict[item].close() 
            self.led_list[item].set_color("gray")




