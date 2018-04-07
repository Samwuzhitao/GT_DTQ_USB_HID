# 软件修改日志
************************************************************************************
**版　　本:v0.1.0**
**开发目的**:此版本为学而思定制的初始版本，用来测试丢包率
**特性描述**: 
************************************************************************************
**时间**:2017-10-08
**描述**:
> 1. HID_DEBUGER 建立初始工程

**时间**:2017-10-09
**描述**:
> 1. 基本完成回显指令及相关测试功能
> 2. 完成刷卡上报及应答
> 3. 增加修改信道的功能
> 4. 修改卡号显示，支持反码显示
> 5. 支持发送题目功能
> 6. 增加查看白名单指令

**时间**:2017-10-13
**描述**:
> 1. 修复发送答案之后第一个提交答案错乱的问题

**时间**:2017-10-16
**描述**:
> 1. 增加一些指令的发送结果的显示，支持清除配置信息接口

**时间**:2017-10-20
**描述**:
> 1. 增加修改包过滤机制
> 2. 修改数据提交的过滤机制，在UID的层面上过滤数据
> 3. 完善拼包逻辑，支持查看白名单接口

**时间**:2017-11-06
**描述**:
> 1. 增加6键单选

**时间**:2017-11-07
**描述**:
> 1. 增加统计功能
> 2. 对输入数据增加CRC校验，防止出现异常数据
> 3. 增加重启次数计数功能

**时间**:2017-11-22
**描述**:
> 1. 修复刷卡会引起小工具死机的BUG

************************************************************************************
**版　　本:v1.6.4**
**开发目的**:为了显示设备名称，方便查找USB名称突然变成@input的问题
**特性描述**: 
************************************************************************************
**时间**:2017-12-22
**描述**:
> 1. 显示打开设备的设备名称
> 2. 修复具有相同设备民称的设备切换无效的BUG

************************************************************************************
**版　　本:v1.6.5**
**开发目的**: 增加配置信息查看输出窗口
**特性描述**: 
************************************************************************************
**时间**:2017-12-22
**描述**:
> 1. 回显增加随机汉字显示功能
> 2. LOG信息输出增加配置信息独立串口

************************************************************************************
**版　　本:v1.6.6**
**开发目的**: 增加乒乓测试功能
**特性描述**: 
************************************************************************************
**时间**:2017-12-22
**描述**:
> 1. 增加单选乒乓测试功能

************************************************************************************
**版　　本:v1.7.0**
**开发目的**: 完成程序下载功能
**特性描述**: 
************************************************************************************
**时间**:2018-01-09
**描述**:
> 1. 完成基本程序框架大搭建
> 2. 使用字符串分割split函数简化发送题目信息获取
> 3. 完成镜像信息的下载

**时间**:2018-01-11
**描述**:
> 1. 完成简单基本的下载功能
> 2. 增加进度天显示下载进度
> 3. 完成简单的一键升级功能

************************************************************************************
**版　　本:v2.0.0**
**开发目的**: 支持语音接收器
**特性描述**: 
************************************************************************************
**时间**:2018-01-11
**描述**:
> 1. 基本完成语音接收器的数据收发功能

**时间**:2018-03-10
**描述**:
> 1. 完成语音数据组包播放逻辑
> 2. 直接开启一个进程处理答题器提交数据，而非使用信号与槽，测试6路答题器语音无压力

************************************************************************************
**版　　本:v2.0.2**
**开发目的**: 支持语音接收器
**特性描述**: 
************************************************************************************
**时间**:2018-03-11
**描述**:
> 1. 优化代码结构，为兼容DTQ_JSQ_V0300留下空间

**时间**:2018-03-13
**描述**:
> 1. 完成题目回显机刷卡指令，实现基本指令的测试

**时间**:2018-03-16
**描述**:
> 1. 重构显示逻辑，解决在UI进程中计数不准确的问题

**时间**:2018-03-19
**描述**:
> 1. 完善协议指令，增加开始绑定、停止绑定、清除配置等

************************************************************************************
**版　　本:v2.0.3**
**开发目的**: 支持语音接收器
**特性描述**: 
************************************************************************************
**时间**:2018-03-20
**描述**:
> 1. 将发送数据独立出一个进程处理，并增加回显

************************************************************************************
**版　　本:v2.0.4**
**开发目的**: 支持语音接收器
**特性描述**: 
************************************************************************************
**时间**:2018-03-23
**描述**:
> 1. 增加数据包综合统计信息输出
> 2. 增加查看白名单按键功能

************************************************************************************
**版　　本:v2.0.5**
**开发目的**: 支持语音接收器
**特性描述**: 
************************************************************************************
**时间**:2018-03-28
**描述**:
> 1. 修复下发停止作答的指令BUG
> 2. 完善 LED、蜂鸣器、电机等指令
> 3. 增加固件更新功能

**时间**:2018-03-31
**描述**:
> 1. 使用 Queue 替换原先的列表作为缓存，调试信息输出剥离线程，保证线程安全

**时间**:2018-04-07
**描述**:
> 1. 增加监测工具功能