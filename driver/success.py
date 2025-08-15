from .token import set_token
from core.print import print_warning
#判断是否是有效登录 

# 初始化全局变量
WX_LOGIN_ED = False
WX_LOGIN_INFO = None

import threading

# 初始化线程锁
login_lock = threading.Lock()

def setStatus(status:bool):
    global WX_LOGIN_ED
    with login_lock:
        WX_LOGIN_ED=status
def getStatus():
    global WX_LOGIN_ED
    with login_lock:
        return WX_LOGIN_ED
def getLoginInfo():
    global WX_LOGIN_INFO
    with login_lock:
        return WX_LOGIN_INFO
def setLoginInfo(info):
    global WX_LOGIN_INFO
    with login_lock:
        WX_LOGIN_INFO=info

def Success(data):
    if data != None:
            # print("\n登录结果:")
            setLoginInfo(data)
            setStatus(True)
            if data['expiry'] !=None:
                print(f"有效时间: {data['expiry']['expiry_time']} (剩余秒数: {data['expiry']['remaining_seconds']})")
                set_token(data)
            else:
                print_warning("登录失败，请检查上述错误信息")
                setStatus(False)

    else:
            print("\n登录失败，请检查上述错误信息")
            setStatus(False)