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
    def __init__(self, com, parent=None):
        super(ComMonitor,self).__init__(parent)
        self.working  = True
        self.com = com
        self.r_monitor_cmd = monitor_cmd_decode()
        self.r_dtq_cmd = dtq_cmd_decode()
        self.state = 0

    def __del__(self):
        self.working=False
        self.wait()

    def run(self):
        while self.working==True:
            if self.com.isOpen() == True:
                try:
                    r_char = self.com.read(1)
                    if self.state == 0:
                        r_cmd = self.r_monitor_cmd.r_machine(r_char)
                    else:
                        r_cmd = self.r_dtq_cmd.r_machine(r_char)

                except serial.SerialException:
                    self.working = False
                    pass
                if r_cmd:
                    r_cmd_str = "R: "
                    for item in r_cmd:
                        r_cmd_str += " %02X" % item
                    print r_cmd_str
                    # self.rcmd.clear()
                    # self.emit(SIGNAL('r_cmd_message(QString, QString)'),self.com.portstr,r_cmd)
