# ChangeLog:
*****************************************************************************************
* **版　　本:V0.1.0**
* **开发目的**:此版本为学而思定制的初始版本，用来测试丢包率
* **特性描述**: 
*****************************************************************************************
* **时间**:2017-10-08
* **描述**:
> 1. HID_DEBUGER 建立初始工程

* **时间**:2017-10-09
* **描述**:
> 1. 基本完成回显指令及相关测试功能
> 2. 完成刷卡上报及应答
> 3. 增加修改信道的功能
> 4. 修改卡号显示，支持反码显示
> 5. 支持发送题目功能
> 6. 增加查看白名单指令

* **时间**:2017-10-13
* **描述**:
> 1. 修复发送答案之后第一个提交答案错乱的问题

* **时间**:2017-10-16
* **描述**:
> 1. 增加一些指令的发送结果的显示，支持清除配置信息接口

* **时间**:2017-10-20
* **描述**:
> 1. 增加修改包过滤机制
> 2. 修改数据提交的过滤机制，在UID的层面上过滤数据
> 3. 完善拼包逻辑，支持查看白名单接口

* **时间**:2017-11-06
* **描述**:
> 1. 增加6键单选

* **时间**:2017-11-07
* **描述**:
> 1. 增加统计功能
> 2. 对输入数据增加CRC校验，防止出现异常数据
> 3. 增加重启次数计数功能

* **时间**:2017-11-22
* **描述**:
> 1. 修复刷卡会引起小工具死机的BUG
