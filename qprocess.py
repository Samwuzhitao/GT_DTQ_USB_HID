# -*- coding: utf-8 -*-
"""
  * @file    :QProcessEntry.py
  * @author  : sam.wu
  * @version : v0.1.0
  * @date    : 2018.03.10
  * @brief   : ptqt 自由进程处理函数：
  *            此类在 QThread 类的基础上创建，直接处于GUI的指令协议解析函数
"""
from PySide.QtCore import *
from PySide.QtGui import *

class QProcessNoStop(QThread):
    def __init__(self, fun, parent=None):
        super(QProcessNoStop, self).__init__(parent)
        self.working = True
        self.fun = fun

    def __del__(self):
        self.working = False
        self.wait()

    def run(self):
        while self.working == True:
            self.fun()

class QProcessOneShort(QThread):
    def __init__(self, fun, parent=None):
        super(QProcessOneShort, self).__init__(parent)
        self.fun = fun

    def __del__(self):
        self.wait()

    def run(self):
        self.fun()