import socket 
import json
from threading import Thread
import time
import libraryTest as lt
from utils.system_run import System
from flask import Flask, render_template, request

# app = Flask("libraryServer", static_folder = "../../library/")
app = Flask("libraryServer", static_folder = "library/")
current_date = time.strftime('%Y-%m-%d', time.localtime())
#潜在问题
#当修改书目信息的时候，并没有对应的图书记录进行关联处理

@app.route("/<path>/<file>")     #发送CSS done
def sendCSS(path, file):          
    print(path + "/" + file)
    return app.send_static_file(path + "/" + file)

@app.route("/<file>")            #发送HTML done
def sendHTML(file):          
    print(file)
    return app.send_static_file(file)

#@app.route('/favicon.ico')
#def favicon():
#    return app.send_static_file('images/logo.png')

@app.route("/registerCheck0", methods = ['post'])     #注册界面
def registerCheck0():             #检查用户手机号、邮箱是否重复（phoneRepeat、mailRepeat）
    data = request.json
    print(data)
    ans = lt.registerCheck0(data)          
    return ans

@app.route("/sendVerCode", methods = ['post'])    #发送验证码
def sendVerCode():             
    data = request.json
    print(data)
    ans = lt.sendVerCode(data)
    return ans

@app.route("/registerCheck1", methods = ['post']) 
def registerCheck1():             #检查管理员工号是否重复（workNumRepeat）
    data = request.json
    print(data)
    ans = lt.registerCheck1(data)
    return ans

@app.route("/loginCheck0", methods = ['post'])    #用户登录界面 done
def loginCheck0():             
    data = request.json
    print(data)
    ans = lt.loginCheck0(data)
    return ans

@app.route("/loginCheck1", methods = ['post'])    #检查管理员账号是否正确（正确为1，否则0）done
def loginCheck1():             
    data = request.json
    print(data)
    ans = lt.loginCheck1(data)
    return ans

@app.route("/userCatelogInfo", methods = ['post'])    #传输用户书目信息（最大页数、name、author、publisher、isbn、time、num、transactor + 是否预约)
def userCatelogInfo():                                    #接收（ID、页号）
    data = request.json
    print(data)
    ans = lt.userCatelogs(data)
    return ans

@app.route("/userInfo", methods = ['post'])    #传输用户信息（接收phone，传出ID、name、phone、mail）done
def userInfo():                               
    data = request.json
    print(data)
    ans = lt.userInfo(data)
    return ans

@app.route("/userReserveInfo", methods = ['post'])    #传输用户预约信息（最大页数 + name、author、publisher、isbn、time、ddl）
def userReserveInfo():                               
    data = request.json
    print(data)
    ans = lt.userReserves(data)
    return ans

@app.route("/userReserve", methods = ['post'])    #用户预约（接收ID、isbn、当前时间python）done
def userReserve():                               
    data = request.json
    print(data)
    lt.userReserve(data)
    return '1'

@app.route("/cancelReserve", methods = ['post'])     #取消预约（接收ID、isbn）
def cancelReserve():                               
    data = request.json
    print(data)
    lt.userCancelReserve(data)
    return '1'

@app.route("/searchUserCatelog", methods = ['post'])  #用户书目信息检索（最大页数 + name、author、publisher、isbn、time、num、transactor + 是否预约）
def searchUserCatelog():                               
    data = request.json
    print(data)
    ans = lt.searchUserCatelog(data)  
    return ans

@app.route("/searchUserReserve", methods = ['post'])  #用户预约信息检索（最大页数 + name、author、publisher、isbn、time、ddl）
def searchUserReserve():                               
    data = request.json
    print(data)
    ans = lt.searchUserReserve(data)
    return ans

@app.route("/userSendInfo", methods = ['post'])  #传输用户借书信息（最大页数 + name、author、publisher、isbn、time、ddl）
def userSendInfo():                               
    data = request.json
    print(data)
    ans = lt.userSends(data)  
    return ans

@app.route("/searchUserSend", methods = ['post'])  #用户借书信息检索（最大页数 + name、author、publisher、isbn、time、ddl）
def searchUserSend():                               
    data = request.json
    print(data)
    ans = lt.searchUserSend(data)     
    return ans

@app.route("/adminInfo", methods = ['post'])    #传输管理员信息（接收ID，传出ID、name）
def adminInfo():                               
    data = request.json
    print(data)
    ans = lt.adminInfo(data)   
    return ans

@app.route("/adminCatelogInfo", methods = ['post'])  #传输管理员书目信息（最大页数、name、author、publisher、isbn、time、num、transactor）
def adminCatelogInfo():                                   
    data = request.json
    print(data)
    ans = lt.adminCatelogs(data)              
    return ans

