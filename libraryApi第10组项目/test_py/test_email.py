from utils.email_sender import EmailSender

sender = EmailSender()
list = ['christianlsl@foxmail.com']
sender.send(list,"预约提示","您预约的书目已被删除")