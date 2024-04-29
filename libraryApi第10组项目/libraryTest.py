import json
import datetime  # 需要用当日的时间
import random
import dateutil
# from datetime import date
from dateutil.parser import parse
import dateutil
from utils.pymysql_comm import UsingMysql
from utils.email_sender import EmailSender

penalty_per_day = 0.05      # 逾期书刊每册每天罚款 0.05 元
def check_transactor(librarian_id):
    with UsingMysql() as um:
        librarian_check_sql = 'SELECT 1 FROM librarian WHERE librarian_id = %s'
        um.cursor.execute(librarian_check_sql, (librarian_id,))
        librarian_existed = um.cursor.fetchone()
        if librarian_existed is None:
            return 0
        return 1

def check_date_format(date_string):
    try:
        dateutil.parser.parse(date_string)
        return True
    except ValueError:
        return False

# 发送验证码
def sendVerCode(data):
    rand=str(random.randint(10011, 99992))
    sender = EmailSender()
    reciever_list = []
    reciever_list.append(data["mail"])
    sender.send(reciever_list, "注册验证码",
                rand)
    return rand

#用户注册，检查用户手机号、邮箱是否重复（phoneRepeat、mailRepeat）
# {"user": user.value, "phone": phone.value, "mail": mail.value, "code": pw.value}:
def registerCheck0(data):
    with UsingMysql() as um:
        um.cursor.execute("select 1 from reader where phone=%s", (data["phone"],))
        check = um.cursor.fetchone()
        if check is not None:
            return "phoneRepeat"
        um.cursor.execute("select 1 from reader where email=%s", (data["mail"],))
        check = um.cursor.fetchone()
        if check is not None:
            return "mailRepeat"
        insert_sql="""INSERT INTO reader(name,phone,email,password) 
                    VALUES (%s,%s,%s,%s)"""
        um.cursor.execute(insert_sql, (data["user"],data["phone"], data["mail"], data["code"],))
        return '1'

# 管理员注册，检查管理员工号是否重复（workNumRepeat）
# {"user": user.value, "worknum": work_num.value ,"code": pw.value}
def registerCheck1(data):
    with UsingMysql() as um:
        um.cursor.execute("select 1 from librarian where librarian_id=%s", (data["worknum"],))
        check = um.cursor.fetchone()
        if check is not None:
            return "workNumRepeat"
        insert_sql="""INSERT INTO librarian(librarian_id,name,password) 
                    VALUES (%s,%s,%s)"""
        um.cursor.execute(insert_sql, (data["worknum"],data["user"], data["code"],))
        return '1'
#------------------------------------------------------------------------------------------
# 用户登录 要求输入手机号和密码
def loginCheck0(data):
    phone = data["phone"]
    password = data["code"]
    with UsingMysql() as um:
        um.cursor.execute("select * from reader where phone=%s and password=%s", (phone, password))
        datas = um.cursor.fetchall()
        if len(datas) == 0:  # 检查用户账号是否正确（正确为1，否则0）
            return '0'
        else:
            return '1'


# 管理员登录 要求输入管理员ID和密码
def loginCheck1(data):
    id = data["ID"]
    password = data["code"]
    with UsingMysql() as um:
        um.cursor.execute("select * from librarian where librarian_id=%s and password=%s", (id, password))
        datas = um.cursor.fetchall()
        if len(datas) == 0:  # 检查用户账号是否正确（正确为1，否则0）
            return '0'
        else:
            return '1'


# 数据库date类型的特殊json处理
class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.date):  # 用于检查对象 obj 是否是 datetime 类型的实例。
            return obj.isoformat()
        return super().default(obj)


# 传输用户书目信息（最大页数、name、author、publisher、isbn、time、num、transactor + 是否预约）
def userCatelogs(data):
    rid = data["ID"]
    page = data["pageNum"]
    row1 = (page - 1) * 7 + 1
    row2 = page * 7
    row = 0

    with UsingMysql() as um:
        # 查询图书信息
        um.cursor.execute("SELECT * FROM cip")
        datas = um.cursor.fetchall()

        # 查询每本书在流通室的可借复本数量
        num_by_isbn = {}
        for data in datas:
            isbn = data["isbn"]
            um.cursor.execute(
                "SELECT COUNT(*) as num FROM book WHERE isbn = %s AND location = '图书流通室' AND status = 0", (isbn,))
            result = um.cursor.fetchone()
            num_by_isbn[isbn] = result["num"]

        # 查询读者的预约信息,构建一个isbn的集合
        um.cursor.execute("SELECT isbn FROM reserve WHERE reader_id = %s", (rid,))
        reserved_books = set(row["isbn"] for row in um.cursor.fetchall())

        # 构建返回结果
        books = [{"max": int((len(datas) - 1) / 7 + 1)}]  # 最大页数为查询结果的数量
        for data in datas:
            row = row + 1
            isbn = data["isbn"]
            flag = isbn in reserved_books  # 判断是否被当前读者预约

            book_info = {
                "name": data["title"],
                "author": data["author"],
                "publisher": data["publisher"],
                "isbn": isbn,
                "time": data["publish_date"],
                "num": num_by_isbn.get(isbn, 0),
                "transactor": data["librarian_id"],
                "reserved": flag,
            }
            if row >= row1 and row <= row2:
                books.append(book_info)

    # 使用自定义的JSONEncoder来处理日期类型的序列化
    return json.dumps(books, cls=CustomEncoder, ensure_ascii=False)


