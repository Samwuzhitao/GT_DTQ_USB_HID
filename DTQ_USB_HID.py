# -*- coding: utf-8 -*-
'''
* File Name   : main.py
* Description : HID 调试器主文件
* Input       : None
# '''
import sys
import random
import Queue
import pywinusb.hid as hid
from  serial.tools import list_ports
from dtq_ht46_dev  import *
from qprocess      import *
from file_transfer import *
from tag_config    import *
import logging

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
        # 数据缓冲区
        self.rev_buf = Queue.Queue()
        self.snd_buf = Queue.Queue()
        self.r_lcd_buf = Queue.Queue(maxsize=100)
        self.r_tree_buf = Queue.Queue(maxsize=40)
        self.s_lcd_buf = Queue.Queue()
        # 表格 UID名单
        self.qtree_dict = {}
        self.dtq_cnt_dict = {}
        self.mp3_player_dict = {}
        self.uid_list = {}
        # USB 设备管理
        self.dev_dict = {}
        self.alive = False
        # 答题协议
        self.dev_pro = None
        # 升级协议
        self.dfu_pro = None

        self.setWindowTitle(u"USB HID调试工具v2.0.10")
        self.com_combo = QComboBox(self)
        self.com_combo.setFixedSize(170, 20)
        self.usb_hid_scan()
        self.usb_bt = QPushButton(u"打开USB设备")
        self.ser_bt = QPushButton(u"搜索DTQ监测设备")
        self.clr_bt = QPushButton(u"清空数据")
        self.pp_test_button = QPushButton(u"开始单选乒乓")
        self.bind_button = QPushButton(u"开始绑定")
        self.check_conf_button = QPushButton(u"查看配置")
        self.clear_conf_button = QPushButton(u"清除配置")
        self.check_wl_button = QPushButton(u"查看白名单")
        self.port_combo = QComboBox(self)
        self.port_combo.addItems([u"PORT0:0x00", u"PORT1:0x01",
            u"PORT2:0x02", u"PORT3:0x03", u"PORT4:0x04"])
        self.port_button = QPushButton(u"复位端口")

        e_hbox = QHBoxLayout()
        e_hbox.addWidget(self.com_combo)
        e_hbox.addWidget(self.usb_bt)
        e_hbox.addWidget(self.ser_bt)
        e_hbox.addWidget(self.pp_test_button)
        e_hbox.addWidget(self.clr_bt)

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
        c_hbox.addWidget(self.port_combo)
        c_hbox.addWidget(self.port_button)

        s_hbox = QHBoxLayout()
        self.ctl_label = QLabel(u"状态控制：")
        self.devid_label = QLabel(u"uID：")
        self.devid_lineedit = QLineEdit()
        self.led_label = QLabel(u"指示灯：")
        self.led_combo = QComboBox(self)
        self.led_combo.addItems([u"NOP:0x00", u"闪一下:0x01"])
        self.beep_label = QLabel(u"蜂鸣器：")
        self.beep_combo = QComboBox(self)
        self.beep_combo.addItems([u"NOP:0x00", u"叫一下:0x01"])
        self.motor_label = QLabel(u"电机：")
        self.motor_combo = QComboBox(self)
        self.motor_combo.addItems([u"NOP:0x00", u"震一下:0x01"])
        self.ctl_button = QPushButton(u"同步状态")
        s_hbox.addWidget(self.ctl_label)
        s_hbox.addWidget(self.devid_label)
        s_hbox.addWidget(self.devid_lineedit)
        s_hbox.addWidget(self.led_label)
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

        self.r_browser = QTextBrowser ()
        self.r_browser.setFixedHeight(160)
        self.r_browser.document().setMaximumBlockCount(100)
        self.s_browser = QTextBrowser ()
        self.s_browser.setFixedHeight(80)
        self.s_browser.document().setMaximumBlockCount(100)

        self.tree_com = QTreeWidget()
        self.tree_com.setFont(QFont(u"答题器数据统计", 8, False))
        self.tree_com.setColumnCount(9)
        self.tree_com.setHeaderLabels([u'序号', u'uID', 
            u'按键次数', u'接收次数', u'回显次数', u'计数初值', 
            u'当前计数值', u'刷卡次数',u'重启次数',u'语音包计数'])
        self.tree_name_pos = {"ANSWER": 3, u'CARD_ID': 7, "VOICE": 9, "VOICE_FLG": 10}
        self.tree_com.setColumnWidth(0, 50)
        for pos in range(1, 9):
            self.tree_com.setColumnWidth(pos, 70)

        self.port_frame = tag_ui(30, self.uid_list, self.s_lcd_buf, self.r_lcd_buf)

        box = QVBoxLayout()
        box.addLayout(e_hbox)
        box.addWidget(self.port_frame)
        box.addLayout(c_hbox)
        box.addLayout(q_hbox)
        box.addLayout(t_hbox)
        box.addLayout(s_hbox)
        box.addLayout(f_hbox)
        box.addWidget(self.s_browser)
        box.addWidget(self.r_browser)
        box.addWidget(self.tree_com)
        box.addLayout(k_hbox)

        self.setLayout(box)
        self.resize(740, 900 )
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
        self.connect(self.tree_com, SIGNAL("itemDoubleClicked (QTreeWidgetItem *, int)"), self.tree_com_itemDoubleClicked)
        self.connect(self.tree_com, SIGNAL("itemClicked (QTreeWidgetItem *, int)"), self.tree_com_itemClicked)

        # 下载数据处理进程
        self.usb_dfu_timer = QTimer()
        self.usb_dfu_timer.timeout.connect(self.usb_dfu_process)
        # GUI 数据处理进程
        self.r_lcd_timer = QTimer()
        self.r_lcd_timer.timeout.connect(self.r_lcd_process)
        self.r_lcd_timer.start(10)
        self.s_lcd_timer = QTimer()
        self.s_lcd_timer.timeout.connect(self.s_lcd_process)
        self.s_lcd_timer.start(10)
        self.r_tree_timer = QTimer()
        self.r_tree_timer.timeout.connect(self.r_tree_process)
        self.r_tree_timer.start(10)
        # 创建 USB 数据解析进程
        self.usb_rbuf_process = QProcessNoStop(self.usb_cmd_rev_process)
        # 创建 USB 发送数据进程
        self.usb_sbuf_process = QProcessNoStop(self.usb_cmd_snd_process)

    def r_tree_process(self):
        if not self.r_tree_buf.empty():
            tree_msg = self.r_tree_buf.get()
            pos = int(tree_msg.split(":")[0])
            uid = str(tree_msg.split(":")[1])
            msg = str(tree_msg.split(":")[2])
            self.qtree_dict[uid].setText(pos, msg)

    # 数据显示进程
    def r_lcd_process(self):
        if not self.r_lcd_buf.empty():
            r_msg = self.r_lcd_buf.get()
            self.r_browser.append(r_msg )

    def r_lcd_hook(self, msg):
        self.r_lcd_buf.put(msg)

    # 数据显示进程
    def s_lcd_process(self):
        if not self.s_lcd_buf.empty():
            s_msg = self.s_lcd_buf.get()
            self.s_browser.append(s_msg )

    # 单击获取设备ID
    def tree_com_itemClicked(self, item, column):
        self.devid_lineedit.setText(unicode(item.text(1)))

    # 双击获取设备ID
    def tree_com_itemDoubleClicked(self, item, column):
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
            # print "CHECK"
            # 发送镜像信息
            if self.dev_pro.dfu_s == 0:
                self.s_lcd_buf.put(u"S: 开始连接设备...")
                if self.dfu_pro.f_offset == 0:
                    image_info = self.dfu_pro.usb_dfu_soh_pac()
                    if image_info:
                        msg = self.dev_pro.get_dfu_msg(0x30, image_info)
                        self.usb_snd_store(msg)
                        return
            # 切换定时器
            if self.dev_pro.dfu_s == 1:
                self.usb_dfu_timer.stop()
                self.usb_dfu_timer.start(10)
                self.dev_pro.dfu_s = 2

            # 切换定时器
            if self.dev_pro.dfu_s == 2:
                image_data = self.dfu_pro.usb_dfu_stx_pac()
                if image_data:
                    msg = self.dev_pro.get_dfu_msg(0x31, image_data)
                    if msg != None:
                        self.usb_snd_store(msg)
                        self.progressDialog_value = (self.dfu_pro.f_offset * 100) / self.dfu_pro.f_size
                        self.progressDialog.setValue(self.progressDialog_value)
                else:
                    self.dev_pro.dfu_s = 3
                return
            # 发送镜像数据
            if self.dev_pro.dfu_s == 3:
                self.s_lcd_buf.put(u"S: 数据传输完成...")
                self.alive    = False
                self.dev_dict = {}
                self.usb_dfu_timer.stop()
                self.usb_dfu_timer.start(300)
                return
        else:
            print "SCAN"
            self.usb_hid_scan()
            for item in self.dev_dict:
                base_name = item.split(".")[0]
                print base_name[:-1]
                # 扫描 BOOT 设备
                if self.dev_pro.dfu_s == 0:
                    if base_name[:-1]== "JSQ_BOOT":
                        self.dev_dict[item].open()
                        self.dev_dict[item].set_raw_data_handler(self.usb_rev_to_buf)
                        self.report = self.dev_dict[item].find_output_reports()
                        self.alive  = True
                        self.dev_pro = dtq_xes_ht46(self.r_lcd_hook)
                        self.usb_rbuf_process.start()
                        self.usb_sbuf_process.start()
                        self.s_lcd_buf.put(u"打开设备:[ %s ] 成功！" % item )
                        self.usb_bt.setText(u"关闭USB设备")
                # 扫描 JSQ 设备
                if self.dev_pro.dfu_s == 3:
                    if base_name[:-1]== "DTQ_JSQ_":
                        self.dev_dict[item].open()
                        self.dev_dict[item].set_raw_data_handler(self.usb_rev_to_buf)
                        self.report = self.dev_dict[item].find_output_reports()
                        self.alive  = True
                        self.dev_pro = dtq_xes_ht46(self.r_lcd_hook)
                        self.usb_rbuf_process.start()
                        self.usb_sbuf_process.start()
                        self.s_lcd_buf.put(u"打开设备:[ %s ] 成功！" % item )
                        msg = self.dev_pro.get_check_wl_msg()
                        self.usb_snd_store(msg)
                        self.usb_bt.setText(u"关闭USB设备")
                        self.dev_pro.dfu_s = 0
                        self.usb_dfu_timer.stop()

    '''
    * Fun Name    : usb_snd_store
    * Description : HID 底层发送数据函数
    * Input       : msg
    '''
    def usb_snd_store(self, msg):
        # 复制指令码到发送数组
        self.snd_buf.put(msg)
        # debug_str = "S: "
        # for item in data:
        #    debug_str += " %02X" % (item)
        # print debug_str

    '''
    * Fun Name    : usb_cmd_snd_process
    * Description : HID 底层发送数据进程
    * Input       : msg
    '''
    def usb_cmd_snd_process(self):
        if not self.snd_buf.empty():
            msg = self.snd_buf.get()
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
                    self.usb_bt.setText(u"打开USB设备")
                    self.dev_dict = {}
                    self.alive = False
                    self.usb_sbuf_process.stop()
                    self.dev_pro.dfu_s = 3
                    self.usb_dfu_timer.start(300)
                    self.s_lcd_buf.put(u"发送数据失败！")
                r_cmd = u"发送数据：S : {0}".format(r_cmd)
                logging.debug(r_cmd)

    '''
    * Fun Name    : usb_rev_to_buf
    * Description : HID USB 接收数据钩子函数
    * Input       : data
    '''
    def usb_rev_to_buf(self, data):
        self.rev_buf.put(data)
        # debug_str = "R: "
        # for item in data:
        #    debug_str += " %02X" % (item)
        # print debug_str

    '''
    * Fun Name    : usb_cmd_rev_process
    * Description : 数据解析函数
    * Input       : None
    ''' 
    def usb_cmd_rev_process(self):
        if not self.rev_buf.empty():
            r_cmd = self.rev_buf.get()
            # 此处指令解析放在协议文件的内部实现，方便实现硬件的兼容
            tree_dict = self.dev_pro.answer_cmd_decode(self.uid_list, r_cmd)
            
            r_answer_cnt = 0
            s_answer_cnt = 0
            lost_rate = 100
            if  "cnt_r" in self.uid_list:
                for item in self.uid_list["cnt_r"]:
                    r_answer_cnt = r_answer_cnt + self.uid_list["cnt_r"][item]
                    s_answer_cnt = s_answer_cnt + self.uid_list["cnt_s1"][item]
                self.k_sum_lineedit.setText(str(s_answer_cnt))
                self.r_sum_lineedit.setText(str(r_answer_cnt))
                lost_rate = r_answer_cnt*100.0/s_answer_cnt
                self.k_rate_lineedit.setText("%f" % lost_rate)

            # 获取指令中的ID
            if tree_dict:
                logging.debug(u"接收数据：R : {0}".format(tree_dict))
                uid = tree_dict["UID"]
                # 更新 GUI 界面
                tree_key = "%010u" % uid
                if tree_key not in self.qtree_dict:
                    self.qtree_dict[tree_key] = QTreeWidgetItem(self.tree_com)
                    self.qtree_dict[tree_key].setText(0, str(len(self.qtree_dict)))
                    self.qtree_dict[tree_key].setText(1, tree_key)
                    if tree_dict["CMD"] in self.tree_name_pos:
                        str_msg = "%d:%010u:%d" % (self.tree_name_pos[tree_dict["CMD"]], uid, tree_dict[tree_dict["CMD"]])
                        self.r_tree_buf.put(str_msg)
                else:
                    str_msg = "%d:%010u:%d" % (self.tree_name_pos[tree_dict["CMD"]], uid, tree_dict[tree_dict["CMD"]])
                    self.r_tree_buf.put(str_msg)
                if tree_dict["CMD"] != "VOICE":
                    cur_msg  = u"[ %s ]: %7d " % (tree_dict["CMD"][0:2], tree_dict[tree_dict["CMD"]])
                    cur_msg += " "*16
                    cur_msg += u"[ RA ]: %3.3f" % (lost_rate)
                    s_msg = self.dev_pro.get_echo_cmd_msg(uid, cur_msg)
                    self.usb_snd_store(s_msg)

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
        if button_str == u"开始单选乒乓":
            s_msg = self.dev_pro.get_echo_cmd_msg(0x11223344, "cur_msg")
            self.usb_snd_store(s_msg)

        if button_str == u"清空数据":
            self.r_browser.clear()
            self.s_browser.clear()
            return

        if button_str == u"打开USB设备":
            usb_port = str(self.com_combo.currentText())
            if usb_port:
                self.dev_dict[usb_port].open()
                self.dev_dict[usb_port].set_raw_data_handler(self.usb_rev_to_buf)
                self.report = self.dev_dict[usb_port].find_output_reports()
                self.alive = True
                if self.dev_pro == None:
                    self.dev_pro = dtq_xes_ht46(self.r_lcd_hook)
                    self.usb_rbuf_process.start()
                    self.usb_sbuf_process.start()
                self.s_lcd_buf.put(u"打开设备:[ %s ] 成功！" % usb_port )
                msg = self.dev_pro.get_check_wl_msg()
                self.usb_snd_store(msg)
                self.usb_bt.setText(u"关闭USB设备")
                return

        if button_str == u"关闭USB设备":
            usb_port = str(self.com_combo.currentText())
            self.alive = False
            if self.dev_dict[usb_port]:
                self.dev_dict[usb_port].close()
                self.usb_rbuf_process.quit()
                self.report = None
                self.dev_pro = None
                self.s_lcd_buf.put(u"关闭设备成功！")
            self.usb_bt.setText(u"打开USB设备")
            return

        if button_str == u"发送题目":
            q_type =  unicode(self.q_combo.currentText())
            if self.alive:
                que_t = int(q_type.split(":")[1][2:])
                que_t = (que_t / 10)*16 +  que_t % 10
                # print que_t
                cur_msg   = unicode(self.q_lineedit.text())
                msg = self.dev_pro.get_question_cmd_msg( que_t, cur_msg )
                self.usb_snd_store( msg )
                self.s_lcd_buf.put(u"S: 发送题目 : %s : %s " % ( q_type, cur_msg ))
            return

        if button_str == u"发送数据":
            i = 0
            msg = unicode(self.cmd_lineedit.text())
            msg_str = u"S: 发送回显 : %s， UID：" % msg
            if "uid_list" in self.uid_list:
                for item in self.uid_list["uid_list"]:
                    cur_msg = u"[ %d ] %s" % (i, msg)
                    i = i + 1
                    s_msg = self.dev_pro.get_echo_cmd_msg(item, cur_msg)
                    self.usb_snd_store(s_msg)
                    msg_str = msg_str + " [ %10u ]" % item
                self.s_lcd_buf.put(msg_str)
            else:
                self.s_lcd_buf.put(u"白名单为空，请刷卡！")
            return

        if button_str == u"查看配置":
            if self.alive:
                msg = self.dev_pro.get_check_dev_info_msg()
                self.usb_snd_store(msg)
                self.s_lcd_buf.put(u"S: 查看设备信息 ")
            return

        if button_str == u"复位端口":
            if self.alive:
                port_type =  unicode(self.port_combo.currentText())
                port = int(port_type.split(":")[1][2:]) 
                msg = self.dev_pro.get_reset_port_msg(port)
                self.usb_snd_store(msg)
                self.s_lcd_buf.put(u"S: 复位端口 ")
            return

        if button_str == u"修改信道":
            if self.alive:
                ch = int(str(self.ch_lineedit.text()))
                msg = self.dev_pro.get_set_rf_ch_msg(ch)
                self.usb_snd_store(msg)
                self.s_lcd_buf.put(u"S: 修改信道 ")
            return

        if button_str == u"停止绑定":
            if self.alive:
                msg = self.dev_pro.get_bind_stop_msg()
                self.usb_snd_store(msg)
                self.bind_button.setText(u"开始绑定")
                self.s_lcd_buf.put(u"S: 停止绑定: 绑定结束！此时刷卡无效")
            return

        if button_str == u"开始绑定":
            if self.alive:
                msg = self.dev_pro.get_bind_start_msg()
                self.usb_snd_store(msg)
                self.bind_button.setText(u"停止绑定")
                self.s_lcd_buf.put(u"S: 开始绑定: 绑定开始！请将需要测试的答题器刷卡绑定！")
            return

        if button_str == u"清除配置":
            if self.alive:
                msg = self.dev_pro.get_clear_dev_info_msg()
                self.usb_snd_store(msg)
                self.s_lcd_buf.put(u"S: 清除配置: ")
            return
        
        if button_str == u"同步状态":
            if self.alive:
                devid = int(str(self.devid_lineedit.text()))
                led_ctl_type = unicode(self.led_combo.currentText())
                leds = int(led_ctl_type.split(":")[1][2:]) 
                beep_ctl_type = unicode(self.beep_combo.currentText())
                beeps = int(beep_ctl_type.split(":")[1][2:])
                motor_ctl_type = unicode(self.motor_combo.currentText())
                motors = int(motor_ctl_type.split(":")[1][2:])
                # print (devid, leds, beeps, motors)
                msg = self.dev_pro.get_dtq_ctl_msg(devid, leds, beeps, motors)
                self.usb_snd_store(msg)
                self.s_lcd_buf.put(u"S: 同步状态: UID：[ %10u ]" % devid)
            return

        if button_str == u"查看白名单":
            if self.alive:
                msg = self.dev_pro.get_check_wl_msg()
                self.usb_snd_store(msg)
                self.s_lcd_buf.put(u"S: 查看白名单:")
            return
        
        if button_str == u"添加固件":
            image_path = unicode(QFileDialog.getOpenFileName(self, 'Open file', './', "bin files(*.bin)"))
            if len(image_path) > 0:
                self.fm_lineedit.setText(image_path)
            return

        if button_str == u"升级程序":
            image_path = unicode(self.fm_lineedit.text())
            if len(image_path) > 0:
                # print image_path
                self.dev_pro.dfu_s = 0
                self.dfu_pro = file_transfer(image_path, self.dev_pro.PAC_LEN - 21)
                self.usb_dfu_timer.start(300)
                self.progressDialog = QProgressDialog(self)
                self.progressDialog.setWindowModality(Qt.WindowModal)
                self.progressDialog.setMinimumDuration(5)
                self.progressDialog.setWindowTitle(u"请等待")
                self.progressDialog.setLabelText(u"下载中...")
                self.progressDialog.setCancelButtonText(u"取消")
                self.progressDialog.setRange(0,100)
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

    def usb_hid_scan(self):
        usb_list = hid.find_all_hid_devices()
        if usb_list  :
            for device in usb_list:
                device_name = unicode("{0.product_name}").format(device)
                if device_name[0:3] == "DTQ" or device_name[0:3] == "JSQ":
                    serial_number = unicode("{0.serial_number}").format(device)
                    cur_usb_name = device_name+"_"+serial_number
                    if  cur_usb_name not in self.dev_dict:
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

if __name__=='__main__':
    app = 0
    app = QApplication(sys.argv)
    datburner = dtq_hid_debuger()
    datburner.show()
    sys.exit(app.exec_())
    if datburner.alive:
        msg = datburner.dev_pro.get_question_cmd_msg( 0x80, u"关闭软件" )
        datburner.usb_snd_store( msg )
        while not datburner.snd_buf.empty():
            time.sleep(10)
        

