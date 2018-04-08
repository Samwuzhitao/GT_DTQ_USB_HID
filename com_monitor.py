# -*- coding: utf-8 -*-
"""
Created on Sat Apr 22 10:59:35 2017

@author: Samwu
"""
import serial
import string
from PyQt4.QtCore import *
from PyQt4.QtGui  import *
from dtq_monitor_dev import *

class ComMonitor(QThread):
    def __init__(self, port, com, r_buf, parent=None):
        super(ComMonitor,self).__init__(parent)
        self.working  = True
        self.port = port
        self.com = com
        self.r_dtq_cmd = dtq_cmd_decode()
        self.r_cmd_decode = dtq_monitor_dev()
        self.state = 0
        self.r_buf = r_buf

    def __del__(self):
        self.working=False
        self.wait()

    def run(self):
        while self.working==True:
            if self.com.isOpen() == True:
                try:
                    r_char = self.com.read(1)
                    r_cmd = self.r_dtq_cmd.r_machine(r_char)
                except serial.SerialException:
                    self.working = False
                    pass
                if r_cmd:
                    self.r_cmd_decode.cmd_decode(self.r_buf, r_cmd)
                    # r_cmd_str = "[ PORT%d ] R:" % self.port
                    # for item in r_cmd:
                    #     r_cmd_str += " %02X" % item
                    # self.r_buf.put(r_cmd_str)
                