# 传输用户信息（接收phone，传出ID、name、phone、mail）
# info = {"ID": "12345", "name": "无敌究极暴龙", "phone": "1231432", "mail": "11123423@163.com"}
def userInfo(data):
    phone = data["phone"]
    with UsingMysql() as um:
        um.cursor.execute("select * from reader where phone=%s", phone)
        datas = um.cursor.fetchone()
        info = {
            "ID": datas["reader_id"],
            "name": datas["name"],
            "phone": datas["phone"],
            "mail": datas["email"],
        }
    return json.dumps(info, ensure_ascii=False)


# 传输用户预约信息（最大页数 + name、author、publisher、isbn、time、ddl）
# data["pageNum"]
# reserves = [{"max": 2},
#            {"name": "数据结构", "author": "王作者", "publisher": "清华", "isbn": 1234, "time": "2023.1.1", "ddl": "2023.2.1"},
def userReserves(data):
    rid = data["ID"]
    page = data["pageNum"]
    row1 = (page - 1) * 7 + 1
    row2 = page * 7
    row = 0
    with UsingMysql() as um:
        um.cursor.execute("select * from reserve,cip where reader_id = %s and reserve.isbn = cip.isbn", rid)
        datas = um.cursor.fetchall()
        # 构建预约信息列表
        reserves = [{"max": int((len(datas) - 1) / 7 + 1)}]  # 最大页数为查询结果的数量
        for data in datas:
            row = row + 1
            length = data["reserve_period"]  # int类型
            reserve_date = data["reserve_date"]
            # 计算预约截止日期
            ddl = reserve_date + datetime.timedelta(days=length)
            reserve_info = {
                "name": data["title"],
                "author": data["author"],
                "publisher": data["publisher"],
                "isbn": data["isbn"],
                "time": reserve_date,
                "ddl": ddl
            }
            if row >= row1 and row <= row2:
                reserves.append(reserve_info)

    # 使用自定义的JSONEncoder来处理日期类型的序列化
    return json.dumps(reserves, cls=CustomEncoder, ensure_ascii=False)


# 传输用户借书信息（最大页数 + name、author、publisher、isbn、time、ddl）
def userSends(data):
    rid = data["ID"]
    page = data["pageNum"]
    row1 = (page - 1) * 7 + 1
    row2 = page * 7
    row = 0
    with UsingMysql() as um:
        # 查询图书信息
        check_borrow='''SELECT * FROM borrow,book,cip where
                      reader_id = %s and borrow.book_id = book.book_id 
                      and book.isbn = cip.isbn and return_date is null'''
        um.cursor.execute(check_borrow, rid)
        datas = um.cursor.fetchall()
        # 构建返回结果
        books = [{"max": int((len(datas) - 1) / 7 + 1)}]  # 最大页数为查询结果的数量
        for data in datas:
            row = row + 1
            book_info = {
                "name": data["title"],
                "author": data["author"],
                "publisher": data["publisher"],
                "isbn": data["isbn"],
                "time": data["borrow_date"],
                "ddl": data["due_date"],
            }
            if row >= row1 and row <= row2:
                books.append(book_info)
    print(books)
    # 使用自定义的JSONEncoder来处理日期类型的序列化
    return json.dumps(books, cls=CustomEncoder, ensure_ascii=False)


# 用户书目信息检索（最大页数 + name、author、publisher、isbn、time、num、transactor + 是否预约）
# books = [{"max": 3},{"name": "数据结构", "author": "王作者", "publisher": "清华", "isbn": 1234, "time": "2023.1.1", "num": 0,"transactor":1, "reserved": "1"}]
def searchUserCatelog(data):
    name = data["name"]
    rid = data["ID"]
    page = data["pageNum"]
    row1 = (page - 1) * 7 + 1
    row2 = page * 7
    row = 0
    with UsingMysql() as um:
        # 查询图书信息
        um.cursor.execute("SELECT * FROM cip WHERE title LIKE %s", ('%' + name + '%',))
        datas = um.cursor.fetchall()

        # 查询每本书在流通室的可借复本数量
        num_by_isbn = {}
        for data in datas:
            isbn = data["isbn"]
            um.cursor.execute(
                "SELECT COUNT(*) as num FROM book WHERE isbn = %s AND location = '图书流通室' AND status = 0", (isbn,))
            result = um.cursor.fetchone()
            num_by_isbn[isbn] = result["num"]

        # 查询读者的预约信息,构建一个isbn的集合
        um.cursor.execute("SELECT isbn FROM reserve WHERE reader_id = %s", (rid,))
        reserved_books = set(row["isbn"] for row in um.cursor.fetchall())

        # 构建返回结果
        books = [{"max": int((len(datas) - 1) / 7 + 1)}]  # 最大页数为查询结果的数量
        for data in datas:
            row = row + 1
            isbn = data["isbn"]
            flag = isbn in reserved_books  # 判断是否被当前读者预约

            book_info = {
                "name": data["title"],
                "author": data["author"],
                "publisher": data["publisher"],
                "isbn": isbn,
                "time": data["publish_date"],
                "num": num_by_isbn.get(isbn, 0),
                "transactor": data["librarian_id"],
                "reserved": flag,
            }
            if row >= row1 and row <= row2:
                books.append(book_info)

    # 使用自定义的JSONEncoder来处理日期类型的序列化
    return json.dumps(books, cls=CustomEncoder, ensure_ascii=False)


