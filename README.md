# SMTP POP3 IMAP mail parsing MySQL distributed storage
****
## 项目的步骤：
### 1.判断是否指定日期路径传入
    sys.argv[2]指定格式 例如20211231
    sys.argv[2] == null时 默认处理当天数据
### 2.mysql数据库建立
    建立格式：年月日
### 3.遍历目标文件夹下面的全部pcapng文件
### 2.开启多线程处理函数
