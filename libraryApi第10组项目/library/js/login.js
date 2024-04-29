export function checkError(){
    if(has_error.value == 1) return
    var error_id=ref('')
    if(user.value == ''){
        error_msg.value = "用户名不能为空"
        error_id.value = "user"
    }
    else if(pw.value == ''){
        error_msg.value = "密码不能为空"
        error_id.value = "password"
    }
    else if(confirm_pw.value == ''){
        error_msg.value = "请再次输入密码"
        error_id.value = "confirm_pw"
    }
    else if(phone.value == ''){
        error_msg.value = "手机号不能为空"
        error_id.value = "phone"
    }
    else if(mail.value == ''){
        error_msg.value = "邮箱不能为空"
        error_id.value = "mail"
    }
    else if(code.value == '' && mod == '0'){
        error_msg.value = "请输入验证码"
        error_id.value = "code"
    }
    if(error_id.value != ''){
        var ele = document.getElementById(error_id.value)
        ele.style.border = "2px solid red"
        has_error.value = 1;
        ele.onfocus = ()=>{
            // console.log("1234")
            has_error.value = 0;
            ele.style.border = "1px solid black";
            ele.onfocus=""
        }
    }
}