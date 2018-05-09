#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
* File Name   : main.py
* Description : HID 调试器主文件
* Input       : None
# '''
import sys
from PySide.QtCore import *
from PySide.QtGui import *
import pywinusb.hid as hid
import ctypes
import random
import Queue
import UserString
import serial
from qprocess import *
from file_transfer import *
import logging
from dtq_ht46_dev import *
from port_frame import *
import cProfile

JSQ_VID = 0x0483
JSQ_PID = 0x5A4C

# 配置日志输出的方式及格式
LOG_TIME = time.strftime('%Y%m%d%H', time.localtime(time.time()))
logging.basicConfig (
    level = logging.DEBUG,
    filename = os.path.abspath("./") + "\\log\\log-%s.txt" % LOG_TIME,
    filemode = 'a',
    format = u'[%(asctime)s] %(message)s',
)

class hid_pnp_event(hid.HidPnPWindowMixin):
    hidConnected = Signal(hid.HidDevice, str)
    def __init__(self):
        getAsPtr = ctypes.pythonapi.PyCObject_AsVoidPtr
        getAsPtr.restype = ctypes.c_void_p
        getAsPtr.argtypes = [ctypes.py_object]
        window_hnd = getAsPtr(self.winId())

        hid.HidPnPWindowMixin.__init__(self, window_hnd)
        self.hid_device = None
        self._hid_target = None
        self.on_hid_pnp()

    def on_hid_pnp(self, hid_pnp_event = None):
        old_device = self.hid_device
        if hid_pnp_event == "connected":
            if self.hid_device:
                pass
            else:
                self.test_for_connection()
        elif hid_pnp_event == "disconnected":
            if self.hid_device and not self.hid_device.is_plugged():
                self.hid_device = None
        else:
            self.test_for_connection()
        if old_device != self.hid_device:
            if hid_pnp_event == "disconnected":
                self.hidConnected.emit(old_device, hid_pnp_event)
            else:
                self.hidConnected.emit(self.hid_device, hid_pnp_event)

    def test_for_connection(self):
        if not self._hid_target:
            return
        all_items =  self._hid_target.get_devices()
        if all_items:
            if len(all_items) == 1:
                self.hid_device = all_items[0]
            else:
                grouped_items = self._hid_target.get_devices_by_parent()
                if len(grouped_items) > 1:
                    pass
                else:
                    pass
                self.hid_device = all_items[0]
        if self.hid_device:
            self.hid_device.open()

    def set_target(self, hid_filter):
        self._hid_target = hid_filter
        self.test_for_connection()
        if self.hid_device:
            self.hidConnected.emit(self.hid_device, "connected")

