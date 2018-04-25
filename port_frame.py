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

class port_frame(QFrame):
    def __init__(self, size, sys_info, s_lcd, r_lcd, parent=None):
        self.sys_info = sys_info
        self.port_name_dict = {}
        self.uart_dict = {}
        self.led_list  = []
        self.r_cmd_process_dict = {}
        self.s_cmd_pro_dict = {}
        self.led_combo_dict = {}
        self.r_lcd = r_lcd
        self.s_lcd = s_lcd
        self.dev_pro = dtq_monitor_dev()

        super(port_frame, self).__init__(parent)
        self.led1 = LED(size)
        self.led1_combo = QComboBox(self)
        self.led1_combo.addItems([ u"压测",u"监测"])
        self.led1_bt = QPushButton(u"[0]开始")
        self.led_list.append(self.led1)
        self.led2 = LED(size)
        self.led2_combo = QComboBox(self)
        self.led2_combo.addItems([ u"压测",u"监测"])
        self.led2_bt = QPushButton(u"[1]开始")
        self.led_list.append(self.led2)
        self.led3 = LED(size)
        self.led3_combo = QComboBox(self)
        self.led3_combo.addItems([ u"压测",u"监测"])
        self.led3_bt = QPushButton(u"[2]开始")
        self.led_list.append(self.led3)
        self.led4 = LED(size)
        self.led4_combo = QComboBox(self)
        self.led4_combo.addItems([ u"压测",u"监测"])
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

    # 按键回调函数
    def btn_event_callback(self):
        button = self.sender()
        if button is None or not isinstance(button, QPushButton):
            return
        button_str = button.text()
        pos = int(button_str[1])
        cmd = unicode(button_str[3:])
        # print pos,cmd
        port_item  = "PORT%d" % pos 
        if port_item in self.sys_info:
            addr = self.sys_info[port_item]["addr"]
            rx_ch = self.sys_info[port_item]["rf_rx"]
            tx_ch = self.sys_info[port_item]["rf_tx"]
        else:
            self.r_lcd.put(u"请先打开接收器设备")
            return
        
        if cmd == u"开始":
            esb_mode = 0
            if pos in self.port_name_dict:
                try:
                    ser = serial.Serial(self.port_name_dict[pos], 256000)
                    self.uart_dict[pos] = ser
                    button.setText(u"[%d]停止" % pos)
                    work_mode = unicode(self.led_combo_dict[pos].currentText())
                    if work_mode == u"监测":
                        self.r_cmd_process_dict[pos] = ComMonitor(pos, ser, self.r_lcd)
                        self.r_cmd_process_dict[pos].start()
                        esb_mode = 1
                    s_cmd = self.dev_pro.get_start_esb_msg(pos, addr, rx_ch, tx_ch, esb_mode)
                    if self.uart_dict[pos].isOpen() == True:
                        self.uart_dict[pos].write(s_cmd)
                        r_cmd = ser.read(11)
                        r_cmd_str = "" 
                        for item in r_cmd:
                            r_cmd_str += "%02X" % ord(item)
                        if r_cmd_str:
                            # print r_cmd_str
                            if r_cmd_str[0:16] == "6105811122334401": # 打开串口OK
                                self.led_list[pos].set_color("green")
                except serial.SerialException:
                    pass

        if cmd == u"停止":
            button.setText(u"[%d]开始" % pos)
            work_mode = unicode(self.led_combo_dict[pos].currentText())
            if work_mode == u"监测":
                self.r_cmd_process_dict[pos].quit()
            s_cmd = self.dev_pro.get_stop_esb_msg()
            if self.uart_dict[pos].isOpen() == True:
                self.uart_dict[pos].write(s_cmd)
                r_cmd = self.uart_dict[pos].read(18)
                r_cmd_str = "" 
                for item in r_cmd:
                    r_cmd_str += "%02X" % ord(item)
                if r_cmd_str:
                    # print r_cmd_str
                    if r_cmd_str[0:16] == "6105821122334408": # 打开串口OK
                        self.led_list[pos].set_color("blue")
                self.uart_dict[pos].close()

    # 打开串口
    def uart_scan(self):
        tmp_port_dict = {}
        s_cmd = self.dev_pro.get_stop_esb_msg()
        ser = None
        port_pos = 0

        for i in range(100):
            try:
                port_name = "COM%d" % i
                s = serial.Serial(port_name)
                tmp_port_dict[port_name] = port_name
                s.close()
            except serial.SerialException:
                pass

        for port in tmp_port_dict:
            try:
                ser = serial.Serial( port, 256000, timeout = 0.1)
                if ser.isOpen() == True:
                    ser.write(s_cmd)
                    r_cmd = ser.read(18)
                    r_cmd_str = "" 
                    for item in r_cmd:
                        r_cmd_str += "%02X" % ord(item)
                    if r_cmd_str:
                        # print r_cmd_str
                        if r_cmd_str[0:16] == "6105821122334408": # 打开串口OK
                            self.led_list[port_pos].set_color("blue")
                            self.port_name_dict[port_pos] = port
                            ser.close()
                            port_pos = port_pos + 1
            except serial.SerialException:
                pass

    # 关闭串口
    def uart_close(self):
        for item in self.port_name_dict:
            if item in self.uart_dict:
                s_cmd = self.dev_pro.get_stop_esb_msg()
                if self.uart_dict[item].isOpen() == True:
                    self.uart_dict[item].write(s_cmd)
                    self.uart_dict[item].close()
            self.led_list[item].set_color("gray")
        self.led1_bt.setText(u"[0]开始")
        self.led2_bt.setText(u"[1]开始")
        self.led3_bt.setText(u"[2]开始")
        self.led4_bt.setText(u"[3]开始")