# 用户预约信息检索（最大页数 + name、author、publisher、isbn、time、ddl）
# books = [{"max": 2},{"name": "计组", "author": "周作者", "publisher": "北大", "isbn": 4321, "time": "2023.9.9", "ddl": "2023.10.9"}]
def searchUserReserve(data):
    name = data["name"]
    rid = data["ID"]
    page = data["pageNum"]
    row1 = (page - 1) * 7 + 1
    row2 = page * 7
    row = 0
    with UsingMysql() as um:
        um.cursor.execute(
            "select * from reserve,cip where reader_id = %s and reserve.isbn = cip.isbn and cip.title LIKE %s",
            (rid, '%' + name + '%'))
        datas = um.cursor.fetchall()
        # 构建预约信息列表
        reserves = [{"max": int((len(datas) - 1) / 7 + 1)}]  # 最大页数为查询结果的数量
        for data in datas:
            row = row + 1
            length = data["reserve_period"]  # int类型
            reserve_date = data["reserve_date"]
            # 计算预约截止日期
            ddl = reserve_date + datetime.timedelta(days=length)
            reserve_info = {
                "name": data["title"],
                "author": data["author"],
                "publisher": data["publisher"],
                "isbn": data["isbn"],
                "time": reserve_date,
                "ddl": ddl
            }
            if row >= row1 and row <= row2:
                reserves.append(reserve_info)

    # 使用自定义的JSONEncoder来处理日期类型的序列化
    return json.dumps(reserves, cls=CustomEncoder, ensure_ascii=False)


# 用户借书信息检索（最大页数 + name、author、publisher、isbn、time、ddl）
def searchUserSend(data):
    name = data["name"]
    rid = data["ID"]
    page = data["pageNum"]
    row1 = (page - 1) * 7 + 1
    row2 = page * 7
    row = 0
    with UsingMysql() as um:
        # 查询图书信息
        um.cursor.execute(
            "SELECT * FROM borrow,book,cip where reader_id = %s and borrow.book_id = book.book_id and book.isbn = cip.isbn and cip.title LIKE %s",
            (rid, '%' + name + '%'))
        datas = um.cursor.fetchall()
        # 构建返回结果
        books = [{"max": int((len(datas) - 1) / 7 + 1)}]  # 最大页数为查询结果的数量
        for data in datas:
            row = row + 1
            book_info = {
                "name": data["title"],
                "author": data["author"],
                "publisher": data["publisher"],
                "isbn": data["isbn"],
                "time": data["borrow_date"],
                "ddl": data["due_date"],
            }
            if row >= row1 and row <= row2:
                books.append(book_info)
    print(books)
    # 使用自定义的JSONEncoder来处理日期类型的序列化
    return json.dumps(books, cls=CustomEncoder, ensure_ascii=False)


# 用户预约（接收ID、isbn、当前时间python）
def userReserve(data):
    rid = data["ID"]
    isbn = data["isbn"]
    date = datetime.datetime.now().strftime('%Y-%m-%d')
    length = 10  # 预约期限为10天
    sql = """
    INSERT INTO reserve (reader_id, isbn, reserve_date, reserve_period)
    VALUES
        (%s, %s, %s, %s)
    """
    with UsingMysql() as um:
        um.cursor.execute(sql, (rid, isbn, date, length))

    return


# 用户取消预约（接收ID、isbn）
def userCancelReserve(data):
    rid = data["ID"]
    isbn = data["isbn"]
    sql = """
    DELETE FROM reserve
    WHERE reader_id = %s AND isbn = %s
    """
    with UsingMysql() as um:
        um.cursor.execute(sql, (rid, isbn))

    with UsingMysql() as um:
        um.cursor.execute("select * from book")
        datas = um.cursor.fetchall()
        print(datas)
    return


# ----------------------------------------------------------------------------------------------没做完
# 传输管理员书目信息（最大页数、name、author、publisher、isbn、time、num、transactor + 是否预约）
def adminCatelogs(data):
    page = data["pageNum"]
    row1 = (page - 1) * 7 + 1
    row2 = page * 7
    row = 0

    with UsingMysql() as um:
        # 查询图书信息
        um.cursor.execute("SELECT * FROM cip")
        datas = um.cursor.fetchall()

        # 查询每本书在流通室的可借复本数量
        num_by_isbn = {}
        for data in datas:
            isbn = data["isbn"]
            um.cursor.execute(
                "SELECT COUNT(*) as num FROM book WHERE isbn = %s", (isbn,))
            result = um.cursor.fetchone()
            num_by_isbn[isbn] = result["num"]

        # 构建返回结果
        books = [{"max": int((len(datas) - 1) / 7 + 1)}]  # 最大页数为查询结果的数量
        for data in datas:
            row = row + 1
            isbn = data["isbn"]

            book_info = {
                "name": data["title"],
                "author": data["author"],
                "publisher": data["publisher"],
                "isbn": isbn,
                "time": data["publish_date"],
                "num": num_by_isbn.get(isbn, 0),
                "transactor": data["librarian_id"],
                "reserved": "0",
            }
            if row >= row1 and row <= row2:
                books.append(book_info)

    # 使用自定义的JSONEncoder来处理日期类型的序列化
    return json.dumps(books, cls=CustomEncoder, ensure_ascii=False)


# 传输管理员信息（接收ID，传出ID、name）
# info = {"ID": "54321", "name": "无极至上天尊"}
def adminInfo(data):
    lid = data["ID"]
    with UsingMysql() as um:
        um.cursor.execute("select * from librarian where librarian_id=%s", lid)
        datas = um.cursor.fetchone()
        info = {
            "ID": datas["librarian_id"],
            "name": datas["name"],
        }
    return json.dumps(info, ensure_ascii=False)


