# -*- coding: utf-8 -*-
'''
* File Name   : main.py
* Description : HID 调试器主文件
* Input       : None
'''
from DEV_DTQ_HT46 import *
from QProcessEntry import *
import sys
import logging
import random
import pywinusb.hid as hid
from  serial.tools import list_ports

# 配置日志输出的方式及格式
LOG_TIME = time.strftime('%Y%m%d%H', time.localtime(time.time()))
logging.basicConfig (
    level = logging.DEBUG,
    filename = os.path.abspath("./") + "\\log\\log-%s.txt" % LOG_TIME,
    filemode = 'a',
    format = u'[%(asctime)s] %(message)s',
)

'''
* Class Name  : dtq_hid_debuger
* Description : HID 调试器主类
* Input       : None
'''
class dtq_hid_debuger(QWidget):
    def __init__(self, parent=None):
        super(dtq_hid_debuger, self).__init__(parent)
        # 设备协议
        self.dev_pro = None
        # 接收数据缓冲区
        self.rev_buf = []
        self.buf_cnt = 0
        # 表格UID名单
        self.qtree_dict = {}
        self.dtq_cnt_dict = {}

        self.test_rf_ch = 1
        self.dev_dict = {}
        self.uid_list = []
        self.report = None
        self.send_msg = u"恭喜你！答对了"
        self.send_cnt = {}
        
        self.card_cnt_dict = {}
        self.alive = False
        self.pp_test_flg = False
        self.xes_dev = None
        self.setWindowTitle(u"USB HID调试工具v2.0.0")
        self.com_combo = QComboBox(self)
        self.com_combo.setFixedSize(170, 20)
        self.usb_hid_scan()
        self.open_button = QPushButton(u"打开USB设备")
        self.clear_button = QPushButton(u"清空数据")
        self.test_button = QPushButton(u"开始回显压测")
        self.pp_test_button = QPushButton(u"开始单选乒乓")
        self.bind_button = QPushButton(u"开始绑定")
        self.check_conf_button = QPushButton(u"查看配置")
        self.clear_conf_button = QPushButton(u"清除配置")
        self.check_wl_button = QPushButton(u"查看白名单")

        e_hbox = QHBoxLayout()
        e_hbox.addWidget(self.com_combo)
        e_hbox.addWidget(self.open_button)
        e_hbox.addWidget(self.test_button)
        e_hbox.addWidget(self.pp_test_button)
        e_hbox.addWidget(self.clear_button)

        c_hbox = QHBoxLayout()
        self.ch_label = QLabel(u"设置信道：")
        self.ch_lineedit = QLineEdit(u'1')
        self.ch_button = QPushButton(u"修改信道")
        self.cmd_label = QLabel(u"回显功能：")
        self.cmd_lineedit = QLineEdit(u'恭喜你！答对了')
        self.change_button = QPushButton(u"发送数据")
        c_hbox.addWidget(self.ch_label)
        c_hbox.addWidget(self.ch_lineedit)
        c_hbox.addWidget(self.ch_button)
        c_hbox.addWidget(self.bind_button)
        c_hbox.addWidget(self.check_conf_button)
        c_hbox.addWidget(self.clear_conf_button)
        c_hbox.addWidget(self.check_wl_button)

        f_hbox = QHBoxLayout()
        self.fm_label=QLabel(u"固件路径：")
        self.fm_lineedit = QLineEdit()
        self.fm_add_button = QPushButton(u"添加固件")
        self.fm_update_button = QPushButton(u"升级程序")
        f_hbox.addWidget(self.fm_label)
        f_hbox.addWidget(self.fm_lineedit)
        f_hbox.addWidget(self.fm_add_button)
        f_hbox.addWidget(self.fm_update_button)

        k_hbox = QHBoxLayout()
        self.k_sum_label = QLabel(u"按键总和:")
        self.k_sum_label.setFont(QFont("Roman times", 15, QFont.Bold))
        self.k_sum_lineedit = QLineEdit(u'0')
        self.k_sum_lineedit.setFont(QFont("Roman times", 15, QFont.Bold))
        self.r_sum_label=QLabel(u"接收总和:")
        self.r_sum_label.setFont(QFont("Roman times", 15, QFont.Bold))
        self.r_sum_lineedit = QLineEdit(u'0')
        self.r_sum_lineedit.setFont(QFont("Roman times", 15, QFont.Bold))
        self.k_rate_label = QLabel(u"成功率:")
        self.k_rate_label.setFont(QFont("Roman times", 15, QFont.Bold))
        self.k_rate_lineedit = QLineEdit(u'0%')
        self.k_rate_lineedit.setFont(QFont("Roman times", 15, QFont.Bold))

        k_hbox.addWidget(self.k_sum_label)
        k_hbox.addWidget(self.k_sum_lineedit)
        k_hbox.addWidget(self.r_sum_label)
        k_hbox.addWidget(self.r_sum_lineedit)
        k_hbox.addWidget(self.k_rate_label)
        k_hbox.addWidget(self.k_rate_lineedit)

        t_hbox = QHBoxLayout()
        t_hbox.addWidget(self.cmd_label)
        t_hbox.addWidget(self.cmd_lineedit)
        t_hbox.addWidget(self.change_button)

        self.q_label = QLabel(u"答题功能：")
        self.q_combo = QComboBox(self)
        self.q_combo.setFixedSize(105, 20)
        self.q_combo.addItems([u"单题单选:0x01", u"是非判断:0x02",
            u"抢红包  :0x03", u"单题多选:0x04", u"多题单选:0x05",
            u"通用题型:0x06", u"6键单选 :0x07", u"语音作答:0x08",
            u"停止作答:0x80"])
        self.q_lineedit = QLineEdit(u'发送题目测试')
        self.q_button = QPushButton(u"发送题目")

        q_hbox = QHBoxLayout()
        q_hbox.addWidget(self.q_label)
        q_hbox.addWidget(self.q_combo)
        q_hbox.addWidget(self.q_lineedit)
        q_hbox.addWidget(self.q_button)

        self.browser = QTextBrowser ()
        self.browser.setFixedHeight(80)
        self.conf_browser = QTextBrowser ()
        self.conf_browser.setFixedHeight(40)

        self.tree_com = QTreeWidget()
        self.tree_com.setFont(QFont(u"答题器数据统计", 8, False))
        self.tree_com.setColumnCount(9)
        self.tree_com.setHeaderLabels([u'序号', u'uID', 
            u'按键次数', u'接收次数', u'回显次数', u'计数初值', 
            u'当前计数值', u'刷卡次数',u'重启次数',u'语音包接收'])
        self.tree_com.setColumnWidth(0, 50)
        for pos in range(1, 9):
            self.tree_com.setColumnWidth(pos, 75)

        box = QVBoxLayout()
        box.addLayout(e_hbox)
        box.addLayout(c_hbox)
        box.addLayout(q_hbox)
        box.addLayout(t_hbox)
        box.addLayout(f_hbox)
        box.addWidget(self.conf_browser)
        box.addWidget(self.browser)
        box.addWidget(self.tree_com)
        box.addLayout(k_hbox)

        self.setLayout(box)
        self.resize(800, 700 )
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
        self.pp_test_button.clicked.connect(self.btn_event_callback)
        self.fm_add_button.clicked.connect(self.btn_event_callback)
        self.fm_update_button.clicked.connect(self.btn_event_callback)
        self.q_combo.currentIndexChanged.connect(self.q_combo_changed_callback)
        # 创建回显压测定时器
        self.echo_timer = QTimer()
        self.echo_timer.timeout.connect(self.usb_hid_echo_data)
        # 下载数据处理进程
        self.image_timer = QTimer()
        self.image_timer.timeout.connect(self.usb_dfu_process)
        # 创建并启动 GUI 数据刷新进程
        self.gui_flash_timer = QTimer()
        self.gui_flash_timer.timeout.connect(self.qtree_dict_gui_flash)
        self.gui_flash_timer.start(200)
        # 创建并启动 USB 数据解析进程
        self.usb_rbuf_process = QProcessEntry(self.usb_cmd_decode)
        self.usb_rbuf_process.start()

    def q_combo_changed_callback(self):
        q_type = unicode(self.q_combo.currentText())
        q_type_str = q_type.split(":")[0]
        self.q_lineedit.setText(q_type_str)

    def usb_dfu_process(self):
        if self.alive:
            print "CHECK"
            # # 发送镜像信息
            # if self.usbhidmonitor.cmd_decode.usb_dfu_state == 0:
            #     self.browser.append(u"S : 开始连接设备...")
            #     if self.usbhidmonitor.cmd_decode.iamge_cmd_cnt == 0:
            #         image_info_pac = self.xes_encode.usb_dfu_soh_pac()
            #         if image_info_pac :
            #             self.usb_hid_send_msg( image_info_pac )
            # # # 发送镜像数据
            # if self.usbhidmonitor.cmd_decode.usb_dfu_state == 1:
            #     self.browser.append(u"S : 建立连接成功...")
            #     self.image_timer.stop()
        else:
            print "SCAN"
            self.usb_hid_scan()
            for item in self.dev_dict:
                base_name = item.split(".")[0]
                # print base_name[:-1],self.usbhidmonitor.cmd_decode.usb_dfu_state

                # if self.usbhidmonitor.cmd_decode.usb_dfu_state == 0:
                #     if base_name[:-1]== "JSQ_BOOT":
                #         self.dev_dict[item].open()
                #         self.dev_dict[item].set_raw_data_handler(self.usb_show_hook)
                #         self.report = self.dev_dict[item].find_output_reports()
                #         self.alive  = True
                #         self.usbhidmonitor = UsbHidMontior()
                #         self.connect(self.usbhidmonitor,SIGNAL('usb_r_msg()'),self.usb_cmd_decode)
                #         self.usbhidmonitor.start()
                #         self.browser.append(u"打开设备:[ %s ] 成功！" % item )
                #         self.open_button.setText(u"关闭USB设备")

                # if self.usbhidmonitor.cmd_decode.usb_dfu_state == 2:
                #     if base_name[:-1]== "DTQ_JSQ_":
                #         self.dev_dict[item].open()
                #         self.dev_dict[item].set_raw_data_handler(self.usb_show_hook)
                #         self.report = self.dev_dict[item].find_output_reports()
                #         self.alive  = True
                #         self.usbhidmonitor = UsbHidMontior()
                #         self.connect(self.usbhidmonitor,SIGNAL('usb_r_msg()'),self.usb_cmd_decode)
                #         self.usbhidmonitor.start()
                #         self.browser.append(u"打开设备:[ %s ] 成功！" % item )
                #         self.open_button.setText(u"关闭USB设备")
                #         self.usbhidmonitor.cmd_decode.usb_dfu_state = 0
                #         self.image_timer.stop()

    '''
    * Fun Name    : usb_hid_send_msg
    * Description : HID 底层发送数据函数
    * Input       : msg
    '''
    def usb_hid_send_msg(self, msg):
        # 复制指令码到发送数组
        tmp_msg = [0x00]
        for item in msg:
            tmp_msg.append(item)
        # 没有满的数据自动补0
        for item_pos in range(len(tmp_msg), self.dev_pro.PAC_LEN):
            tmp_msg.append(0x00)
        # 发送数据
        if self.report:
            self.report[0].set_raw_data(tmp_msg)
            try:
                self.report[0].send()
            except hid.HIDError:
                self.open_button.setText(u"打开USB设备")
                self.dev_dict = {}
                self.alive = False
            tmp_msg = u"发送数据：S : {0}".format(tmp_msg)
            logging.debug(tmp_msg)

    '''
    * Fun Name    : usb_hid_send_msg
    * Description : HID USB 接收数据钩子函数
    * Input       : data
    '''
    def usb_show_hook(self, data):
        self.rev_buf.append(data)

    '''
    * Fun Name    : qtree_dict_gui_flash
    * Description : GUI 界面更新
    * Input       : None
    '''
    def qtree_dict_gui_flash(self):
        if self.qtree_dict:
            for item in self.qtree_dict:
                if item in self.dtq_cnt_dict:
                    self.qtree_dict[item].setText(9, str(self.dtq_cnt_dict[item]["VOICE_CNT"]))

    '''
    * Fun Name    : usb_cmd_decode
    * Description : 数据解析函数
    * Input       : None
    ''' 
    def usb_cmd_decode(self):
        if len(self.rev_buf) > 0:
            tmp_msg = self.rev_buf.pop()
            res_dict = self.dev_pro.answer_cmd_decode(tmp_msg)
            logging.debug(u"接收数据：R : {0}".format(res_dict))
            dev_id = res_dict[u"UID"]
            # 答题器数据统计
            if dev_id > 0:
                # 统计数据更新
                if res_dict["CMD"] == "DTQ_VOICE":
                    if dev_id in self.dtq_cnt_dict:
                        self.dtq_cnt_dict[dev_id]["VOICE_CNT"] = self.dtq_cnt_dict[dev_id]["VOICE_CNT"] + 1
                    else:
                        self.dtq_cnt_dict[dev_id] = {}
                        self.dtq_cnt_dict[dev_id]["VOICE_CNT"] = 1
                # GUI 界面初始化
                if dev_id not in self.qtree_dict:
                    self.qtree_dict[dev_id] = QTreeWidgetItem(self.tree_com)
                    self.qtree_dict[dev_id].setText(0, str(len(self.qtree_dict)))
                    self.qtree_dict[dev_id].setText(1, str(dev_id))
                    self.qtree_dict[dev_id].setText(9, str(self.dtq_cnt_dict[dev_id]["VOICE_CNT"]))

    '''
    * Fun Name    : btn_event_callback
    * Description : 按键处理回调函数
    * Input       : None
    ''' 
    def btn_event_callback(self):
        button = self.sender()
        if button is None or not isinstance(button, QPushButton):
            return

        button_str = button.text()
        if button_str == u"清空数据":
            self.browser.clear()

        if button_str == u"打开USB设备":
            usb_port = str(self.com_combo.currentText())
            if usb_port:
                self.dev_dict[usb_port].open()
                self.dev_dict[usb_port].set_raw_data_handler(self.usb_show_hook)
                self.report = self.dev_dict[usb_port].find_output_reports()
                self.alive = True
                self.dev_pro = XesHT46Pro()
                self.browser.append(u"打开设备:[ %s ] 成功！" % usb_port )
                self.open_button.setText(u"关闭USB设备")

        if button_str == u"关闭USB设备":
            usb_port = str(self.com_combo.currentText())
            self.alive = False
            if self.dev_dict[usb_port]:
                self.dev_dict[usb_port].close()
                self.report = None
                self.browser.append(u"关闭设备成功！")
            self.open_button.setText(u"打开USB设备")

        if button_str == u"发送题目":
            q_type =  unicode(self.q_combo.currentText())
            if self.alive:
                que_t = int(q_type.split(":")[1][2:])
                self.browser.clear()
                cur_msg   = unicode(self.q_lineedit.text())
                msg = self.dev_pro.get_question_cmd_msg( que_t, cur_msg )
                self.usb_hid_send_msg( msg )
                self.browser.append(u"S : 发送题目 : %s : %s " % ( q_type, cur_msg ))
                
        # if button_str == u"开始回显压测":
        #     if self.alive:
        #         self.test_button.setText(u"停止回显压测")
        #         self.echo_timer.start(300)

        # if button_str == u"停止回显压测":
        #     if self.alive:
        #         self.test_button.setText(u"开始回显压测")
        #         self.echo_timer.stop()

        # if button_str == u"发送数据":
        #     if self.uid_list:
        #         for item in self.uid_list:
        #             if self.send_cnt.has_key(item):
        #                 self.send_cnt[item] =self.send_cnt[item] + 1
        #             else:
        #                 self.send_cnt[item] = 1
        #             cur_msg   = unicode(self.cmd_lineedit.text())
        #             if cur_msg:
        #                 self.send_msg = cur_msg
        #             else:
        #                 self.send_msg = u"uID:%010d  S_CNT：%d" % (self.xes_encode.uid_negative(item),self.send_cnt[item])
        #             msg = self.xes_encode.get_echo_cmd_msg( item, self.send_msg )
        #             self.usb_hid_send_msg( msg )

        # if button_str == u"开始绑定":
        #     if self.alive:
        #         self.send_msg = u"绑定开始！请将需要测试的答题器刷卡绑定！"
        #         self.usb_hid_send_msg(self.xes_encode.bind_start_msg)
        #         self.bind_button.setText(u"停止绑定")
        #         self.browser.append(u"S : BIND_START: %s " % ( self.send_msg ))

        # if button_str == u"停止绑定":
        #     if self.alive:
        #         self.send_msg = u"绑定结束！此时刷卡无效"
        #         self.usb_hid_send_msg(self.xes_encode.bind_stop_msg)
        #         self.bind_button.setText(u"开始绑定")
        #         self.browser.append(u"S : BIND_STOP: %s " % ( self.send_msg ))

        # if button_str == u"修改信道":
        #     if self.alive:
        #         ch = int(str(self.ch_lineedit.text()))
        #         self.send_msg = u"修改信道"
        #         self.usb_hid_send_msg(self.xes_encode.get_ch_cmd_msg(ch))
        #         self.bind_button.setText(u"开始绑定")
        #         self.browser.append(u"S : SET_CH: %d %s " % (ch,self.send_msg ))

        # if button_str == u"查看配置":
        #     if self.alive:
        #         self.send_msg = u"查看设备信息"
        #         self.usb_hid_send_msg(self.xes_encode.get_device_info_msg)
        #         self.browser.append(u"S : GET_DEVICE_INFO: %s " % ( self.send_msg ))

        # if button_str == u"清除配置":
        #     if self.alive:
        #         self.send_msg = u"清除配置信息"
        #         self.usb_hid_send_msg(self.xes_encode.clear_dev_info_msg)
        #         self.browser.append(u"S : CLEAR_DEV_INFO: %s " % ( self.send_msg ))
        #         self.usbhidmonitor.cmd_decode.wl_list = []

        # if button_str == u"查看白名单":
        #     if self.alive:
        #         self.send_msg = u"查看白名单"
        #         self.usb_hid_send_msg(self.xes_encode.check_wl)
        #         self.browser.append(u"S : CHECK_WL: %s " % ( self.send_msg ))

        # if button_str == u"开始单选乒乓":
        #     if self.alive:
        #         self.pp_test_flg = True
        #         msg = self.xes_encode.get_question_cmd_msg( 0x01, "" )
        #         self.usb_hid_send_msg( msg )
        #         self.pp_test_button.setText(u"停止单选乒乓")

        # if button_str == u"停止单选乒乓":
        #     if self.alive:
        #         self.pp_test_flg = False
        #         self.pp_test_button.setText(u"开始单选乒乓")

        # if button_str == u"添加固件":
        #     temp_image_path = unicode(QFileDialog.getOpenFileName(self, 'Open file', './', "bin files(*.bin)"))
        #     if len(temp_image_path) > 0:
        #         self.fm_lineedit.setText(temp_image_path)

        # if button_str == u"生成头文件":
        #     image_path = unicode(self.fm_lineedit.text())
        #     if len(image_path) > 0:
        #         file_name = os.path.basename(image_path)
        #         file_size = int(os.path.getsize(image_path))
        #         file_offset = 0
        #         print "File Name: %s " % file_name
        #         print "File Size: %d " % file_size
        #         new_file_name = file_name.split('_')[1]+'.h'
        #         print new_file_name
        #         dst_f = open(new_file_name, "w")

        #         dst_f.write('/*******************************************************************************\n')
        #         dst_f.write('* File Name          : %s\n' % (file_name.split('.')[0]+'.h'))
        #         dst_f.write('* Author             : Sam.wu\n')
        #         dst_f.write('* Version            : V1.0.0\n')
        #         dst_f.write('* Date               : %s\n' % time.strftime( LOGTIMEFORMAT,time.localtime(time.time())))
        #         dst_f.write('********************************************************************************/\n\r\n')
        #         dst_f.write('#ifndef __%s_IMAGE__\n' % file_name.split('_')[1])
        #         dst_f.write('#define __%s_IMAGE__\n' % file_name.split('_')[1])
        #         dst_f.write('#include "stm32f10x.h"\n\r\n')
        #         dst_f.write('const uint8_t %s_image[] =\n' % file_name.split('_')[1])
        #         dst_f.write('{\n')
        #         while file_offset < file_size:
        #             src_f = open(image_path, "rb")
        #             src_f.seek(file_offset,0)
        #             if (file_offset + 16) < file_size:
        #                 r_len = 16
        #             else:
        #                 r_len = file_size-file_offset
        #             image_data = src_f.read( r_len )
        #             image_data_arry = ""
        #             for item in image_data:
        #                 image_data_arry = image_data_arry + " 0x%02X," % (ord(item))
        #             image_data_arry = image_data_arry + '\n'
        #             print image_data_arry
        #             dst_f.write(image_data_arry)
        #             file_offset = file_offset + r_len
        #             src_f.close()
        #         dst_f.write('}\n\r\n')
        #         dst_f.write('#endif\r\n')
        #         dst_f.close()

        # if button_str == u"转化HEX文件":
        #     image_path = unicode(self.fm_lineedit.text())
        #     if len(image_path) > 0 :
        #         f = open(image_path)
        #         li = f.readlines()
        #         f.close()

        #         time_data = time.strftime( '%Y%m%d',time.localtime(time.time()))
        #         uid_str   = "%08X" % (string.atoi(str(self.dtq_id_lineedit.text()),10))
        #         insert_data = "08FC0000" + time_data + uid_str
        #         insert_data_hex = insert_data.decode("hex")

        #         check_sum = 0
        #         for i in insert_data_hex:
        #             check_sum = (ord(i) + check_sum) % 0x100

        #         insert_data = ':' + insert_data + "%02X\n" % (0x100-check_sum)
        #         li.insert(1, insert_data)
        #         #print li
        #         file_path = self.dtq_image_path[0:len(self.dtq_image_path)-4]
        #         self.new_image_path = file_path + "_NEW.hex"

        #         new_file = open(self.new_image_path ,'w')
        #         for i in li:
        #             new_file.write(i)
        #         new_file.close()

        #         self.browser.append(u"<font color=black>DTQ@UID:[%s] HEX文件转换成功</font>" %
        #             str(self.dtq_id_lineedit.text()) )
        #     else:
        #         self.browser.append(u"<font color=black>DTQ@错误:</font><font color=red>无烧写固件</font>")

        # if button_str == u"升级程序":
        #     image_path = unicode(self.fm_lineedit.text())
        #     if len(image_path) > 0:
        #         print image_path
        #         self.xes_encode.usb_dfu_init( image_path )
        #         self.usbhidmonitor.cmd_decode.iamge_cmd_cnt = 0
        #         self.image_timer.start(300)
        #         self.progressDialog=QProgressDialog(self)
        #         self.progressDialog.setWindowModality(Qt.WindowModal)
        #         self.progressDialog.setMinimumDuration(5)
        #         self.progressDialog.setWindowTitle(u"请等待")
        #         self.progressDialog.setLabelText(u"下载中...")
        #         self.progressDialog.setCancelButtonText(u"取消")
        #         self.progressDialog.setRange(0,100)

    def usb_hid_scan(self):
        usb_list = hid.find_all_hid_devices()
        if usb_list  :
            for device in usb_list:
                device_name = unicode("{0.product_name}").format(device)
                print device_name
                if device_name[0:3] == "DTQ" or device_name[0:3] == "JSQ":
                    serial_number = unicode("{0.serial_number}").format(device)
                    cur_usb_name = device_name+"_"+serial_number
                    if self.dev_dict.has_key(cur_usb_name):
                        print "SAME"
                    else:
                        self.com_combo.addItem(device_name+"_"+serial_number)
                        self.dev_dict[device_name+"_"+serial_number] = device

    def get_rand_gp2312(self):
        head = random.randint(0xb0, 0xf7)
        # 在head区号为55的那一块最后5个汉字是乱码,为了方便缩减下范围
        body = random.randint(0xa1, 0xf9)
        val = (head<<8)|body
        str = "%x" % val
        str_gb2312 = str.decode('hex').decode('gb2312')
        return str_gb2312

    def usb_hid_echo_data(self):
        if self.uid_list:
            for item in self.uid_list:
                if self.send_cnt.has_key(item):
                    self.send_cnt[item] =self.send_cnt[item] + 1
                else:
                    self.send_cnt[item] = 1
                self.send_msg = u"uID:%010d  S_CNT：%-8d" % (self.xes_encode.uid_negative(item),self.send_cnt[item])
                rand_str = ""
                for i in range(8):
                    rand_str = rand_str + "%s" % self.get_rand_gp2312()
                self.send_msg = self.send_msg + rand_str
                msg = self.xes_encode.get_echo_cmd_msg( item, self.send_msg )
                self.usb_hid_send_msg( msg )
                # self.browser.append(u"S : ECHO: CARD_ID:[%010d] str:%s" % ( self.xes_encode.uid_negative(item), self.send_msg ))

    def usb_hid_echo_test(self):
        if self.uid_list:
            for item in self.uid_list:
                msg = self.xes_encode.get_echo_cmd_msg( item, self.send_msg )
                self.usb_hid_send_msg( msg )
                self.browser.append(u"S : ECHO: CARD_ID:[%010d] str:%s" % ( self.xes_encode.uid_negative(item), self.send_msg ))


if __name__=='__main__':
    app = QApplication(sys.argv)
    datburner = dtq_hid_debuger()
    datburner.show()
    app.exec_()
