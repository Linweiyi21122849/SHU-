import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class EmailSender:
    def __init__(self):
        self.smtp = smtplib.SMTP()

        # 连接邮箱服务器地址
        self.smtp.connect('smtp.qq.com')

        # 发件人地址及授权码
        self.email_from_username = 'library_10@foxmail.com'
        self.email_from_password = 'ezdbgperyekzdbhb'
        self.smtp.login(self.email_from_username, self.email_from_password)

    def generate_email_body(self, email_to_list, email_title, email_content):
        """
        组成邮件体
        :param email_to_list:收件人列表
        :param email_title:邮件标题
        :param email_content:邮件正文内容
        :return:
        """
        email_body = MIMEMultipart('mixed')
        email_body['Subject'] = email_title
        email_body['From'] = self.email_from_username
        email_body['To'] = ",".join(email_to_list)

        text_plain = MIMEText(email_content, 'plain', 'utf-8')
        email_body.attach(text_plain)
        return email_body

    def send(self,email_to_list, email_title, email_content):
        # 发送邮件
        email_body = self.generate_email_body(email_to_list, email_title,email_content)
        # 注意：此处必须同时指定发件人与收件人，否则会当作垃圾邮件处理掉
        self.smtp.sendmail(self.email_from_username, email_to_list, email_body.as_string())

    def exit(self):
        """
        退出服务
        :return:
        """
        self.smtp.quit()
