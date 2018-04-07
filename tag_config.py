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

class tag_ui(QFrame):
    def __init__(self, size, parent=None):
        self.port_list = {}
        self.led_list  = []

        super(tag_ui, self).__init__(parent)
        self.led1 = LED(size)
        self.led1_combo = QComboBox(self)
        self.led1_combo.addItems([ u"监测",u"压测"])
        self.led1_button = QPushButton(u"开始")
        self.led_list.append(self.led1)
        self.led2 = LED(size)
        self.led2_combo = QComboBox(self)
        self.led2_combo.addItems([ u"监测",u"压测"])
        self.led2_button = QPushButton(u"开始")
        self.led_list.append(self.led2)
        self.led3 = LED(size)
        self.led3_combo = QComboBox(self)
        self.led3_combo.addItems([ u"监测",u"压测"])
        self.led3_button = QPushButton(u"开始")
        self.led_list.append(self.led3)
        self.led4 = LED(size)
        self.led4_combo = QComboBox(self)
        self.led4_combo.addItems([ u"监测",u"压测"])
        self.led4_button = QPushButton(u"开始")
        self.led_list.append(self.led4)

        c_gbox = QHBoxLayout()
        c_gbox.addWidget(self.led1       )
        c_gbox.addWidget(self.led1_combo )
        c_gbox.addWidget(self.led1_button)
        c_gbox.addWidget(self.led2       )
        c_gbox.addWidget(self.led2_combo )
        c_gbox.addWidget(self.led2_button)
        c_gbox.addWidget(self.led3       )
        c_gbox.addWidget(self.led3_combo )
        c_gbox.addWidget(self.led3_button)
        c_gbox.addWidget(self.led4       )
        c_gbox.addWidget(self.led4_combo )
        c_gbox.addWidget(self.led4_button)

        self.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        self.setLayout(c_gbox)

    def uart_scan(self):
        connect_cmd = "61 30 00 00 21"
        connect_cmd = str(connect_cmd.replace(' ',''))
        connect_cmd = connect_cmd.decode("hex")
        ser         = None
        # 扫描串口
        port_pos = 0
        for i in range(100):
            try:
                ser = serial.Serial( "COM%d" % i, 256000, timeout = 0.5)
                if ser.isOpen() == True:
                    ser.write(connect_cmd)
                    r_cmd = ser.read(12)
                    r_cmd_str = "" 
                    for item in r_cmd:
                        r_cmd_str += "%02X" % ord(item)
                    # print r_cmd_str
                    if r_cmd_str:
                        if r_cmd_str[0:8] == "61B00700": # 打开串口OK
                            self.led_list[port_pos].set_color("blue")
                            self.port_list[port_pos] = ser
                            self.port_list[port_pos].close()
                            port_pos = port_pos + 1
            except serial.SerialException:
                pass

    def uart_close(self):
        for item in self.port_list:
            if self.port_list[item].isOpen() == True:
                self.port_list[item].close()
            self.led_list[item].set_color("gray")

if __name__=='__main__':
    app = QApplication(sys.argv)
    datburner = tag_ui(30)
    datburner.show()
    app.exec_()




