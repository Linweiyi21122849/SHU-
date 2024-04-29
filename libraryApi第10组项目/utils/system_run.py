import time
import threading
from utils.pymysql_comm import UsingMysql
from utils.email_sender import EmailSender

class System(threading.Thread):
    def __init__(self,current_date, n=5):
        self.n = n
        # 每隔n秒执行一次系统监测
        super().__init__()
        self.current_date = current_date
    def process_reserve(self):
        with UsingMysql() as um:
            # 通知超出预约期限的读者
            # check_reserve = "SELECT email FROM reserve, reader WHERE reserve.reader_id = reader.reader_id and date_add(reserve_date, interval reserve_period day)< current_date()"
            check_reserve = """SELECT email FROM reserve, reader 
                    WHERE reserve.reader_id = reader.reader_id 
                    and date_add(reserve_date, interval reserve_period day)< %s"""
            um.cursor.execute(check_reserve, (self.current_date,))
            emails = um.cursor.fetchall()
            if len(emails) > 0:
                # 发送邮件
                sender = EmailSender()
                reciever_list = [item['email'] for item in emails]
                sender.send(reciever_list, "预约提示",
                            "亲爱的读者\n  抱歉，您的预约已过期，具体信息请登陆查看。")

            # 删除过期预约/已借到
            # reserve_del = 'DELETE FROM reserve where date_add(reserve_date, interval reserve_period day)< current_date()'
            reserve_del = 'DELETE FROM reserve where date_add(reserve_date, interval reserve_period day)< %s'
            um.cursor.execute(reserve_del, (self.current_date,))
            # reserve_del = """DELETE FROM reserve WHERE
            #         isbn IN (SELECT isbn FROM borrow,book where
            #         return_date is null and borrow.reader_id=reserve.reader_id)"""
            # um.cursor.execute(reserve_del)

            # 通知预约读者有书可借
            reserve_list = '''SELECT reader_id, email FROM reader WHERE reader_id 
                                in (SELECT reader_id FROM reserve WHERE
                                email_sended =0 and
                                isbn in (SELECT DISTINCT book.isbn FROM book WHERE status=0))'''
            um.cursor.execute(reserve_list)
            emails = um.cursor.fetchall()
            if len(emails) > 0:
                # 发送邮件
                sender = EmailSender()
                reciever_list = [item['email'] for item in emails]
                sender.send(reciever_list, "预约提示",
                            "亲爱的读者\n  您预约的书目已经可以借阅，具体信息请登陆查看。")
            update_sql = '''UPDATE reserve SET email_sended = 1 
                            where isbn in (SELECT book.isbn FROM book WHERE status=0)'''
            um.cursor.execute(update_sql)
    def process_borrow(self):
        with UsingMysql() as um:
            # borrow_list = 'SELECT email FROM borrow, reader WHERE due_date < current_date()'
            # 对于已到期且未归还的图书，系统通过Email自动通知读者
            borrow_list = """SELECT email FROM borrow, reader 
                    WHERE borrow.reader_id=reader.reader_id and due_date < %s
                    and return_date is null 
                    """
            um.cursor.execute(borrow_list, (self.current_date,))
            emails = um.cursor.fetchall()
        if len(emails) > 0:
            # 发送邮件
            sender = EmailSender()
            reciever_list = [item['email'] for item in emails]
            sender.send(reciever_list, "借书超期提示",
                        "亲爱的读者\n  您借阅的书目已到期，请及时归还，否则会产生罚金。")
    def run(self) -> None:
        while True:
            self.process_reserve()
            self.process_borrow()
            time.sleep(self.n)