'''
* Class Name  : dtq_hid_debuger
* Description : HID 调试器主类
* Input       : None
'''
class dtq_hid_debuger(QWidget, hid_pnp_event):
    def __init__(self, parent=None):
        super(dtq_hid_debuger, self).__init__(parent)
        hid_pnp_event.__init__(self)
        # 数据缓冲区
        self.rcmd_buf = Queue.Queue()
        self.scmd_buf = Queue.Queue()
        self.r_lcd_buf = Queue.Queue()
        self.s_lcd_buf = Queue.Queue()
        # 表格 UID名单
        self.qtree_dict = {}
        self.dtq_cnt_dict = {}
        self.mp3_player_dict = {}
        self.jsq_tcb = {}
        # USB 设备管理
        self.alive = False
        # 答题协议
        self.dev_pro = None
        # 升级协议
        self.dfu_pro = None

        self.setWindowTitle(u"USB HID调试工具v2.0.15")
        self.connect_label = QLabel(u"连接状态:")
        self.connect_label.setFixedWidth(60)
        self.led = LED(30)
        self.led.setFixedWidth(30)
        self.usb_bt = QPushButton(u"搜索USB设备")
        self.ser_bt = QPushButton(u"搜索DTQ监测设备")
        self.clr_bt = QPushButton(u"清空数据")
        self.pp_test_button = QPushButton(u"开始单选乒乓")
        e_hbox = QHBoxLayout()
        e_hbox.addWidget(self.connect_label)
        e_hbox.addWidget(self.led)
        e_hbox.addWidget(self.usb_bt)
        e_hbox.addWidget(self.ser_bt)
        e_hbox.addWidget(self.pp_test_button)
        e_hbox.addWidget(self.clr_bt)

        self.ch_label = QLabel(u"设置信道：")
        self.ch_lineedit = QLineEdit(u'1')
        self.ch_button = QPushButton(u"修改信道")
        self.bind_button = QPushButton(u"开始绑定")
        self.check_conf_button = QPushButton(u"查看配置")
        self.clear_conf_button = QPushButton(u"清除配置")
        self.check_wl_button = QPushButton(u"查看白名单")
        self.port_combo = QComboBox(self)
        self.port_combo.addItems([u"PORT:0", u"PORT:1",
            u"PORT:2", u"PORT:3", u"PORT:4"])
        self.port_button = QPushButton(u"复位端口")
        c_hbox = QHBoxLayout()
        c_hbox.addWidget(self.ch_label)
        c_hbox.addWidget(self.ch_lineedit)
        c_hbox.addWidget(self.ch_button)
        c_hbox.addWidget(self.bind_button)
        c_hbox.addWidget(self.check_conf_button)
        c_hbox.addWidget(self.clear_conf_button)
        c_hbox.addWidget(self.check_wl_button)
        c_hbox.addWidget(self.port_combo)
        c_hbox.addWidget(self.port_button)

        s_hbox = QHBoxLayout()
        self.ctl_label = QLabel(u"状态控制：")
        self.devid_label = QLabel(u"uID：")
        self.devid_lineedit = QLineEdit()
        self.devid_lineedit.setFixedWidth(135)
        self.led_label = QLabel(u"指示灯：")
        self.led_color_combo = QComboBox(self)
        self.led_color_combo.addItems([u"红:0x01", u"绿:0x02", u"蓝:0x03", u"黄:0x04",u"紫:0x05",u"青:0x06",u"白:0x07"])
        self.led_combo = QComboBox(self)
        self.led_combo.addItems([u"闪:0x01", u"闪:0x02",u"闪:0x03",u"闪:0x04",u"闪:0x05",u"NOP:0x00"])
        self.beep_label = QLabel(u"蜂鸣器：")
        self.beep_combo = QComboBox(self)
        self.beep_combo.addItems([u"叫:0x01", u"叫:0x02",u"叫:0x03",u"叫:0x04",u"叫:0x05",u"NOP:0x00"])
        self.motor_label = QLabel(u"电机：")
        self.motor_combo = QComboBox(self)
        self.motor_combo.addItems([u"震:0x01", u"震:0x02",u"震:0x03",u"震:0x04",u"震:0x05",u"NOP:0x00"])
        self.ctl_button = QPushButton(u"同步状态")
        s_hbox.addWidget(self.ctl_label)
        s_hbox.addWidget(self.devid_label)
        s_hbox.addWidget(self.devid_lineedit)
        s_hbox.addWidget(self.led_label)
        s_hbox.addWidget(self.led_color_combo)
        s_hbox.addWidget(self.led_combo)
        s_hbox.addWidget(self.beep_label)
        s_hbox.addWidget(self.beep_combo)
        s_hbox.addWidget(self.motor_label)
        s_hbox.addWidget(self.motor_combo)
        s_hbox.addWidget(self.ctl_button)

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
        self.sum_sedit = QLineEdit(u'0')
        self.sum_sedit.setFont(QFont("Roman times", 15, QFont.Bold))
        self.r_sum_label=QLabel(u"接收总和:")
        self.r_sum_label.setFont(QFont("Roman times", 15, QFont.Bold))
        self.sum_redit = QLineEdit(u'0')
        self.sum_redit.setFont(QFont("Roman times", 15, QFont.Bold))
        self.sum_rate_label = QLabel(u"按键成功率:")
        self.sum_rate_label.setFont(QFont("Roman times", 15, QFont.Bold))
        self.sum_rate_edit = QLineEdit(u'0')
        self.sum_rate_edit.setFont(QFont("Roman times", 15, QFont.Bold))

        k_hbox.addWidget(self.k_sum_label)
        k_hbox.addWidget(self.sum_sedit)
        k_hbox.addWidget(self.r_sum_label)
        k_hbox.addWidget(self.sum_redit)
        k_hbox.addWidget(self.sum_rate_label)
        k_hbox.addWidget(self.sum_rate_edit)

        debug_hbox = QHBoxLayout()
        self.debug_label = QLabel(u"性能监测：")
        self.usb_r_sum_label = QLabel(u"USBR：")
        self.usb_r_sum_sedit = QLineEdit(u'0')
        self.usb_s_sum_label=QLabel(u"USBS：")
        self.usb_s_sum_redit = QLineEdit(u'0')
        self.lcd_r_label = QLabel(u"LCD：")
        self.lcd_r_edit = QLineEdit(u'0')
        self.connect_label = QLabel(u"CONNECT：")
        self.connect_edit = QLineEdit(u'0')
 
        debug_hbox.addWidget(self.debug_label)
        debug_hbox.addWidget(self.usb_r_sum_label)
        debug_hbox.addWidget(self.usb_r_sum_sedit)
        debug_hbox.addWidget(self.usb_s_sum_label)
        debug_hbox.addWidget(self.usb_s_sum_redit)
        debug_hbox.addWidget(self.lcd_r_label)
        debug_hbox.addWidget(self.lcd_r_edit)
        debug_hbox.addWidget(self.connect_label)
        debug_hbox.addWidget(self.connect_edit)

        self.cmd_label = QLabel(u"回显功能：")
        self.echo_uid_label = QLabel(u"uID：")
        self.echo_uid_lineedit = QLineEdit()
        self.echo_uid_lineedit.setFixedWidth(135)
        self.cmd_lineedit = QLineEdit(u'恭喜你！答对了')
        self.change_button = QPushButton(u"发送数据")
        t_hbox = QHBoxLayout()
        t_hbox.addWidget(self.cmd_label)
        t_hbox.addWidget(self.echo_uid_label)
        t_hbox.addWidget(self.echo_uid_lineedit)
        t_hbox.addWidget(self.cmd_lineedit)
        t_hbox.addWidget(self.change_button)

        self.q_label = QLabel(u"答题功能：")
        self.an_devid_label = QLabel(u"uID：")
        self.an_devid_lineedit = QLineEdit()
        self.an_devid_lineedit.setFixedWidth(135)
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
        q_hbox.addWidget(self.an_devid_label)
        q_hbox.addWidget(self.an_devid_lineedit)
        q_hbox.addWidget(self.q_combo)
        q_hbox.addWidget(self.q_lineedit)
        q_hbox.addWidget(self.q_button)

        self.r_browser = QTextBrowser ()
        self.r_browser.setFixedHeight(160)
        self.r_browser.document().setMaximumBlockCount(100)
        self.s_browser = QTextBrowser ()
        self.s_browser.setFixedHeight(80)
        self.s_browser.document().setMaximumBlockCount(100)

        self.tree_com = QTreeWidget()
        self.tree_com.setFont(QFont(u"答题器数据统计", 8, False))
        self.tree_com.setColumnCount(14)
        self.tree_com.setHeaderLabels([u'序号', u'uID', u'RSSI', u'电量', 
            u'按压次数', u'按键次数', u'发送次数', u'回显次数',u'答案',
            u'AN_S0', u'AN_CNT', u'CA_CNT',u'PO_CNT',u'VO_CNT'])
        self.tree_com.setColumnWidth(0, 40)
        self.tree_com.setColumnWidth(1, 70)
        self.tree_com.setColumnWidth(2, 35)
        self.tree_com.setColumnWidth(3, 30)
        for pos in range(4, 8):
            self.tree_com.setColumnWidth(pos, 55)
        self.tree_com.setColumnWidth(8, 110)
        for pos in range(9, 14):
            self.tree_com.setColumnWidth(pos, 55)

        self.port_frame = port_frame(30, self.jsq_tcb, self.s_lcd_buf, self.r_lcd_buf)

        box = QVBoxLayout()
        box.addLayout(e_hbox)
        box.addWidget(self.port_frame)
        box.addLayout(c_hbox)
        box.addLayout(t_hbox)
        box.addLayout(q_hbox)
        box.addLayout(s_hbox)
        box.addLayout(f_hbox)
        box.addLayout(debug_hbox)
        box.addWidget(self.s_browser)
        box.addWidget(self.r_browser)
        box.addWidget(self.tree_com)
        box.addLayout(k_hbox)

        self.setLayout(box)
        self.resize(805, 900 )
        self.port_button.clicked.connect(self.btn_event_callback)
        self.usb_bt.clicked.connect(self.btn_event_callback)
        self.clr_bt.clicked.connect(self.btn_event_callback)
        self.ser_bt.clicked.connect(self.btn_event_callback)
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
        self.ctl_button.clicked.connect(self.btn_event_callback)
        self.q_combo.currentIndexChanged.connect(self.q_combo_changed_callback)
        # 按键双击操作的实现
        self.connect(self.tree_com, SIGNAL("itemDoubleClicked (QTreeWidgetItem *, int)"), self.tree_2_clicked)
        self.connect(self.tree_com, SIGNAL("itemClicked (QTreeWidgetItem *, int)"), self.tree_1_clicked)

        # 下载数据处理进程
        self.usb_dfu_timer = QTimer()
        self.usb_dfu_timer.timeout.connect(self.usb_dfu_process)
        # GUI 数据处理进程
        self.r_lcd_timer = QTimer()
        self.r_lcd_timer.timeout.connect(self.r_lcd_process)
        self.r_lcd_timer.start(1)
        self.s_lcd_timer = QTimer()
        self.s_lcd_timer.timeout.connect(self.s_lcd_process)
        self.s_lcd_timer.start(10)
        self.r_tree_timer = QTimer()
        self.r_tree_timer.timeout.connect(self.update_tree_process)
        self.r_tree_timer.start(300)
        # 创建 USB 数据解析进程，USB 发送数据进程
        self.usb_rbuf_process = QProcessNoStop(self.usb_rcmd_process)
        self.usb_sbuf_process = QProcessNoStop(self.usb_scmd_process)
        self.usb_rbuf_process.start()
        self.usb_sbuf_process.start()
        self.hidConnected.connect( self.on_connected )

    def on_connected(self, my_hid, event_str):
        self.r_lcd_buf.put(u"设备 vId={0:04x}, pId={1:04x}: {2} ！".format(
            my_hid.vendor_id, my_hid.product_id, event_str ))
        if my_hid.vendor_id == JSQ_VID and my_hid.product_id == JSQ_PID:
            if event_str == "connected":
                if "connected" not in self.jsq_tcb:
                    self.jsq_tcb["connected"] = 1
                else:
                    self.jsq_tcb["connected"] = self.jsq_tcb["connected"] + 1

                self.hid_device.set_raw_data_handler(self.usb_rev_hook)
                self.report = self.hid_device.find_output_reports()
                self.alive = True
                self.dev_pro = dtq_xes_ht46(self.r_lcd_hook, self.usb_snd_hook)
                self.led.set_color("blue")
                msg = self.dev_pro.get_check_wl_msg()
                self.usb_snd_hook(msg)
            else:
                self.alive = False
                self.led.set_color("gray")

    def update_tree_process(self):
        if self.alive and self.dev_pro.dtqdict:
            for uid in self.dev_pro.dtqdict:
                if uid:
                    if uid not in self.qtree_dict:
                        self.qtree_dict[uid] = QTreeWidgetItem(self.tree_com)
                        self.qtree_dict[uid].setText(0, str(len(self.qtree_dict)))
                        self.qtree_dict[uid].setText(1, "%010u" % uid)
                    tmp_uid = self.dev_pro.dtqdict[uid]
                    self.qtree_dict[uid].setText(2, tmp_uid.rssi_str)
                    self.qtree_dict[uid].setText(3, str(tmp_uid.power))
                    self.qtree_dict[uid].setText(4, str(tmp_uid.press_cnt))
                    self.qtree_dict[uid].setText(5, str(tmp_uid.key_cnt))
                    self.qtree_dict[uid].setText(6, str(tmp_uid.send_cnt))
                    self.qtree_dict[uid].setText(7, str(tmp_uid.echo_cnt))
                    self.qtree_dict[uid].setText(8, str(tmp_uid.ans_str))
                    self.qtree_dict[uid].setText(9, str(tmp_uid.answer_cnt_s0))
                    self.qtree_dict[uid].setText(10, str(tmp_uid.answer_cnt))
                    self.qtree_dict[uid].setText(11, str(tmp_uid.card_cnt))
                    self.qtree_dict[uid].setText(12, str(tmp_uid.power_cnt))
                    self.qtree_dict[uid].setText(13, str(tmp_uid.pac_cnt))
            # 刷新统计信息
            self.sum_sedit.setText(str(self.dev_pro.sum_scnt))
            self.sum_redit.setText(str(self.dev_pro.sum_rcnt))
            self.sum_rate_edit.setText("%f" % self.dev_pro.lost_rate)

    # 数据显示进程
    def r_lcd_process(self):
        if not self.r_lcd_buf.empty():
            self.r_lcd_timer.stop()
            r_msg = self.r_lcd_buf.get()
            self.r_browser.append(r_msg)
            logging.debug(u"接收数据：%s" % r_msg)
            self.r_lcd_timer.start()
        else:
            self.r_lcd_timer.stop()
            self.r_lcd_timer.start(10)

    def r_lcd_hook(self, msg):
        self.r_lcd_buf.put(msg)

    # 数据显示进程
    def s_lcd_process(self):
        if not self.s_lcd_buf.empty():
            s_msg = self.s_lcd_buf.get()
            self.s_browser.append(s_msg )
        else:
            if self.alive:
                self.usb_r_sum_sedit.setText(str(self.rcmd_buf.qsize()))
                self.usb_s_sum_redit.setText(str(self.scmd_buf.qsize()))
                self.lcd_r_edit.setText(str(self.r_lcd_buf.qsize()))
                self.connect_edit.setText(str(self.jsq_tcb["connected"]))

    # 单击获取设备ID
    def tree_1_clicked(self, item, column):
        self.devid_lineedit.setText(unicode(item.text(1)))
        self.an_devid_lineedit.setText(unicode(item.text(1)))
        self.echo_uid_lineedit.setText(unicode(item.text(1)))

    # 双击获取设备ID
    def tree_2_clicked(self, item, column):
        uid = int(unicode(item.text(1)))
        self.devid_lineedit.setText(unicode(item.text(1)))
        if uid in self.dev_pro.dtqdict:
            if uid in self.mp3_player_dict:
                self.mp3_player_dict[uid].start()
            else:
                self.mp3_player_dict[uid] = QProcessOneShort(self.dev_pro.dtqdict[uid].play)
                self.mp3_player_dict[uid].start()
            msg_str = u"[ %010u ]:播放测试 :%s！" % (self.dev_pro.dtqdict[uid].devid, self.dev_pro.dtqdict[uid].f_name)
            self.s_lcd_buf.put(msg_str)

    def q_combo_changed_callback(self):
        q_type = unicode(self.q_combo.currentText())
        q_type_str = q_type.split(":")[0]
        self.q_lineedit.setText(q_type_str)

    def usb_dfu_process(self):
        if self.alive:
            # 发送镜像信息
            if self.dev_pro.dfu_s == 0:
                self.s_lcd_buf.put(u"S: 开始连接设备...")
                if self.dfu_pro.f_offset == 0:
                    image_info = self.dfu_pro.usb_dfu_soh_pac()
                    if image_info:
                        msg = self.dev_pro.get_dfu_msg(0x30, image_info)
                        self.usb_snd_hook(msg)
                        return
                else:
                    self.r_browser.clear()
                    self.s_browser.clear()
                    self.usb_dfu_timer.stop()

            # 切换定时器
            if self.dev_pro.dfu_s == 1:
                self.usb_dfu_timer.stop()
                self.usb_dfu_timer.start(10)
                self.dev_pro.dfu_s = 2

            # 发送镜像数据
            if self.dev_pro.dfu_s == 2:
                image_data = self.dfu_pro.usb_dfu_stx_pac()
                if image_data:
                    msg = self.dev_pro.get_dfu_msg(0x31, image_data)
                    if msg != None:
                        self.usb_snd_hook(msg)
                        self.progressDialog_value = (self.dfu_pro.f_offset * 100) / self.dfu_pro.f_size
                        self.progressDialog.setValue(self.progressDialog_value)
                else:
                    self.dev_pro.dfu_s = 0
                    self.s_lcd_buf.put(u"S: 数据传输完成...")
                    self.usb_dfu_timer.stop()
                return

    '''
    * Fun Name    : usb_snd_hook
    * Description : HID 底层发送数据函数
    * Input       : msg
    '''
    def usb_snd_hook(self, smsg):
        # 复制指令码到发送数组
        self.scmd_buf.put(smsg)
        # debug_str = "S: "
        # for item in smsg:
        #    debug_str += " %02X" % (item)
        # print debug_str

    '''
    * Fun Name    : usb_scmd_process
    * Description : HID 底层发送数据进程
    * Input       : msg
    '''
    def usb_scmd_process(self):
        if self.alive:
            if not self.scmd_buf.empty():
                msg = self.scmd_buf.get()
                r_cmd = [0x00]
                for item in msg:
                    r_cmd.append(item)
                # 没有满的数据自动补0
                for item_pos in range(len(r_cmd), self.dev_pro.PAC_LEN):
                    r_cmd.append(0x00)
                # 发送数据
                if self.report:
                    self.report[0].set_raw_data(r_cmd)
                    try:
                        self.report[0].send()
                    except hid.HIDError:
                        pass
                        self.s_lcd_buf.put(u"发送数据失败！")
                    r_cmd = u"发送数据：S : {0}".format(r_cmd)
                    logging.debug(r_cmd)

    '''
    * Fun Name    : usb_rev_hook
    * Description : HID USB 接收数据钩子函数
    * Input       : data
    '''
    def usb_rev_hook(self, rcmd):
        self.rcmd_buf.put(rcmd)
        # debug_str = "R: "
        # for item in rcmd:
        #    debug_str += " %02X" % (item)
        # print debug_str

    '''
    * Fun Name    : usb_rcmd_process
    * Description : 数据解析函数
    * Input       : None
    ''' 
    def usb_rcmd_process(self):
        if not self.rcmd_buf.empty():
            r_cmd = self.rcmd_buf.get()
            # 此处指令解析放在协议文件的内部实现,方便实现硬件的兼容
            self.dev_pro.answer_cmd_decode(self.jsq_tcb, r_cmd)
       
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

        if self.alive:
            if button_str == u"开始单选乒乓":
                s_msg = self.dev_pro.get_echo_cmd_msg(0x11223344, "cur_msg")
                self.usb_snd_hook(s_msg)
                return

            if button_str == u"清空数据":
                self.r_browser.clear()
                self.s_browser.clear()
                return

            if button_str == u"发送题目":
                devid_str = str(self.an_devid_lineedit.text())
                if devid_str:
                    devid = int(str(self.an_devid_lineedit.text()))
                else:
                    devid = 0
                q_type =  unicode(self.q_combo.currentText())
                que_t = int(q_type.split(":")[1][2:])
                que_t = (que_t / 10)*16 +  que_t % 10
                # print que_t
                cur_msg   = unicode(self.q_lineedit.text())
                msg = self.dev_pro.get_question_cmd_msg( devid, que_t, cur_msg )
                self.usb_snd_hook( msg )
                self.s_lcd_buf.put(u"S: 发送题目 : %s : %s " % ( q_type, cur_msg ))
                return

            if button_str == u"发送数据":
                i = 0
                uid_str = str(self.echo_uid_lineedit.text())
                msg = unicode(self.cmd_lineedit.text())
                msg_str = u"S: 发送回显 : %s, UID：" % msg
                if uid_str:
                    uid = int(uid_str)
                    if uid in self.dev_pro.dtqdict:
                        cur_msg = u"uID: %10u %s" % (uid, msg)
                        msg_str = msg_str + " [ %10u ]" % uid
                        s_msg = self.dev_pro.get_echo_cmd_msg(uid, cur_msg)
                        self.usb_snd_hook(s_msg)
                else:
                    for item in self.dev_pro.dtqdict:
                        if item:
                            cur_msg = u"uID: %10u %s" % (item, msg)
                            i = i + 1
                            s_msg = self.dev_pro.get_echo_cmd_msg(item, cur_msg)
                            self.usb_snd_hook(s_msg)
                            msg_str = msg_str + " [ %10u ]" % item
                self.s_lcd_buf.put(msg_str)
                return

            if button_str == u"查看配置":
                msg = self.dev_pro.get_check_dev_info_msg()
                self.usb_snd_hook(msg)
                self.s_lcd_buf.put(u"S: 查看设备信息 ")
                return

            if button_str == u"复位端口":
                port_type =  unicode(self.port_combo.currentText())
                port = int(port_type.split(":")[1]) 
                msg = self.dev_pro.get_reset_port_msg(port)
                self.usb_snd_hook(msg)
                self.s_lcd_buf.put(u"S: 复位端口 ")
                return

            if button_str == u"修改信道":
                ch = int(str(self.ch_lineedit.text()))
                msg = self.dev_pro.get_set_rf_ch_msg(ch)
                self.usb_snd_hook(msg)
                self.s_lcd_buf.put(u"S: 修改信道 ")
                return

            if button_str == u"停止绑定":
                msg = self.dev_pro.get_bind_stop_msg()
                self.usb_snd_hook(msg)
                self.bind_button.setText(u"开始绑定")
                self.s_lcd_buf.put(u"S: 停止绑定: 绑定结束！此时刷卡无效")
                return

            if button_str == u"开始绑定":
                msg = self.dev_pro.get_bind_start_msg()
                self.usb_snd_hook(msg)
                self.bind_button.setText(u"停止绑定")
                self.s_lcd_buf.put(u"S: 开始绑定: 绑定开始！请将需要测试的答题器刷卡绑定！")
                return

            if button_str == u"清除配置":
                msg = self.dev_pro.get_clear_dev_info_msg()
                self.usb_snd_hook(msg)
                self.s_lcd_buf.put(u"S: 清除配置: ")
                return

            if button_str == u"同步状态":
                devid_str = str(self.devid_lineedit.text())
                if devid_str:
                    devid = int(devid_str)
                else:
                    devid = 0
                uid_str = ""
                led_cn_str = unicode(self.led_combo.currentText())
                led_cn = int(led_cn_str.split(":")[1][2:]) 
                led_col_str = unicode(self.led_color_combo.currentText())
                led_c = int(led_col_str.split(":")[1][2:]) 
                beep_cn_str = unicode(self.beep_combo.currentText())
                beep_cn = int(beep_cn_str.split(":")[1][2:])
                motor_cn_str = unicode(self.motor_combo.currentText())
                motor_cn = int(motor_cn_str.split(":")[1][2:])
                # print led_cn,led_c,beep_cn,motor_cn
                if devid:
                    msg = self.dev_pro.get_dtq_ctl_msg(devid, led_cn, led_c, beep_cn, motor_cn)
                    uid_str = "[ %10u ]" % devid
                    self.usb_snd_hook(msg)
                else:
                    for item in self.dev_pro.dtqdict:
                        if item:
                            msg = self.dev_pro.get_dtq_ctl_msg(item, led_cn, led_c, beep_cn, motor_cn)
                            uid_str += "[ %10u ]" % item
                            self.usb_snd_hook(msg)
                self.s_lcd_buf.put(u"S: 同步状态: UID：%s" % uid_str)
                return

            if button_str == u"查看白名单":
                msg = self.dev_pro.get_check_wl_msg()
                self.usb_snd_hook(msg)
                self.s_lcd_buf.put(u"S: 查看白名单:")
                return

            if button_str == u"添加固件":
                image_path = unicode(QFileDialog.getOpenFileName(self, u'添加固件', './', u"bin 文件(*.bin)"))
                file_path = unicode(image_path.split("'")[1])
                if len(file_path) > 0:
                    self.fm_lineedit.setText(file_path)
                return

            if button_str == u"升级程序":
                image_path = unicode(self.fm_lineedit.text())
                if len(image_path) > 0:
                    self.dev_pro.dfu_s = 0
                    self.dfu_pro = file_transfer(image_path, self.dev_pro.PAC_LEN - 21)
                    self.progressDialog = QProgressDialog(self)
                    self.progressDialog.setWindowModality(Qt.WindowModal)
                    self.progressDialog.setMinimumDuration(5)
                    self.progressDialog.setWindowTitle(u"请等待")
                    self.progressDialog.setLabelText(u"下载中...")
                    self.progressDialog.setCancelButtonText(u"取消")
                    self.progressDialog.setRange(0,100)
                    self.usb_dfu_timer.start(300)
                return

            if button_str == u"搜索DTQ监测设备":
                self.s_lcd_buf.put(u"S: 搜索DTQ监测设备 ")
                self.port_frame.port_name_dict = {}
                self.port_frame.uart_scan()
                r_cmd_str = u"R: 搜索监测端口:"
                for item in self.port_frame.port_name_dict:
                    r_cmd_str += "[ %s ]" % self.port_frame.port_name_dict[item]
                self.r_lcd_buf.put(r_cmd_str)
                return
        else:
            if button_str == u"搜索USB设备":
                self.s_lcd_buf.put( u"开始查找设备！" )
                self.set_target(hid.HidDeviceFilter(vendor_id = JSQ_VID, product_id = JSQ_PID))

    def get_rand_gp2312(self):
        head = random.randint(0xb0, 0xf7)
        # 在head区号为55的那一块最后5个汉字是乱码,为了方便缩减下范围
        body = random.randint(0xa1, 0xf9)
        val = (head<<8)|body
        str = "%x" % val
        str_gb2312 = str.decode('hex').decode('gb2312')
        return str_gb2312

if __name__=='__main__':
    app = 0
    app = QApplication(sys.argv)
    datburner = dtq_hid_debuger()
    datburner.show()
    sys.exit(app.exec_())
    if datburner.alive:
        msg = datburner.dev_pro.get_question_cmd_msg( 0x80, u"关闭软件" )
        datburner.usb_snd_hook( msg )
        while not datburner.scmd_buf.empty():
            time.sleep(10)
        datburner.usb_rbuf_process.quit()
        datburner.usb_sbuf_process.quit()
        

