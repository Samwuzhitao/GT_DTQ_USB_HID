# -*- coding: utf-8 -*-
"""
Created on Sat Apr 22 10:59:35 2017

@author: john
"""
import os
from PySide.QtCore import *
from PySide.QtGui  import *

class LED(QLabel):
    def __init__(self, x, parent=None):
        super(LED, self).__init__(parent)
        self.ico_path = os.path.abspath("./")
        self.led_b = QImage()
        self.led_b.load(self.ico_path + '\\image\\ledlightblue.ico')
        self.led_g = QImage()
        self.led_g.load(self.ico_path + '\\image\\ledgreen.ico')
        self.led_r = QImage()
        self.led_r.load(self.ico_path + '\\image\\ledred.ico')
        self.led_y = QImage()
        self.led_y.load(self.ico_path + '\\image\\ledgray.ico')
        self.color_dict = {'blue':self.led_b,'green':self.led_g,'red':self.led_r,'gray':self.led_y}
        self.resize(x,x)
        self.setAlignment(Qt.AlignCenter)
        self.setPixmap(QPixmap.fromImage(self.color_dict['gray']).scaled(self.size(),
            Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def set_color(self,color):
        self.setPixmap(QPixmap.fromImage(self.color_dict[color]).scaled(self.size(),
                Qt.KeepAspectRatio, Qt.SmoothTransformation))
