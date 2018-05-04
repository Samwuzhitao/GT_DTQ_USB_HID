# -*- coding: utf-8 -*-
"""
  * @file    : file_transfer.py
  * @author  : sam.wu
  * @version : v0.1.0
  * @date    : 2018.03.28
  * @brief   : 此类是构建的自己的文件传输协议
"""
import string
import os

class file_transfer():
    def __init__(self, file_path, pac_len):
		# 其他管理变量
        self.file_path = None
        self.file_name = None
        self.f_size    = 0
        self.f_offset  = 0
        self.pac_size  = pac_len
        if file_path :
            self.file_path = file_path
            self.file_name = os.path.basename(file_path)
            self.f_size = int(os.path.getsize(file_path))
            # print "File Name: %s " % self.file_name
            # print "File Size: %d " % self.f_size
            # print "pack Size: %d " % self.pac_size

    def usb_dfu_soh_pac(self):
        NOP = 0
        self.f_offset = 0
        if self.file_path :
            image_info = []
            for item in self.file_name:
                image_info.append(ord(item))
            image_info.append(NOP)
            image_info.append( self.f_size & 0xFF )
            image_info.append((self.f_size >> 8) & 0xFF)
            image_info.append((self.f_size >> 16) & 0xFF)
            image_info.append((self.f_size >> 24) & 0xFF)
            return image_info

    def usb_dfu_stx_pac(self):
        # 封装帧内容
        NOP = 0
        r_data = None
        pac_len = 0
        if self.file_path :
            # 读取数据
            if self.f_size > self.f_offset :
                f = open(self.file_path, "rb")
                f.seek(self.f_offset,0)
                if (self.f_offset + self.pac_size) < self.f_size:
                    pac_len = self.pac_size
                else:
                    pac_len = self.f_size-self.f_offset
                r_data = f.read( pac_len )
                f.close()
                # print " f_offset = %5d , sum = %5d, len = %d " % (self.f_offset, self.f_size, pac_len)
            # 封装数据
            if r_data:
                image_data = []
                # 填充偏移
                image_data.append( self.f_offset & 0xFF )
                image_data.append((self.f_offset >> 8) & 0xFF)
                image_data.append((self.f_offset >> 16) & 0xFF)
                image_data.append((self.f_offset >> 24) & 0xFF)
                image_data.append( pac_len )
                # 填充数据内容
                # image_data_arry = "RD:"
                for item in r_data:
                    # image_data_arry = image_data_arry + " %02x" % (ord(item))
                    image_data.append(ord(item))
                # image_data_arry = image_data_arry + '\n'
                # print image_data_arry
                self.f_offset = self.f_offset + pac_len
                return image_data
            else:
                return None
