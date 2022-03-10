# -*- coding: utf-8 -*-
# @Time : 2021/12/31 15:29
# @Author : O·N·E
# @File : Mail_Process.py
import base64
import datetime, time
import os
import re
import glob
import socket
import sys
import dpkt
import threading
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from multiprocessing import Pool
from DButils import Create_SMTP_database, Create_POP3_database, Create_IMAP_database
from DButils import Create_mycat_SMTP_database, Create_mycat_POP3_database, Create_mycat_IMAP_database
from DButils import re_content

# 端口列表
dport_list = [25, 110, 143]


# 获取北京时间戳
def local_Date():
    # 获取当前时间
    today = time.localtime(time.time())
    year_initial = str(today[0])
    month_initial = today[1]
    day_initial = today[2]
    # 判断数字是否小于十位补0
    if month_initial or day_initial < 10:
        month = str(month_initial).zfill(2)
        day = str(day_initial).zfill(2)
    else:
        month = month_initial
        day = day_initial
    return year_initial, month, day


# 当前时间文件路径
def locaL_Date_path(root):
    year_initial, month, day = local_Date()
    # pcapng文件获取
    files = '*.pcapng'
    root_y_mon_d = os.path.join(root, year_initial, year_initial + month, year_initial + month + day)
    pcapng_all_file_path = os.path.join(root_y_mon_d, files)
    ok_path = os.path.join(root_y_mon_d, "ok")
    image_path = os.path.join(root_y_mon_d, "image")
    table_name = "{}_{}_{}".format(year_initial, month, day)
    table_name_ = "{}_{}".format(year_initial, month)
    return pcapng_all_file_path, root_y_mon_d, ok_path, image_path, root, table_name, table_name_


# 指定时间文件路径
def Specify_Date_path(root, Specify_Date):
    # pcapng文件获取
    files = '*.pcapng'
    Specify_year = Specify_Date[:4]
    Specify_mon = Specify_Date[4:6]
    Specify_day = Specify_Date[6:8]
    root_y_mon_d = os.path.join(root, Specify_year, Specify_year + Specify_mon, Specify_year + Specify_mon + Specify_day)
    pcapng_all_file_path = os.path.join(root_y_mon_d, files)
    ok_path = os.path.join(root_y_mon_d, "ok")
    image_path = os.path.join(root_y_mon_d, "image")
    table_name = "{}_{}_{}".format(Specify_year, Specify_mon, Specify_day)
    table_name_ = "{}_{}".format(Specify_year, Specify_mon)
    return pcapng_all_file_path, root_y_mon_d, ok_path, image_path, root, table_name, table_name_


# base64邮件图片下载
def mail_image_download(base64_content, file_name):
    image_data = base64.b64decode(base64_content)
    image_file_path = image_path + "\\" + file_name + ".jpg"
    with open(image_file_path, "wb") as fp:
        fp.write(image_data)


def mail_parse(pcapng):
    """
    解析数据包的内容
    buf:数据包的缓冲区
    sport:客户端端口号
    dport:服务器端口号
    source_ip:源目标ip地址
    target_ip:目标ip地址
    len:ip包的总长度比特，以字节为单位
    ttl:生存时间
    """
    for timestamp, buf in pcapng:
        # 解析成以太网数据包
        eth = dpkt.ethernet.Ethernet(buf)
        # 解析成网络层
        ip = eth.data
        len = ip.len
        ttl = ip.ttl
        source_ip = socket.inet_ntoa(ip.src)
        target_ip = socket.inet_ntoa(ip.dst)
        # 解析成传输层
        tcp = ip.data
        sport = tcp.sport
        dport = tcp.dport
        # 获取基础头信息,时间戳
        timestamp = str(datetime.datetime.fromtimestamp(timestamp))
        if dport in dport_list:
            mail_packet_list = [timestamp, sport, dport, source_ip, target_ip, ttl, len]
            break
    """
    邮件文字内容解析：
    host_name:主机名
    mail_from:邮件发送方
    mail_to:邮件接收方
    x_mail:邮件客户端
    mail_subject:邮件主题
    mail_priority:邮件设置等级
    message_id:邮件id
    mail_content:邮件内容
    """
    content_list = []
    for timestamp, buf in pcapng:
        eth = dpkt.ethernet.Ethernet(buf)
        content = str(eth.data.data.data).split("'")[1]
        content_re = re.sub(r"\\r|\\n", "", content)
        content_list.append(content_re)
    # 清除空白信息
    content_list_info = [i for i in content_list if i != '']
    mail_info = ','.join(content_list_info)
    # print(mail_info)
    return mail_packet_list, mail_info


