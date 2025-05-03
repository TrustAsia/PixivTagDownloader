"""
Pixiv Tag Downloader 应用程序的认证模块。
本模块负责处理Pixiv的认证，通过读取cookie文件并验证登录状态。
"""

import os
import re
import requests
from config import config

class PixivAuth:
    """
    使用cookies处理Pixiv认证。

    该类负责从cookie文件加载认证信息，并验证登录状态。
    它创建一个已认证的会话，供应用程序的其他部分使用。
    """

    def __init__(self):
        """
        初始化认证模块。

        设置cookie文件路径，创建一个空的cookies字典，
        并初始化一个带有适当头部的requests会话。
        """
        self.cookie_file = config.get("cookie_file")  # 从配置获取cookie文件路径
        self.cookies = {}  # 存储cookies的字典
        self.session = requests.Session()  # 创建一个HTTP会话

        # 设置请求头，模拟浏览器行为
        self.session.headers.update({
            'User-Agent': config.get("user_agent"),  # 用户代理
            'Referer': 'https://www.pixiv.net/'  # 引用页
        })

    def load_cookies(self):
        """
        从cookie文件加载cookies。

        读取cookie文件，解析cookie字符串，并更新会话的cookies。

        Returns:
            bool: 如果cookies成功加载则返回True，否则返回False
        """
        # 检查cookie文件是否存在
        if not os.path.exists(self.cookie_file):
            print(f"错误: Cookie文件 '{self.cookie_file}' 未找到。")
            return False

        try:
            # 读取cookie文件
            with open(self.cookie_file, 'r', encoding='utf-8') as f:
                cookie_str = f.read().strip()

            # 解析cookie字符串（格式：key1=value1; key2=value2; ...）
            cookie_pairs = re.split(r';\s*', cookie_str)
            for pair in cookie_pairs:
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    self.cookies[key] = value

            # 更新会话的cookies
            self.session.cookies.update(self.cookies)

            # 如果cookies不为空，则返回True
            return bool(self.cookies)
        except Exception as e:
            print(f"加载cookies时出错: {e}")
            return False

    def verify_login(self):
        """
        通过向Pixiv发送测试请求来验证cookies是否有效。

        尝试访问需要登录的页面，检查是否被重定向到登录页面。

        Returns:
            bool: 如果登录有效则返回True，否则返回False
        """
        try:
            # 尝试访问需要登录的页面
            response = self.session.get('https://www.pixiv.net/dashboard', timeout=config.get("timeout"))

            # 如果被重定向到登录页面，则cookies无效
            if 'login' in response.url:
                print("错误: Cookie无效或已过期。请更新您的cookie.txt文件。")
                return False

            # 检查HTTP状态码是否为200（成功）
            return response.status_code == 200
        except Exception as e:
            print(f"验证登录时出错: {e}")
            return False

    def authenticate(self):
        """
        加载cookies并验证登录。

        这是该类的主要方法，它协调cookie加载和登录验证过程。

        Returns:
            requests.Session: 如果认证成功则返回已认证的会话，否则返回None
        """
        # 尝试加载cookies
        if not self.load_cookies():
            return None

        # 验证登录状态
        if not self.verify_login():
            return None

        print("成功通过Pixiv认证")
        return self.session  # 返回已认证的会话
