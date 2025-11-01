"""
微信公众平台API登录模块
基于 https://github.com/wechat-article/wechat-article-exporter 项目实现
提供二维码登录、token管理、cookie管理等功能
"""

import os
import time
import json
import base64
import requests
from typing import Optional, Dict, Any, Callable
from threading import Lock, Timer
from PIL import Image
import qrcode
from io import BytesIO
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WeChatAPI:
    """微信公众平台API登录类"""
    
    def __init__(self):
        self.base_url = "https://mp.weixin.qq.com"
        self.login_url = f"{self.base_url}/"
        self.home_url = f"{self.base_url}/cgi-bin/home"
        
        # 状态管理
        self.is_logged_in = False
        self.session = requests.Session()
        self.token = None
        self.cookies = {}
        self.qr_code_path = "static/wx_qrcode.png"
        
        # 线程安全
        self._lock = Lock()
        
        # 回调函数
        self.login_callback = None
        self.notice_callback = None
        
        # 确保静态目录存在
        self.qr_code_path = os.path.abspath("static/wx_qrcode.png")
        os.makedirs(os.path.dirname(self.qr_code_path), exist_ok=True)
        
        # 设置请求头
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://mp.weixin.qq.com/'
        })

    def get_qr_code(self, callback: Optional[Callable] = None, notice: Optional[Callable] = None) -> Dict[str, Any]:
        """
        获取登录二维码
        
        Args:
            callback: 登录成功后的回调函数
            notice: 通知回调函数
            
        Returns:
            包含二维码信息的字典
        """
        with self._lock:
            self.login_callback = callback
            self.notice_callback = notice
            
            try:
                # 获取登录页面
                response = self.session.get(self.login_url)
                response.raise_for_status()
                
                # 解析页面获取二维码相关信息
                qr_info = self._extract_qr_info(response.text)
                
                if qr_info:
                    # 生成二维码图片
                    self._generate_qr_image(qr_info['qr_url'])
                    
                    # 启动登录状态检查
                    self._start_login_check(qr_info['uuid'])
                    
                    return {
                        'code': f"{self.qr_code_path}?t={int(time.time())}",
                        'is_exists': os.path.exists(self.qr_code_path),
                        'uuid': qr_info['uuid'],
                        'msg': '请使用微信扫描二维码登录'
                    }
                else:
                    return {
                        'code': None,
                        'is_exists': False,
                        'msg': '获取二维码失败'
                    }
                    
            except Exception as e:
                logger.error(f"获取二维码失败: {str(e)}")
                return {
                    'code': None,
                    'is_exists': False,
                    'msg': f'获取二维码失败: {str(e)}'
                }

    def _extract_qr_info(self, html_content: str) -> Optional[Dict[str, str]]:
        """
        从HTML内容中提取二维码信息
        
        Args:
            html_content: 登录页面HTML内容
            
        Returns:
            包含二维码URL和UUID的字典
        """
        try:
            # 使用更灵活的正则表达式匹配二维码URL和UUID
            import re
            
            # 查找二维码URL
            qr_pattern = r'(https?:\/\/mp\.weixin\.qq\.com\/cgi-bin\/loginqrcode\?action=getqrcode&param=\d+)'
            qr_match = re.search(qr_pattern, html_content)
            
            # 查找UUID
            uuid_pattern = r'(?:"|\')uuid(?:"|\')\s*:\s*(?:"|\')([^"\']+)(?:"|\')'
            uuid_match = re.search(uuid_pattern, html_content)
            
            if qr_match and uuid_match:
                return {
                    'qr_url': qr_match.group(1),
                    'uuid': uuid_match.group(1)
                }
            
            # 如果没有找到，尝试其他方式获取
            return self._get_qr_info_api()
            
        except Exception as e:
            logger.error(f"解析二维码信息失败: {str(e)}")
            return None

    def _get_qr_info_api(self) -> Optional[Dict[str, str]]:
        """
        通过API获取二维码信息
        
        Returns:
            包含二维码URL和UUID的字典
        """
        try:
            # 首先访问登录页面，模拟浏览器打开行为
            logger.info("模拟浏览器访问登录页面...")
            login_response = self.session.get(self.login_url)
            login_response.raise_for_status()
            session = self.session
            # 设置更完整的浏览器请求头
            browser_headers = {
                'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Sec-Fetch-Dest': 'image',
                'Sec-Fetch-Mode': 'no-cors',
                'Sec-Fetch-Site': 'same-origin',
                "Sec-Fetch-Mode": "navigate",
                "Upgrade-Insecure-Requests": "1",
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': self.login_url
            }
            
            # 更新session请求头
            session.headers.update(browser_headers)
            
            # 启动登录流程获取UUID
            uuid = self.start_login()
            if not uuid:
                uuid = self._generate_uuid()
            
            # 构建二维码请求URL，模拟浏览器请求
            timestamp = int(time.time() * 1000)  # 使用毫秒时间戳
            qr_api_url = f"{self.base_url}/cgi-bin/scanloginqrcode?action=getqrcode&uuid={uuid}&random={timestamp}"
            

          
            
            logger.info(f"请求二维码: {qr_api_url}")
            logger.info(f"使用UUID: {uuid}")
            # 发送请求获取二维码
            response = session.get(qr_api_url,  allow_redirects=False)
            
            # 检查响应状态
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                
                # 检查是否返回图片
                if 'image/' in content_type:
                    # 验证图片数据有效性
                    try:
                        from PIL import Image
                        Image.open(BytesIO(response.content))
                        
                        # 保存二维码图片
                        with open(self.qr_code_path, 'wb') as f:
                            f.write(response.content)
                        
                        logger.info(f"二维码获取成功，已保存到: {self.qr_code_path}")
                        
                        return {
                            'qr_url': f"{qr_api_url}?",
                            'uuid': uuid
                        }
                        
                    except Exception as e:
                        logger.error(f"二维码图片数据无效: {str(e)}")
                        
                else:
                    logger.warning(f"响应不是图片格式: {content_type}")
                    logger.debug(f"响应内容: {response.text[:200]}...")
            
            elif response.status_code == 302:
                # 处理重定向
                redirect_url = response.headers.get('Location')
                logger.info(f"收到重定向: {redirect_url}")
                
                if redirect_url:
                    redirect_response = self.session.get(redirect_url)
                    if redirect_response.status_code == 200 and 'image/' in redirect_response.headers.get('Content-Type', ''):
                        with open(self.qr_code_path, 'wb') as f:
                            f.write(redirect_response.content)
                        
                        return {
                            'qr_url': redirect_url,
                            'uuid': uuid
                        }
            
            else:
                logger.error(f"请求失败: 状态码={response.status_code}")
                logger.debug(f"响应头: {dict(response.headers)}")
                logger.debug(f"响应内容: {response.text[:500]}...")
            
            
        except Exception as e:
            logger.error(f"API获取二维码失败: {str(e)}")
    #开始登录 
    def start_login(self):
        """
        启动登录流程
        """
        uuid=self._generate_uuid()
        self.session.cookies.set("uuid",uuid)
        url=f"{self.base_url}/cgi-bin/bizlogin?action=startlogin"
        fingerprint=self._generate_uuid()
        data={
            "fingerprint": fingerprint,
            "token": "1788989385",
            "lang": "zh_CN",
            "f": "json",
            "ajax": "1",
            "redirect_url": "/cgi-bin/settingpage?t=setting/index&amp;action=index&amp;token=1788989385&amp;lang=zh_CN",
            "login_type": "3",
        }
        response=self.session.post(url,data=data)
          # 从响应头或Cookie中获取UUID
        uuid = response.cookies.get('uuid') or response.headers.get('X-UUID') 
        return uuid
    
    def pre_login(self):
        """
        启动登录流程
        """
        uuid=self._generate_uuid()
        self.session.cookies.set("uuid",uuid)
        url=f"{self.base_url}/cgi-bin/bizlogin"
        params={
            "action": "prelogin",
            "fingerprint": self._generate_uuid(),
            "token": "",
            "lang": "zh_CN",
            "f": "json",
            "ajax": "1"
        }
        response=self.session.get(url,params=params)
          # 从响应头或Cookie中获取UUID
        uuid = response.cookies.get('uuid') or response.headers.get('X-UUID') 
        return uuid
        

    def _generate_uuid(self) -> str:
        """
        生成UUID
        
        Returns:
            UUID字符串
        """
        import uuid
        return str(uuid.uuid4())
    
    def _generate_qr_image(self, qr_url: str):
        """
        生成二维码图片
        
        Args:
            qr_url: 二维码URL
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.qr_code_path), exist_ok=True)
            
            # 如果是完整的URL，直接下载
            if qr_url.startswith('http'):
                response = self.session.get(qr_url)
                response.raise_for_status()
                
                with open(self.qr_code_path, 'wb') as f:
                    f.write(response.content)
            else:
                # 如果是数据，生成二维码
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(qr_url)
                qr.make(fit=True)
                
                img = qr.make_image(fill_color="black", back_color="white")
                
                # 确保图片格式正确
                if not self.qr_code_path.lower().endswith('.png'):
                    self.qr_code_path = os.path.splitext(self.qr_code_path)[0] + '.png'
                
                # 使用BytesIO临时保存图片，确保编码正确
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                
                # 写入文件
                with open(self.qr_code_path, 'wb') as f:
                    f.write(buffer.getvalue())
                
            logger.info(f"二维码已保存到: {self.qr_code_path}")
            
        except Exception as e:
            logger.error(f"生成二维码图片失败: {str(e)}")

    def _start_login_check(self, uuid: str):
        """
        启动登录状态检查
        
        Args:
            uuid: 二维码UUID
        """
        def check_login():
            try:
                # 检查登录状态
                status = self._check_login_status(uuid)
                
                if status == 'success':
                    self._handle_login_success()
                elif status == 'waiting':
                    # 继续等待
                    Timer(2.0, check_login).start()
                elif status == 'scanned':
                    # 已扫描，等待确认
                    if self.notice_callback:
                        self.notice_callback('已扫描，请在手机上确认登录')
                    Timer(2.0, check_login).start()
                elif status == 'expired':
                    # 二维码过期
                    if self.notice_callback:
                        self.notice_callback('二维码已过期，请重新获取')
                else:
                    # 继续检查
                    Timer(2.0, check_login).start()
                    
            except Exception as e:
                logger.error(f"检查登录状态失败: {str(e)}")
                Timer(5.0, check_login).start()  # 出错后延长检查间隔
        
        # 启动检查
        Timer(2.0, check_login).start()

    def _check_login_status(self, uuid: str) -> str:
        """
        检查登录状态
        
        Args:
            uuid: 二维码UUID
            
        Returns:
            登录状态: 'waiting', 'scanned', 'success', 'expired', 'error'
        """
        try:
            check_url=f"{self.base_url}/cgi-bin/scanloginqrcode"
            fingerprint=self.cookies.get("fingerprint")
            params = {
                "action": "ask",
                "fingerprint": fingerprint,
                "lang": "zh_CN",
                "f": "json",
                "ajax": 1
            }
            
            response = self.session.get(check_url, params=params)
            response.raise_for_status()
            
            # 解析响应
            if response.headers.get('content-type', '').startswith('application/json'):
                data = response.json()
                status = data.get('status', 0)
                print(data)
                if "invalid session" in str(data):
                    return 'invalid session'
                if status == 1:
                    self.cookies=dict(self.session.cookies)
                    return 'success'  # 登录成功
                elif status == 2:
                    return 'scanned'  # 已扫描
                elif status == 3:
                    return 'success'  # 登录成功
                elif status == 4:
                    return 'scanned'  # 已扫描，等待确认
                else:
                    return 'wait'  # 继续等待
                    
        except Exception as e:
            logger.error(f"检查登录状态失败: {str(e)}")
            return 'error'

    def _handle_login_success(self):
        """
        处理登录成功
        """
        try:
            with self._lock:
                self.is_logged_in = True
                
                # 获取token和cookies
                self._extract_login_info()
                
                # 清理二维码文件
                self._clean_qr_code()
                
                # 调用成功回调
                if self.login_callback:
                    login_data = {
                        'cookies': dict(self.session.cookies),
                        'cookies_str': self._format_cookies_string(),
                        'token': self.token,
                        'wx_login_url': self.qr_code_path,
                        'expiry': self._calculate_expiry()
                    }
                    self.login_callback(login_data, self._get_account_info())
                
                logger.info("登录成功！")
                
        except Exception as e:
            logger.error(f"处理登录成功失败: {str(e)}")

    def _extract_login_info(self):
        """
        提取登录信息（token和cookies）
        """
        try:
            # 访问首页获取token
            response = self.session.get(self.home_url)
            response.raise_for_status()
            
            # 从URL或页面内容中提取token
            import re
            token_match = re.search(r'token=([^&\s"\']+)', response.text)
            if token_match:
                self.token = token_match.group(1)
            
            # 更新cookies
            self.cookies = dict(self.session.cookies)
            
        except Exception as e:
            logger.error(f"提取登录信息失败: {str(e)}")

    def _format_cookies_string(self) -> str:
        """
        格式化cookies为字符串
        
        Returns:
            cookies字符串
        """
        return '; '.join([f"{k}={v}" for k, v in self.cookies.items()])

    def _calculate_expiry(self) -> Optional[float]:
        """
        计算cookies过期时间
        
        Returns:
            过期时间戳
        """
        try:
            # 查找有过期时间的cookie
            for cookie in self.session.cookies:
                if cookie.expires:
                    return cookie.expires
            
            # 如果没有找到，返回默认过期时间（24小时后）
            return time.time() + 24 * 3600
            
        except Exception as e:
            logger.error(f"计算过期时间失败: {str(e)}")
            return None

    def _get_account_info(self) -> Optional[Dict[str, Any]]:
        """
        获取账号信息
        
        Returns:
            账号信息字典
        """
        try:
            # 这里需要根据实际页面结构获取账号信息
            response = self.session.get(self.home_url)
            response.raise_for_status()
            
            # 解析账号信息（需要根据实际页面结构调整）
            account_info = {
                'wx_app_name': '公众号名称',
                'wx_logo': '',
                'wx_read_yesterday': '0',
                'wx_share_yesterday': '0',
                'wx_watch_yesterday': '0',
                'wx_yuan_count': '0',
                'wx_user_count': '0'
            }
            
            return account_info
            
        except Exception as e:
            logger.error(f"获取账号信息失败: {str(e)}")
            return None

    def _clean_qr_code(self):
        """
        清理二维码文件
        """
        try:
            if os.path.exists(self.qr_code_path):
                os.remove(self.qr_code_path)
        except Exception as e:
            logger.error(f"清理二维码文件失败: {str(e)}")

    def login_with_token(self, token: str, cookies: Optional[Dict[str, str]] = None) -> bool:
        """
        使用token登录
        
        Args:
            token: 登录token
            cookies: cookies字典
            
        Returns:
            是否登录成功
        """
        try:
            with self._lock:
                self.token = token
                
                if cookies:
                    self.session.cookies.update(cookies)
                    self.cookies = cookies
                
                # 验证登录状态
                response = self.session.get(f"{self.home_url}?token={token}")
                response.raise_for_status()
                
                if 'home' in response.url:
                    self.is_logged_in = True
                    logger.info("Token登录成功")
                    return True
                else:
                    logger.warning("Token登录失败")
                    return False
                    
        except Exception as e:
            logger.error(f"Token登录失败: {str(e)}")
            return False

    def logout(self):
        """
        登出
        """
        with self._lock:
            self.is_logged_in = False
            self.token = None
            self.cookies = {}
            self.session.cookies.clear()
            self._clean_qr_code()
            logger.info("已登出")

    def is_login_valid(self) -> bool:
        """
        检查登录是否有效
        
        Returns:
            登录是否有效
        """
        if not self.is_logged_in or not self.token:
            return False
        
        try:
            response = self.session.get(f"{self.home_url}?token={self.token}")
            return 'home' in response.url
        except:
            return False

    def get_session_info(self) -> Dict[str, Any]:
        """
        获取会话信息
        
        Returns:
            会话信息字典
        """
        return {
            'is_logged_in': self.is_logged_in,
            'token': self.token,
            'cookies': self.cookies,
            'cookies_str': self._format_cookies_string(),
            'expiry': self._calculate_expiry()
        }


# 创建全局实例
wechat_api = WeChatAPI()


def get_qr_code(callback: Optional[Callable] = None, notice: Optional[Callable] = None) -> Dict[str, Any]:
    """
    获取登录二维码（全局函数）
    
    Args:
        callback: 登录成功回调函数
        notice: 通知回调函数
        
    Returns:
        二维码信息字典
    """
    return wechat_api.get_qr_code(callback, notice)


def login_with_token(token: str, cookies: Optional[Dict[str, str]] = None) -> bool:
    """
    使用token登录（全局函数）
    
    Args:
        token: 登录token
        cookies: cookies字典
        
    Returns:
        是否登录成功
    """
    return wechat_api.login_with_token(token, cookies)


def get_session_info() -> Dict[str, Any]:
    """
    获取会话信息（全局函数）
    
    Returns:
        会话信息字典
    """
    return wechat_api.get_session_info()


def logout():
    """
    登出（全局函数）
    """
    wechat_api.logout()


if __name__ == "__main__":
    # 测试代码
    def login_success_callback(session_data, account_info):
        print("登录成功！")
        print(f"Token: {session_data.get('token')}")
        print(f"账号信息: {account_info}")
    
    def notice_callback(message):
        print(f"通知: {message}")
    
    # 获取二维码
    result = get_qr_code(login_success_callback, notice_callback)
    print(f"二维码结果: {result}")
    
    # 保持程序运行以等待登录
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("程序退出")
        logout()