def database_insert(mail_packet_list, mail_info, file_path, file_name, smtp_cur, smtp_conn, pop3_cur, pop3_conn, imap_cur, imap_conn, table_name):
    """
    :param mail_packet_list: 邮件包信息解析列表
    :param mail_info: 邮件信息内容
    :param file_path: pcapng文件的详细目录
    :param table_name: 表名称
    """
    lock = threading.Lock()
    tmp = {}
    # 信息查找并提取
    if mail_packet_list[2] == 25:
        table_name_year_month = "SMTP_" + table_name_
        try:
            tmp["host_name"] = re.findall(r"EHLO (.+?),", mail_info)[0]
        except:
            tmp["host_name"] = ''
        try:
            tmp["mail_from"] = re.findall(r"MAIL FROM: <(.+?)>", mail_info)[0]
        except:
            tmp["mail_from"] = ''
        try:
            tmp["mail_to"] = re.findall(r"RCPT TO: <(.+?)>", mail_info)[0]
        except:
            tmp["mail_to"] = ''
    elif mail_packet_list[2] == 110:
        table_name_year_month = "POP3_" + table_name_
        try:
            tmp["host_name"] = re.findall(r"from (.+?) [\(]", mail_info)[0]
        except:
            tmp["host_name"] = ''
        try:
            tmp["mail_from"] = re.findall(r"From: [\"](.+?)[\"] <", mail_info)[0]
        except:
            tmp["mail_from"] = ''
        try:
            tmp["mail_to"] = [i.split("<")[1] for i in re.findall(r"To: (.+?)>", mail_info)][0]
        except:
            tmp["mail_to"] = ''
    elif mail_packet_list[2] == 143:
        table_name_year_month = "IMAP_" + table_name_
        try:
            tmp["host_name"] = re.findall(r"Received: from (.+?) ", mail_info)[-1]
        except:
            tmp["host_name"] = ''
        try:
            tmp["mail_from"] = re.findall(r"From: [\"](.+?)[\"] <", mail_info)[0]
        except:
            tmp["mail_from"] = ''
        try:
            tmp["mail_to"] = [i.split("<")[1] for i in re.findall(r"To: (.+?)>", mail_info)][0]
        except:
            tmp["mail_to"] = ''
    tmp["x_mailer"], tmp["mail_subject"], tmp["mail_priority"], tmp["message_id"], tmp["mail_content"], tmp["mail_image"] = re_content(mail_info)
    # 判断邮件是否图片信息
    if tmp["mail_image"] != '':
        mail_image_str = tmp["mail_image"].split(">")[1]
        mail_image_download(mail_image_str, file_name)
    # mail_content 邮件内容base64解析
    decrypt_mail_content = base64.b64decode(tmp["mail_content"]).decode("utf-8").strip()
    # mysql邮件内容MySQL插入
    column_name = "insert_time,timestamp, sport, dport, source_ip, target_ip,len,ttl, host_name, mail_from, mail_to, x_mail, mail_subject, mail_priority, message_id,mail_content"
    sql = "insert into {table_name_year_month} (id,{column_name},file_path,image_sign,parse_sign) values(next value for MYCATSEQ_ORDERS,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    year_initial, month, day = local_Date()
    insert_time = year_initial + "-" + month + "-" + day
    timestamp = mail_packet_list[0]
    sport = mail_packet_list[1]
    dport = mail_packet_list[2]
    source_ip = mail_packet_list[3]
    target_ip = mail_packet_list[4]
    len = mail_packet_list[5]
    ttl = mail_packet_list[6]
    success_number = 1
    fail_number = 0

    # 判断邮件是否存在图片
    if tmp["mail_image"] != '':
        success_index_values = insert_time, timestamp, sport, dport, source_ip, target_ip, len, ttl, tmp[
            "host_name"], tmp["mail_from"], tmp["mail_to"], tmp["x_mailer"], tmp["mail_subject"], tmp["mail_priority"], tmp[
                                   "message_id"], decrypt_mail_content, file_path, success_number, success_number
    else:
        success_index_values = insert_time, timestamp, sport, dport, source_ip, target_ip, len, ttl, tmp[
            "host_name"], tmp["mail_from"], tmp["mail_to"], tmp["x_mailer"], tmp["mail_subject"], tmp["mail_priority"], tmp[
                                   "message_id"], decrypt_mail_content, file_path, fail_number, success_number
    try:
        if mail_packet_list[2] == 25:
            lock.acquire()
            try:
                smtp_cur.execute(sql.format(table_name_year_month=table_name_year_month, column_name=column_name), success_index_values)
            except:
                sql = "insert into {table_name_year_month}(id,insert_time,file_path,parse_sign) values(next value for MYCATSEQ_ORDERS,%s,%s,%s)"
                smtp_cur.execute(sql.format(table_name_year_month=table_name_year_month), (insert_time, file_path, fail_number))
            smtp_conn.commit()
            lock.release()
            # smtp_cur.close()
            # smtp_conn.close()
        elif mail_packet_list[2] == 110:
            lock.acquire()
            try:
                pop3_cur.execute(sql.format(table_name_year_month=table_name_year_month, column_name=column_name), success_index_values)
            except:
                sql = "insert into {table_name_year_month} (id,insert_time,file_path,parse_sign) values(next value for MYCATSEQ_ORDERS,%s,%s,%s)"
                pop3_cur.execute(sql.format(table_name_year_month=table_name_year_month), (insert_time, file_path, fail_number))
            pop3_conn.commit()
            lock.release()
        elif mail_packet_list[2] == 143:
            lock.acquire()
            try:
                imap_cur.execute(sql.format(table_name_year_month=table_name_year_month, column_name=column_name), success_index_values)
            except:
                sql = "insert into {table_name_year_month} (id,insert_time,file_path,parse_sign) values(next value for MYCATSEQ_ORDERS,%s,%s,%s)"
                imap_cur.execute(sql.format(table_name_year_month=table_name_year_month), (insert_time, file_path, fail_number))
            imap_conn.commit()
            lock.release()

    except Exception as e:
        print("{}数据插入{}失败".format(file_path, table_name), e)

    # 文件标记
    # file = open(os.path.join(ok_path, file_name + ".txt"), "w")
    # file.close()