# 传输图书信息（最大页数 + name、author、publisher、isbn、time、ddl）
# infos= [{"max": 5},
# {"ID": "1", "name": "计组","isbn": 1234, "place": "图书流通室", "state": "已借出", "transactor":1},
def adminDetail(data):
    page = data["pageNum"]
    row1 = (page - 1) * 7 + 1
    row2 = page * 7
    row = 0
    status_mapping = {
        -1: "不外借",
        0: "未借出",
        1: "已借出",
    }
    with UsingMysql() as um:
        um.cursor.execute("select * from book,cip where book.isbn = cip.isbn")
        datas = um.cursor.fetchall()
        # 构建预约信息列表
        infos = [{"max": int((len(datas) - 1) / 7 + 1)}]  # 最大页数为查询结果的数量
        for data in datas:
            row = row + 1
            # 计算预约截止日期
            info = {
                "ID": data["book_id"],
                "name": data["title"],
                "isbn": data["isbn"],
                "place": data["location"],
                "state": status_mapping[data["status"]],
                "transactor": data["librarian_id"]
            }
            if row >= row1 and row <= row2:
                infos.append(info)
    return json.dumps(infos, ensure_ascii=False)


# 传输借书信息（最大页数 + name、author、publisher、isbn、time、ddl）
# sends = [{"max": 4},
#          {"name": "数据结构", "author": "王作者", "publisher": "清华", "isbn": 1234, "time": "2023.3.4", "num": 0,"transactor":1},
def adminSends(data):
    page = data["pageNum"]
    row1 = (page - 1) * 7 + 1
    row2 = page * 7
    row = 0
    with UsingMysql() as um:
        # 查询图书信息
        um.cursor.execute("SELECT * FROM cip")
        datas = um.cursor.fetchall()

        # 查询每本书在流通室的可借复本数量
        num_by_isbn = {}
        for data in datas:
            isbn = data["isbn"]
            um.cursor.execute(
                "SELECT COUNT(*) as num FROM book WHERE isbn = %s AND location = '图书流通室' AND status = 0", (isbn,))
            result = um.cursor.fetchone()
            num_by_isbn[isbn] = result["num"]

        # 构建返回结果
        books = [{"max": int((len(datas) - 1) / 7 + 1)}]  # 最大页数为查询结果的数量
        for data in datas:
            row = row + 1
            isbn = data["isbn"]
            book_info = {
                "name": data["title"],
                "author": data["author"],
                "publisher": data["publisher"],
                "isbn": isbn,
                "time": data["publish_date"],
                "num": num_by_isbn.get(isbn, 0),
                "transactor": data["librarian_id"],
            }
            if row >= row1 and row <= row2:
                books.append(book_info)

    # 使用自定义的JSONEncoder来处理日期类型的序列化
    return json.dumps(books, cls=CustomEncoder, ensure_ascii=False)

 #传输还书信息（最大页数 + ID、name、isbn、time、ddl、penalty、returned）
def adminReturns(data,current_date):
    page = data["pageNum"]
    # 传进来的页码
    row1 = (page - 1) * 7 + 1
    row2 = page * 7
    row = 0
    with UsingMysql() as um:
        # 查询图书信息
        select_borrow_sql = '''
                    SELECT reader_id,title,book.isbn,borrow_date,due_date,return_date,borrow.librarian_id,
                    DATEDIFF(%s,due_date) AS 'date_diff'
                    FROM borrow,book,cip
                    WHERE borrow.book_id=book.book_id and book.isbn=cip.isbn
        '''
        um.cursor.execute(select_borrow_sql,(current_date,))
        datas = um.cursor.fetchall()

        # 构建返回结果
        books = [{"max": int((len(datas) - 1) / 7 + 1)}]  # 最大页数为查询结果的数量
        for data in datas:
            row = row + 1
            if row >= row1 and row <= row2:
                penalty = 0
                if data['return_date'] is None:
                    if data["date_diff"] > 0:
                        penalty = data["date_diff"] * penalty_per_day
                else:
                    penalty = penalty_per_day * (data['return_date'] - data['borrow_date']).days

                book_info = {
                    "ID": data["reader_id"],
                    "name": data["title"],
                    "isbn": data['isbn'],
                    "time": data["borrow_date"],
                    "ddl": data["due_date"],
                    "penalty": round(penalty,4),
                    "returned": 0 if data['return_date'] is None else 1,
                }
                books.append(book_info)

    # 使用自定义的JSONEncoder来处理日期类型的序列化
    return json.dumps(books, cls=CustomEncoder, ensure_ascii=False)