@app.route("/adminDetail", methods = ['post'])     #传输图书信息（最大页数 + name、author、publisher、isbn、time、ddl）
def adminDetail():                                   
    data = request.json
    print(data)
    ans = lt.adminDetail(data)             
    return ans

@app.route("/adminSendInfo", methods = ['post'])   #传输借书信息（最大页数 + name、author、publisher、isbn、time、ddl）
def adminSendInfo():                                   
    data = request.json
    print(data)
    ans = lt.adminSends(data)               
    return ans

@app.route("/adminReturnInfo", methods = ['post'])  #传输还书信息（最大页数 + ID、name、isbn、time、ddl、penalty、returned）
def adminReturnInfo():                                   
    data = request.json
    print(data)
    ans = lt.adminReturns(data,current_date)               
    return ans

@app.route("/addCatelog", methods = ['post'])     #增加书目（接收name、author、publisher、isbn、time、transactor） 
def addCatelog():                                 #正确返回“1”，错误返回错误信息(ISBN号已存在)
    data = request.json
    print(data)
    ans = lt.addCatalog(data)               
    return ans

@app.route("/delCatelog", methods = ['post'])     #删除书目（接收isbn,同时会把同isbn的所有图书一起删除） 
def delCatelog():                                   
    data = request.json
    print(data)
    lt.delCatalog(data)    
    return '1'

@app.route("/modCatelog", methods = ['post'])     #修改书目（接收name、author、publisher、old_isbn、isbn、time、transactor） 
def modCatelog():                                 #正确返回“1”，错误返回错误信息(ISBN号不存在、日期格式不正确、经办人不存在)  
    data = request.json
    print(data)
    ans = lt.modCatalog(data)                          
    return ans

@app.route("/addInfo", methods = ['post'])     #增加图书（接收isbn、place、state、transactor） 
def addInfo():                                 #正确返回“1”，错误返回错误信息(ISBN号已存在、经办人不存在)  
    data = request.json
    print(data)
    ans = lt.addInfo(data)                                       
    return ans

@app.route("/delInfo", methods = ['post'])     #删除图书（接收ID） 
def delInfo():                                  
    data = request.json
    print(data)
    lt.delInfo(data)     
    return '1'
    
@app.route("/modInfo", methods = ['post'])     #修改图书（接收ID、isbn、place、transactor） 
def modInfo():                                 #正确返回“1”，错误返回错误信息(ISBN号不存在、经办人不存在)  
    data = request.json
    print(data)
    ans = lt.modInfo(data)                                                    
    return ans

@app.route("/sendBook", methods = ['post'])     #借书（接收ID、isbn、name）、python（借书日期、到期日期、罚金） 
def sendBook():                                 #正确返回“1”，错误返回错误信息(读者ID不存在)  
    data = request.json
    print(data)
    ans = lt.sendBook(data)                                                                       
    return ans

@app.route("/returnBook", methods = ['post'])     #还书（接收ID、name、isbn、time、ddl、penalty、returned） 
def returnBook():                                 #正确返回“1”，错误返回错误信息(读者ID不存在)  
    data = request.json
    print(data)
    ans = lt.returnBook(data, current_date)                                                                                          
    return ans

@app.route("/searchAdminCatelog", methods = ['post'])   #管理员书目信息检索（最大页数 + name、author、publisher、isbn、time、num、transactor） 
def searchAdminCatelog():                                   
    data = request.json
    print(data)
    ans = lt.searchAdminCatelog(data)                                                                                          
    return ans

@app.route("/searchAdminInfo", methods = ['post'])   #管理员图书信息检索（最大页数 + ID、name、isbn、place、state、transactor） 
def searchAdminInfo():                                   
    data = request.json
    print(data)
    ans = lt.searchAdminInfo(data)                                                                                          
    return ans

@app.route("/searchAdminSend", methods = ['post'])   #管理员借书信息检索（最大页数 + name、author、publisher、isbn、time、num、transactor） 
def searchAdminSend():                                   
    data = request.json
    print(data)
    ans = lt.searchAdminSend(data)    
    print(ans)
    return ans

@app.route("/searchAdminReturn", methods = ['post'])  #管理员还书信息检索（最大页数 + name、author、publisher、isbn、time、num、transactor） 
def searchAdminReturn():                                   
    data = request.json
    print(data)
    ans = lt.searchAdminReturn(data,current_date)                                                                                          
    return ans



if __name__=="__main__":
    host = "127.0.0.1"; port = 4444
    app.debug = True
    system_run = System(current_date, n=5)  # 间隔n秒运行一次后台检查
    system_run.start()
    app.run(host, port)
        


    
