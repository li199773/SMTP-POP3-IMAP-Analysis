# -*- coding: utf-8 -*-
# @Time : 2021/12/21 21:24
# @Author : O·N·E
# @File : DButils.py
import re
import pymysql

# mysql ip地址
host_imap = '192.168.81.245'
host_pop3 = '192.168.81.216'
host_smtp = '192.168.81.242'
host_mycat = '192.168.81.211'
# 端口号
port = 3306
port_mycat = 8066
# 登录名
user = "root"
# 密码
password = "123456"
charset = "utf8"


def table_sql_name(table_name_):
    sql = "create table if not exists " + table_name_ + """(
                        id int(32) primary key,
                        insert_time date DEFAULT NULL,
                        timestamp timestamp,
                        sport int,
                        dport int,
                        source_ip char(30),
                        target_ip char(30),
                        len int,
                        ttl int,
                        host_name varchar(50),
                        mail_from varchar(50),
                        mail_to varchar(50),
                        x_mail varchar(50),
                        mail_subject varchar(1000),
                        mail_priority int,
                        message_id varchar(50),
                        mail_content varchar(10000),
                        file_path varchar(200),
                        image_sign int,
                        parse_sign int
                        )
                    """
    return sql


def Create_SMTP_database(table_name):
    smtp_table_name = "smtp_" + table_name
    sql = table_sql_name(smtp_table_name)
    smtp_conn = pymysql.connect(
        host=host_smtp,
        port=port,
        user=user,
        password=password,
        database='smtp_database',
        charset=charset
    )
    smtp_cur = smtp_conn.cursor()
    smtp_cur.execute(sql)


def Create_POP3_database(table_name):
    pop3_table_name = "pop3_" + table_name
    sql = table_sql_name(pop3_table_name)
    pop3_conn = pymysql.connect(
        host=host_pop3,
        port=port,
        user=user,
        password=password,
        database='pop3_database',
        charset=charset
    )
    pop3_cur = pop3_conn.cursor()
    pop3_cur.execute(sql)


def Create_IMAP_database(table_name):
    imap_table_name = "imap_" + table_name
    sql = table_sql_name(imap_table_name)
    imap_conn = pymysql.connect(
        host=host_imap,
        port=port,
        user=user,
        password=password,
        database='imap_database',
        charset=charset
    )
    imap_cur = imap_conn.cursor()
    imap_cur.execute(sql)


def Create_mycat_SMTP_database(table_name):
    table_name_year_month = "smtp_" + table_name
    sql = table_sql_name(table_name_year_month)
    smtp_conn = pymysql.connect(
        host=host_mycat,
        port=port_mycat,
        user=user,
        password=password,
        database='mycat',
        charset=charset
    )
    smtp_cur = smtp_conn.cursor()
    smtp_cur.execute(sql)

    # smtp_cur.execute("show tables")
    # table_list = [tuple[0] for tuple in smtp_cur.fetchall()]
    # print(table_list)
    return smtp_cur, smtp_conn


def Create_mycat_POP3_database(table_name):
    table_name_year_month = "pop3_" + table_name
    sql = table_sql_name(table_name_year_month)
    pop3_conn = pymysql.connect(
        host=host_mycat,
        port=port_mycat,
        user=user,
        password=password,
        database='mycat',
        charset=charset
    )
    pop3_cur = pop3_conn.cursor()
    pop3_cur.execute(sql)
    return pop3_cur, pop3_conn


def Create_mycat_IMAP_database(table_name):
    table_name_year_month = "imap_" + table_name
    sql = table_sql_name(table_name_year_month)
    imap_conn = pymysql.connect(
        host=host_mycat,
        port=port_mycat,
        user=user,
        password=password,
        database='mycat',
        charset=charset
    )
    imap_cur = imap_conn.cursor()
    imap_cur.execute(sql)
    return imap_cur, imap_conn


def re_content(text):
    tmp = {}
    try:
        tmp["x_mailer"] = re.findall(r"X-Mailer: (.+?)[\[]", text)[0]
    except:
        tmp["x_mailer"] = ''
    try:
        tmp["mail_subject"] = re.findall(r"Subject: (.+?)X", text)[0]
    except:
        tmp["mail_subject"] = ''
    try:
        tmp["mail_priority"] = re.findall(r"X-Priority: (.+?)X", text)[0]
    except:
        tmp["mail_priority"] = ''
    try:
        tmp["message_id"] = re.findall(r"Message-ID: <(.+?)>", text)[0]
    except:
        tmp["message_id"] = ''
    try:
        tmp["mail_content"] = re.findall(r"Content-Transfer-Encoding: base64(.+?)-", text)[0]
    except:
        tmp["mail_content"] = ''
    try:
        tmp["mail_image"] = re.findall(r"Content-ID: <(.+?)------=_", text)[0]
    except:
        tmp["mail_image"] = ''
    return tmp["x_mailer"], tmp["mail_subject"], tmp["mail_priority"], tmp["message_id"], tmp["mail_content"], tmp["mail_image"]
