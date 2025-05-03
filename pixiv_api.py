"""
Pixiv Tag Downloader 的API模块。
提供简单的接口供其他Python脚本直接调用。
"""

from auth import PixivAuth
from api import PixivAPI
from downloader import PixivDownloader
from config import config

class PixivTagDownloader:
    """
    Pixiv Tag Downloader的API类。

    提供简单的接口供其他Python脚本直接调用，用于下载Pixiv用户的作品。
    """

    def __init__(self, cookie_file=None, output_dir=None, max_threads=None,
                 min_delay=None, max_delay=None, timeout=None, max_retries=None,
                 use_aria2=None):
        """
        初始化Pixiv Tag Downloader API。

        Args:
            cookie_file (str, optional): Cookie文件路径。默认为None，使用配置中的值。
            output_dir (str, optional): 输出目录。默认为None，使用配置中的值。
            max_threads (int, optional): 最大下载线程数。默认为None，使用配置中的值。
            min_delay (float, optional): 请求之间的最小延迟（秒）。默认为None，使用配置中的值。
            max_delay (float, optional): 请求之间的最大延迟（秒）。默认为None，使用配置中的值。
            timeout (int, optional): HTTP请求超时（秒）。默认为None，使用配置中的值。
            max_retries (int, optional): 下载失败时的最大重试次数。默认为None，使用配置中的值。
            use_aria2 (bool, optional): 是否使用Aria2下载。默认为None，自动检测。
        """
        # 更新配置
        if cookie_file:
            config.set("cookie_file", cookie_file)
        if output_dir:
            config.set("output_dir", output_dir)
        if max_threads:
            config.set("max_threads", max_threads)
        if min_delay:
            config.set("min_delay", min_delay)
        if max_delay:
            config.set("max_delay", max_delay)
        if timeout:
            config.set("timeout", timeout)
        if max_retries:
            config.set("max_retries", max_retries)

        # 确保输出目录存在
        config.ensure_output_dir()

        # 保存Aria2设置
        self.use_aria2 = use_aria2

        # 初始化认证、API和下载器
        self.auth = PixivAuth()
        self.session = None
        self.api = None
        self.downloader = None

    def check_aria2_connection(self):
        """
        检查 Aria2 连接状态。

        Returns:
            bool: 如果 Aria2 连接可用则返回 True，否则返回 False
        """
        import os
        from aria2_downloader import Aria2Downloader

        # 检查是否存在 Aria2 配置文件
        if not os.path.exists("aria2.yaml"):
            print("未找到 aria2.yaml 配置文件")
            return False

        # 初始化 Aria2 下载器并检查连接
        aria2 = Aria2Downloader("aria2.yaml")
        if aria2.is_available():
            print("Aria2 连接检查: 成功")
            return True
        else:
            print("Aria2 连接检查: 失败")
            return False

    def login(self):
        """
        登录Pixiv。

        Returns:
            bool: 如果登录成功则返回True，否则返回False
        """
        self.session = self.auth.authenticate()
        if not self.session:
            print("错误: 无法登录Pixiv，请检查cookie文件")
            return False

        self.api = PixivAPI(self.session)

        # 如果指定使用 Aria2，先检查连接
        if self.use_aria2 is True:
            aria2_available = self.check_aria2_connection()
            if not aria2_available:
                print("警告: 无法连接到 Aria2 服务器，将使用直接下载方式")
                self.use_aria2 = False

        self.downloader = PixivDownloader(self.session, self.api, self.use_aria2)
        return True

    def get_user_info(self, uid):
        """
        获取用户信息。

        Args:
            uid (str): 用户ID

        Returns:
            dict: 用户信息或None（如果失败）
        """
        if not self.api:
            if not self.login():
                return None

        return self.api.get_user_info(uid)

    def get_user_works(self, uid, work_type="all"):
        """
        获取用户的所有作品。

        Args:
            uid (str): 用户ID
            work_type (str, optional): 作品类型。可选值："all", "illustrations", "manga", "novels"。默认为"all"。

        Returns:
            list: 作品列表或空列表（如果失败）
        """
        if not self.api:
            if not self.login():
                return []

        return self.api.get_user_works(uid, work_type)

    def get_user_tags(self, uid, work_type="all"):
        """
        获取用户作品中的所有标签。

        Args:
            uid (str): 用户ID
            work_type (str, optional): 作品类型。可选值："all", "illustrations", "manga", "novels"。默认为"all"。

        Returns:
            list: 标签列表或空列表（如果失败）
        """
        if not self.api:
            if not self.login():
                return []

        # 获取用户作品
        works = self.get_user_works(uid, work_type)
        if not works:
            print(f"未找到用户 {uid} 的作品")
            return []

        # 提取标签
        print(f"正在提取用户 {uid} 的标签...")
        tags = self.api.extract_all_tags(works)
        return tags

    def download_by_uid(self, uid, tags=None, tag_logic="OR", work_type="all"):
        """
        根据用户ID下载作品。

        Args:
            uid (str): 用户ID
            tags (list, optional): 标签列表。如果为None，则下载所有作品。默认为None。
            tag_logic (str, optional): 标签过滤逻辑。可选值："AND", "OR"。默认为"OR"。
            work_type (str, optional): 作品类型。可选值："all", "illustrations", "manga", "novels"。默认为"all"。

        Returns:
            tuple: (total_works, successful_downloads) 或 (0, 0)（如果失败）
        """
        if not self.api:
            if not self.login():
                return 0, 0

        # 获取用户信息
        user_info = self.get_user_info(uid)
        if not user_info:
            print(f"错误: 无法获取用户 {uid} 的信息")
            return 0, 0

        print(f"成功获取用户信息: {user_info['name']} (UID: {uid})")

        # 获取用户作品
        print(f"正在获取用户 {uid} 的作品列表...")
        works = self.get_user_works(uid, work_type)

        if not works:
            print(f"错误: 未找到用户 {uid} 的作品")
            return 0, 0

        print(f"找到 {len(works)} 个作品")

        # 下载作品
        selected_tags = tags or []
        if selected_tags:
            print(f"使用标签过滤: {', '.join(selected_tags)} (逻辑: {tag_logic})")
        else:
            print("不使用标签过滤，下载所有作品")

        total_works, successful_downloads = self.downloader.download_works(
            works, selected_tags, tag_logic
        )

        # 显示下载结果摘要
        print("\n" + "=" * 60)
        print("下载完成".center(58))
        print("=" * 60)
        print(f"总计作品数: {total_works}")
        print(f"成功下载: {successful_downloads}")
        print(f"失败: {total_works - successful_downloads}")
        print("=" * 60)

        if successful_downloads > 0:
            print(f"\n作品已保存到 {config.get('output_dir')} 目录")

        return total_works, successful_downloads