# 增加书目（接收name、author、publisher、isbn、time、transactor）
# {'name': '操作系统', 'author': '陈乔乔', 'publisher': '上海大学出版社', 'isbn': '978-3-16-55556-5', 'time': '2024-01-06', 'transactor': 1}
def addCatalog(data):
    isbn = data["isbn"]
    title = data["name"]
    author = data["author"]
    publisher = data["publisher"]
    publish_date_str = data["time"]
    copies = 0
    librarian_id = data["transactor"]

    # 检查是否存在相同的 ISBN 号
    with UsingMysql() as um:
        check_sql = "SELECT COUNT(*) as count FROM cip WHERE isbn = %s"
        um.cursor.execute(check_sql, (isbn,))
        result = um.cursor.fetchone()

    if result["count"] > 0:
        return "ISBN号已存在"
    else:
        # 检查日期是否合法
        try:
            publish_date = datetime.datetime.strptime(publish_date_str, '%Y-%m-%d').date()
        except ValueError:
            return "日期非法"
        # 在数据库中插入新的书目信息
        with UsingMysql() as um:
            insert_sql = """
            INSERT INTO cip (isbn, title, author, publisher, publish_date, copies, librarian_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            um.cursor.execute(insert_sql, (isbn, title, author, publisher, publish_date, copies, librarian_id))
            return "1"


# 删除书目（接收isbn）
# {'name': '操作系统二', 'author': '陈乔乔', 'publisher': '上海大学出版社', 'isbn': '978-7-30-222223-6', 'time': '2024-01-06', 'num': 0, 'transactor': 1, 'reserved': '0'}
def delCatalog(data):
    isbn = data["isbn"]
    # 在数据库中删除指定的书目信息
    with UsingMysql() as um:
        # 检查是否存在指定的 ISBN 号
        check_cip_sql = "SELECT COUNT(*) as count FROM cip WHERE isbn = %s"
        um.cursor.execute(check_cip_sql, (isbn,))
        result = um.cursor.fetchone()

        # 检查borrow表中是否有此isbn
        check_borrow_sql = "SELECT COUNT(*) as count FROM borrow, book WHERE isbn = %s"
        um.cursor.execute(check_borrow_sql, (isbn,))
        borrowed = um.cursor.fetchone()
        if borrowed["count"] > 0:
            return "此isbn还存在图书未归还,无法删除"

        if result["count"] > 0:
            # 如果存在，则执行删除操作
            del_sql = "DELETE FROM cip WHERE isbn = %s"
            um.cursor.execute(del_sql, (isbn,))
            # delete all books on this isbn
            del_book_sql = "DELETE FROM book WHERE isbn =%s"
            um.cursor.execute(del_book_sql, (isbn,))

            check_borrow_sql = "SELECT email FROM reserve, reader WHERE isbn = %s"
            um.cursor.execute(check_borrow_sql, (isbn,))
            emails = um.cursor.fetchall()
            if len(emails) > 0:
                # 发送邮件
                sender = EmailSender()
                reciever_list = [item['email'] for item in emails]
                sender.send(reciever_list, "预约提示",
                            "亲爱的读者\n  抱歉，您预约的书目已从库存中删除，具体信息请登陆查看。")

            return "1"  # 成功删除
        else:
            return "ISBN号不存在"


# 修改书目（接收name、author、publisher、old_isbn、isbn、time、transactor）
# {'name': '操作系统', 'author': '陈乔乔', 'publisher': '上海大学出版社', 'isbn': '978-7-30-222222-6', 'time': '2024-01-06', 'transactor': '1', 'old_isbn': '978-7-30-222222-6'}
def modCatalog(data):
    old_isbn = data["old_isbn"]
    new_isbn = data["isbn"]
    # 在数据库中删除指定的书目信息
    with UsingMysql() as um:
        # 检查是否存在指定的 ISBN 号
        check_cip_sql = "SELECT COUNT(*) as count FROM cip WHERE isbn = %s"
        um.cursor.execute(check_cip_sql, (old_isbn,))
        result = um.cursor.fetchone()
        if not check_transactor(data['transactor']):    # 检查librarian_id是否存在
            return "经办人不存在!"

        # 检查日期合法
        if not check_date_format(data['time']):
            return '日期不合法！'

        if result["count"] > 0:
            # update cip, cascade all foreign key
            set_sql = "UPDATE cip SET isbn = %s,title= %s,author= %s,publisher= %s,publish_date= %s,librarian_id= %s WHERE isbn = %s"
            um.cursor.execute(set_sql, (
            new_isbn, data['name'], data['author'], data['publisher'], data['time'], data['transactor'], old_isbn))

            check_borrow_sql = "SELECT email FROM reserve, reader WHERE reserve.reader_id=reader.reader_id and isbn = %s"
            um.cursor.execute(check_borrow_sql, (new_isbn,))
            emails = list(um.cursor.fetchall())

            check_borrow_sql = "SELECT email FROM borrow,book,reader WHERE borrow.reader_id=reader.reader_id and  borrow.book_id=book.book_id and isbn = %s"
            um.cursor.execute(check_borrow_sql, (new_isbn,))
            borrow_emails = um.cursor.fetchall()
            emails.extend(list(borrow_emails))

            if len(emails) > 0:
                # 发送邮件
                sender = EmailSender()
                reciever_list = [item['email'] for item in emails]
                sender.send(reciever_list, "预约提示",
                            "亲爱的读者：\n  您预约/借阅的书目isbn号已被修改，具体信息请登陆查看。")

            return "1"  # 成功删除
        else:
            return "ISBN号不存在"


# 增加图书（接收isbn、place、state、transactor）
# 正确返回“1”，错误返回错误信息(ISBN号已存在、经办人不存在)
# {'isbn': '978-7-30-333333-6', 'place': '图书流通室', 'transactor': 1}
def addInfo(data):
    isbn = data["isbn"]
    place = data["place"]
    transactor = data["transactor"]

    # 根据 place 的值初始化 state
    if place == '图书阅览室':
        state = -1
    else:
        state = 0
    if not check_transactor(transactor):  # 检查librarian_id是否存在
        return ("经办人不存在!")
    # 检查是否存在相同的 ISBN 号
    with UsingMysql() as um:
        check_sql = "SELECT COUNT(*) as count FROM cip WHERE isbn = %s"
        um.cursor.execute(check_sql, (isbn,))
        result = um.cursor.fetchone()

        if result["count"] == 0:
            return "ISBN不存在"

        # 获取当前数据库中记录的数量，用于生成新的 book_id
        get_count_sql = "SELECT COUNT(*) as count FROM book"
        um.cursor.execute(get_count_sql)
        count_result = um.cursor.fetchone()
        count = count_result["count"] + 1  # 记录数量加1

        while True:
            # 生成新的 book_id
            book_id = f'B{str(count).zfill(3)}'  # 使用 zfill() 填充零，保持四位数码

            # 检查生成的 book_id 是否已存在
            check_book_id_sql = "SELECT COUNT(*) as count FROM book WHERE book_id = %s"
            um.cursor.execute(check_book_id_sql, (book_id,))
            book_id_result = um.cursor.fetchone()

            if book_id_result["count"] == 0:
                break  # 如果不存在，退出循环
            else:
                count += 1  # 如果存在，增加计数，继续生成新的 book_id

        # 在数据库中插入新的图书记录
        insert_sql = """
        INSERT INTO book (book_id, isbn, location, status, librarian_id)
        VALUES (%s, %s, %s, %s, %s)
        """
        um.cursor.execute(insert_sql, (book_id, isbn, place, state, transactor))

        # 更新 cip 表中对应的 isbn 记录的 copies 字段
        update_cip_sql = "UPDATE cip SET copies = copies + 1 WHERE isbn = %s"
        um.cursor.execute(update_cip_sql, (isbn,))

        return "1"


# 删除图书（接收ID）
# {'ID': 'B44', 'name': '操作系统二', 'isbn': '978-7-30-222223-6', 'place': '图书流通室', 'state': '不外借', 'transactor': 1}
def delInfo(data):
    bid = data["ID"]
    # 在数据库中删除指定的书目信息
    with UsingMysql() as um:
        # 检查是否存在指定的 ISBN 号
        check_sql = "SELECT COUNT(*) as count FROM book WHERE book_id = %s"
        um.cursor.execute(check_sql, (bid,))
        result = um.cursor.fetchone()

        if result["count"] > 0:
            um.cursor.execute("SELECT isbn FROM book WHERE book_id = %s", (bid,))
            isbn = um.cursor.fetchone()['isbn']
            # 如果存在，则执行删除操作
            del_sql = "DELETE FROM book WHERE book_id = %s"
            um.cursor.execute(del_sql, (bid,))

            # 更新 cip 表中对应的 isbn 记录的 copies 字段
            update_cip_sql = "UPDATE cip SET copies = copies - 1 WHERE isbn = %s"
            um.cursor.execute(update_cip_sql, (isbn,))

            return "1"  # 成功删除
        else:
            return "BOOK_ID号不存在"


# 修改图书（接收ID、isbn、place、transactor）
# {'ID': 'B045', 'name': '操作系统二', 'isbn': '978-7-30-222223-6', 'place': '图书阅览室', 'transactor': '1'}
def modInfo(data):
    id = data["ID"]
    new_isbn = data["isbn"]
    # 在数据库中删除指定的书目信息
    with UsingMysql() as um:
        # 检查是否存在指定的 book_id 号
        check_book_sql = "SELECT COUNT(*) as count FROM book WHERE book_id = %s"
        um.cursor.execute(check_book_sql, (id,))
        result = um.cursor.fetchone()
        if not check_transactor(data['transactor']):    # 检查librarian_id是否存在
            return "经办人不存在!"

        # 检查是否存在指定的isbn
        check_book_sql = "SELECT 1 FROM cip WHERE isbn = %s"
        um.cursor.execute(check_book_sql, (new_isbn,))
        isbn_check = um.cursor.fetchone()
        if isbn_check is None:
            return "isbn不存在！"

        stat = -1
        if data['place']=="图书流通室":
            stat = 0
        if result["count"] > 0:
            # update cip, cascade all foreign key
            set_sql = "UPDATE book SET isbn = %s,location= %s,librarian_id= %s,status=%s WHERE book_id = %s"
            um.cursor.execute(set_sql, (new_isbn, data['place'], data['transactor'],stat, id))

            return "1"  # 成功删除
        else:
            return "book_id不存在"



# 借书（接收ID、isbn、name）、python（借书日期、到期日期、罚金） 一个读者只能借10本书
# {'name': '数据库系统概论', 'isbn': '978-3-16-148410-0', 'ID': '1', 'admin_ID': 1}
def sendBook(data):
    name = data["name"]
    isbn = data["isbn"]
    rid = data["ID"]
    lid = data["admin_ID"]
    borrow_date = datetime.datetime.now().strftime('%Y-%m-%d')
    length = 60  # 借书的最大天数
    due_date = (datetime.datetime.now() + datetime.timedelta(days=length)).strftime('%Y-%m-%d')

    with UsingMysql() as um:
        # 检查读者id
        check_reader_sql = "SELECT 1 FROM reader WHERE reader_id = %s"
        um.cursor.execute(check_reader_sql, (rid,))
        reader_check = um.cursor.fetchone()
        if reader_check is None:
            return "读者id不存在！"

        # 检查该读者的借书记录数量是否已经达到10本
        check_borrow_count_sql = "SELECT COUNT(*) as count FROM borrow WHERE reader_id = %s"
        um.cursor.execute(check_borrow_count_sql, (rid,))
        borrow_count_result = um.cursor.fetchone()
        borrow_count = borrow_count_result["count"]
        if borrow_count >= 10:
            return "借书过多，每位读者最多借阅10本书"

        reader_sql = "SELECT 1 FROM reader WHERE reader_id = %s"
        um.cursor.execute(check_borrow_count_sql, (rid,))
        reader_result = um.cursor.fetchone()
        if reader_result is None:
            return "读者号不存在"

        # 从图书表中获取给定ISBN的第一本书的book_id
        get_book_id_sql = "SELECT book_id FROM book WHERE isbn = %s and location = '图书流通室' and status = 0 LIMIT 1"
        um.cursor.execute(get_book_id_sql, (isbn,))
        result = um.cursor.fetchone()

        if result is not None:
            book_id = result["book_id"]

            # 在借书表中插入新的记录
            insert_borrow_sql = """
            INSERT INTO borrow (reader_id, librarian_id, book_id, borrow_date, due_date)
            VALUES (%s, %s, %s, %s, %s)
            """
            um.cursor.execute(insert_borrow_sql, (rid, lid, book_id, borrow_date, due_date))

            # 更新图书表中对应的 book_id 记录的 status 字段
            update_book_status_sql = "UPDATE book SET status = 1 WHERE book_id = %s"
            um.cursor.execute(update_book_status_sql, (book_id,))

            # 如果存在预约，则删除预约表信息
            reserve_del = 'DELETE FROM reserve WHERE reader_id = %s AND isbn = %s'
            um.cursor.execute(reserve_del, (rid, isbn))

            return "1"  # 借书成功
        else:
            return "该ISBN号的图书不存在或者无法借出"  # 在图书表中找不到ISBN

# 还书（接收ID、name、isbn、time、ddl、penalty、returned）
# 返回penalty，错误返回错误信息(读者ID不存在)
def returnBook(data, current_date):
    with UsingMysql() as um:
        # 检查该读者此书的借书情况
        check_borrow_sql = '''SELECT borrow.book_id,DATEDIFF(%s,borrow.due_date) AS 'date_diff' 
                    FROM borrow,book,cip
                    WHERE borrow.book_id=book.book_id and book.isbn=cip.isbn
                    and borrow.borrow_date=%s and reader_id=%s and title=%s 
                    and book.isbn=%s and return_date is null
       '''

        um.cursor.execute(check_borrow_sql, (current_date,data["time"],data["ID"],data["name"],data["isbn"]))
        borrow_result = um.cursor.fetchone()

        if len(borrow_result) == 0:
            return "此借阅信息不存在"
        # 还书
        return_book = '''UPDATE borrow SET return_date=%s
                    WHERE borrow.book_id=%s and borrow.borrow_date=%s 
                    and reader_id=%s and return_date is null
       '''
        um.cursor.execute(return_book, (current_date, borrow_result["book_id"],data["time"],data["ID"]))

        # 更新图书表中对应的 book_id 记录的 status 字段
        update_book_status_sql = "UPDATE book SET status = 0 WHERE book_id = %s"
        um.cursor.execute(update_book_status_sql, (borrow_result["book_id"],))

        #通知预约的读者
        reserve_list = '''SELECT reserve.reader_id, email FROM reserve,reader 
                            WHERE email_sended =0 and reserve.reader_id=reader.reader_id 
                            and isbn=%s'''
        um.cursor.execute(reserve_list,(data["isbn"],))
        reserve_list = um.cursor.fetchall()
        if len(reserve_list) > 0:
            # 发送邮件
            sender = EmailSender()
            email = [item['email'] for item in reserve_list]
            sender.send(email, "预约提示",
                        "亲爱的读者\n  您预约的《{}》 书目已经可以借阅，具体信息请登陆查看。".format(data["name"]))
        # 更新email_sended，保证只发送1次邮件
        update_sql = '''UPDATE reserve SET email_sended = 1 
                        where isbn =%s'''
        um.cursor.execute(update_sql,(data["isbn"],))

        book_info = {
                "penalty": borrow_result["date_diff"]*penalty_per_day if borrow_result["date_diff"]>0 else 0,
            }

    return json.dumps(book_info, cls=CustomEncoder, ensure_ascii=False)

# 管理员书目信息检索（最大页数 + name、author、publisher、isbn、time、num、transactor + 是否预约）
# sbooks = [{"max": 3},{"name": "数据结构", "author": "王作者", "publisher": "清华", "isbn": 1234, "time": "2023.1.1", "num": 0,"transactor":1, "reserved": "1"}]
def searchAdminCatelog(data):
    name = data["name"]
    page = data["pageNum"]
    row1 = (page - 1) * 7 + 1
    row2 = page * 7
    row = 0
    with UsingMysql() as um:
        # 查询图书信息
        um.cursor.execute("SELECT * FROM cip WHERE title LIKE %s", ('%' + name + '%',))
        datas = um.cursor.fetchall()

        # 查询每本书在流通室的可借复本数量
        num_by_isbn = {}
        for data in datas:
            isbn = data["isbn"]
            um.cursor.execute(
                "SELECT COUNT(*) as num FROM book WHERE isbn = %s", (isbn,))
            result = um.cursor.fetchone()
            num_by_isbn[isbn] = result["num"]

        # 构建返回结果
        books = [{"max": int((len(datas) - 1) / 7 + 1)}]  # 最大页数为查询结果的数量
        for data in datas:
            row = row + 1
            isbn = data["isbn"]

            book_info = {
                "name": data["title"],
                "author": data["author"],
                "publisher": data["publisher"],
                "isbn": isbn,
                "time": data["publish_date"],
                "num": num_by_isbn.get(isbn, 0),
                "transactor": data["librarian_id"],
                "reserved": "0",
            }
            if row >= row1 and row <= row2:
                books.append(book_info)

    # 使用自定义的JSONEncoder来处理日期类型的序列化
    return json.dumps(books, cls=CustomEncoder, ensure_ascii=False)


# 管理员图书信息检索（最大页数 + ID、name、isbn、place、state、transactor）
# {"ID": "3", "name": "无敌", "isbn": "1dd34", "place": "图书阅览室", "state": "不外借", "transactor": 4}
def searchAdminInfo(data):
    name = data["name"]
    page = data["pageNum"]
    row1 = (page - 1) * 7 + 1
    row2 = page * 7
    row = 0
    status_mapping = {
        -1: "不外借",
        0: "未借出",
        1: "已借出",
    }
    with UsingMysql() as um:
        um.cursor.execute("select * from book,cip where book.isbn = cip.isbn and title LIKE %s and status=0", ('%' + name + '%',))
        datas = um.cursor.fetchall()
        # 构建预约信息列表
        infos = [{"max": int((len(datas) - 1) / 7 + 1)}]  # 最大页数为查询结果的数量
        for data in datas:
            row = row + 1
            # 计算预约截止日期
            info = {
                "ID": data["book_id"],
                "name": data["title"],
                "isbn": data["isbn"],
                "place": data["location"],
                "state": status_mapping[data["status"]],
                "transactor": data["librarian_id"]
            }
            if row >= row1 and row <= row2:
                infos.append(info)
    return json.dumps(infos, ensure_ascii=False)


# 管理员借书信息检索（最大页数 + name、author、publisher、isbn、time、num、transactor）
def searchAdminSend(data):
    # name = data["name"]
    # page = data["pageNum"]
    # row1 = (page - 1) * 7 + 1
    # row2 = page * 7
    # row = 0
    # with UsingMysql() as um:
    #     # 查询图书信息
    #     um.cursor.execute("SELECT * FROM book,cip where book.isbn=cip.isbn and title LIKE %s and status = 0 ", ('%' + name + '%',))
    #     datas = um.cursor.fetchall()
    name = data["name"]
    page = data["pageNum"]
    row1 = (page - 1) * 7 + 1
    row2 = page * 7
    row = 0
    with UsingMysql() as um:
        # 查询图书信息
        um.cursor.execute("SELECT * FROM cip where title like %s",('%' + name + '%'))
        datas = um.cursor.fetchall()

        # 查询每本书在流通室的可借复本数量
        num_by_isbn = {}
        for data in datas:
            isbn = data["isbn"]
            um.cursor.execute(
                "SELECT COUNT(*) as num FROM book WHERE isbn = %s AND location = '图书流通室' AND status = 0",
                (isbn,))
            result = um.cursor.fetchone()
            num_by_isbn[isbn] = result["num"]

        # 构建返回结果
        books = [{"max": int((len(datas) - 1) / 7 + 1)}]  # 最大页数为查询结果的数量
        for data in datas:
            row = row + 1
            isbn = data["isbn"]
            book_info = {
                "name": data["title"],
                "author": data["author"],
                "publisher": data["publisher"],
                "isbn": isbn,
                "time": data["publish_date"],
                "num": num_by_isbn.get(isbn, 0),
                "transactor": data["librarian_id"],
            }
            if row >= row1 and row <= row2:
                books.append(book_info)

    # 使用自定义的JSONEncoder来处理日期类型的序列化
    return json.dumps(books, cls=CustomEncoder, ensure_ascii=False)

#管理员还书信息检索（最大页数 + name、author、publisher、isbn、time、num、transactor）
# {"max": 1},{"ID": "3", "name": "操作系统", "isbn": 5678, "time": "2022.1.1", "ddl": "2022.3.1", "penalty": 0,"returned": 0}]
def searchAdminReturn(data,current_date):
    id = data["name"]
    page = data["pageNum"]
    row1 = (page - 1) * 7 + 1
    row2 = page * 7
    row = 0
    with UsingMysql() as um:
        # 查询借书信息
        search_borrow = '''
                    SELECT reader_id,title,book.isbn,borrow_date,due_date,return_date,
                    DATEDIFF(%s,due_date) AS 'date_diff'
                    FROM borrow,book,cip
                    WHERE borrow.book_id=book.book_id and book.isbn=cip.isbn 
                    and reader_id LIKE %s
        '''
        um.cursor.execute(search_borrow,(current_date, '%' + id + '%',))
        datas = um.cursor.fetchall()
        # 构建返回结果
        books = [{"max": int((len(datas) - 1) / 7 + 1)}]  # 最大页数为查询结果的数量
        for data in datas:
            row = row + 1
            if row >= row1 and row <= row2:
                penalty = 0
                if data['return_date'] is None:
                    if data["date_diff"] > 0:
                        penalty = data["date_diff"] * penalty_per_day
                else:
                    penalty = penalty_per_day * (data['return_date'] - data['borrow_date']).days

                book_info = {
                    "ID": data["reader_id"],
                    "name": data["title"],
                    "isbn": data['isbn'],
                    "time": data["borrow_date"],
                    "ddl": data["due_date"],
                    "penalty": round(penalty,4),
                    "returned": 0 if data['return_date'] is None else 1,
                }
                books.append(book_info)

        # 使用自定义的JSONEncoder来处理日期类型的序列化
    return json.dumps(books, cls=CustomEncoder, ensure_ascii=False)
