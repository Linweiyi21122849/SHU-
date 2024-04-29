#! /usr/bin/python
# -*- coding: UTF-8 -*-
import pymysql
from timeit import default_timer

#需要你自己配置
host = 'localhost'
port = 3306
db = 'library_sys'
user = 'root'
password = '1800538123'

def get_connection():
    #这个函数用于创建并返回一个 pymysql 的数据库连接对象。
    conn = pymysql.connect(host=host, port=port, db=db, user=user, password=password)
    return conn

# ---- 使用 with 的方式来优化代码
class UsingMysql(object):

    def __init__(self, commit=True):
        """
        :param commit: 是否在最后提交事务(设置为False的时候方便单元测试)
        """
        self._commit = commit

    def __enter__(self):
        # 在进入的时候自动获取连接和cursor
        conn = get_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        conn.autocommit = False

        self._conn = conn
        self._cursor = cursor
        return self

    def __exit__(self, *exc_info):
        # 提交事务
        if self._commit:
            self._conn.commit()
        # 在退出的时候自动关闭连接和cursor
        self._cursor.close()
        self._conn.close()

    @property
    def cursor(self):
        return self._cursor