def mail_read(file_path, file_name):
    """
    pcapng文件处理
    :param pcapng_all_file_path: 给定日期pcapng文件路径
    :param ok_path: 给定日期的文件夹下面创建一个ok文件夹
    """
    # 数据库创建
    smtp_cur, smtp_conn = Create_mycat_SMTP_database(table_name_)
    pop3_cur, pop3_conn = Create_mycat_POP3_database(table_name_)
    imap_cur, imap_conn = Create_mycat_IMAP_database(table_name_)

    # pcap文件二进制读取
    with open(file_path, "rb") as fp:
        pcapng = dpkt.pcapng.Reader(fp)
        try:
            mail_packet_list, mail_info = mail_parse(pcapng)  # pcapng文件解析
            database_insert(mail_packet_list, mail_info, file_path, file_name, smtp_cur, smtp_conn, pop3_cur, pop3_conn, imap_cur, imap_conn,
                            table_name)
            # database_insert(mail_packet_list, mail_info, file_path, file_name, table_name)  # 结果数据库插入
        except dpkt.dpkt.NeedData:
            print("{}未解析到数据".format(file_path))


if __name__ == '__main__':
    a = time.time()
    # 判断是否指定日期路径传入
    """sys.argv[2]指定格式 例如20211231"""
    Specify_Date = sys.argv[2]
    if Specify_Date == 'null':
        pcapng_all_file_path, root_y_mon_d, ok_path, image_path, root, table_name, table_name_ = locaL_Date_path(sys.argv[1])
    else:
        pcapng_all_file_path, root_y_mon_d, ok_path, image_path, root, table_name, table_name_ = Specify_Date_path(sys.argv[1], Specify_Date)
    if not os.path.exists(ok_path):
        os.mkdir(ok_path)
    if not os.path.exists(image_path):
        os.mkdir(image_path)

        # 数据库建立
    # 年月日表格建立
    Create_SMTP_database(table_name)
    Create_POP3_database(table_name)
    Create_IMAP_database(table_name)
    # 年月表格建立

    # 多线程
    file_paths = []
    # 遍历文件夹下面所有的pcap文件
    for file_path in glob.glob(pcapng_all_file_path):
        file_name = re.split('\\\|\.', file_path)[-2]  # pcapng文件的名字
        res = os.path.exists(os.path.join(ok_path, file_name + ".txt"))
        if res == False:
            file_paths.append(file_path)
        else:
            print("fail")
    with ThreadPoolExecutor(50) as thread:
        for file_path in file_paths:
            file_name = re.split('\\\|\.', file_path)[-2]
            future_tasks = thread.submit(mail_read, file_path, file_name)

    b = time.time()
    print(b - a)
