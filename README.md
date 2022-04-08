# SMTP POP3 IMAP mail parsing MySQL distributed storage
****
## 一.项目重要步骤：
### 1.判断是否指定日期路径传入
    sys.argv[2]指定格式 例如20211231
    sys.argv[2] == null时 默认处理当天数据
### 2.mysql数据库建立
    建立格式：年月日
### 3.遍历目标文件夹下面的全部pcapng文件
### 4.dpkt解析
    (1) 以太网数据包
    (1) 网络层:ip len ttl source_ip target_ip
    (2) 传输层:tcp sport dport
### 5.正则表达式提取邮件文字信息解析
    host_name:主机名
    mail_from:邮件发送方
    mail_to:邮件接收方
    x_mail:邮件客户端
    mail_subject:邮件主题
    mail_priority:邮件设置等级
    message_id:邮件id
    mail_content:邮件内容
### 6.图片信息判断并且单独存储
    if tmp["mail_image"] != '':
        mail_image_str = tmp["mail_image"].split(">")[1]
        mail_image_download(mail_image_str, file_name)
### 8.mysql数据库存储
### 9.开启多线程处理函数
****
## 二.`MySQL`分库分表
### 按照`SMTP` `POP3` `IMAP`分成3个数据库存储在不同服务器，并且按照月份进行存储，每月按照日期分表
### 详情见`Distributed-MySQL`
****
## 三.定时调度
### crontab按照每10分钟进行调度一次，因为数据推送间隔并不是固定的
