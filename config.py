"""
Pixiv Tag Downloader 应用程序的配置设置。
本模块负责管理应用程序的配置，包括从文件加载配置、保存配置和提供配置值。
"""

import os
import json

# 默认配置
# 这些是应用程序的默认设置，如果没有找到配置文件或配置文件中缺少某些设置，将使用这些值
DEFAULT_CONFIG = {
    "output_dir": "Output",         # 下载内容的输出目录
    "cookie_file": "cookie.txt",    # 存储Pixiv Cookie的文件
    "max_threads": 5,               # 最大下载线程数
    "min_delay": 1,                 # 请求之间的最小延迟（秒）
    "max_delay": 3,                 # 请求之间的最大延迟（秒）
    "timeout": 30,                  # HTTP请求超时时间（秒）
    "max_retries": 3,               # 下载失败时的最大重试次数
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",  # 请求的User-Agent头
}

# 导出DEFAULT_CONFIG，使其可以在其他模块中使用

# 文件路径
CONFIG_FILE = "config.json"  # 配置文件路径
COOKIE_FILE = DEFAULT_CONFIG["cookie_file"]  # Cookie文件路径

class Config:
    """
    应用程序的配置管理器。

    该类负责加载、保存和提供应用程序配置。
    它支持从文件加载配置，并在文件不存在或加载失败时使用默认配置。
    """

    def __init__(self):
        """
        使用默认值初始化配置。

        创建配置对象并尝试从配置文件加载设置。
        如果配置文件不存在或加载失败，将使用默认配置。
        """
        self.config = DEFAULT_CONFIG.copy()  # 复制默认配置
        self.load_config()  # 尝试从文件加载配置

    def load_config(self):
        """
        如果配置文件存在，则从文件加载配置。

        尝试读取并解析配置文件，并用文件中的值更新当前配置。
        如果文件不存在或解析失败，将保留默认配置。
        """
        if os.path.exists(CONFIG_FILE):
            try:
                # 打开并读取配置文件
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)  # 更新配置
                print(f"配置已从 {CONFIG_FILE} 加载")
            except Exception as e:
                print(f"加载配置时出错: {e}")
                print("使用默认配置")

    def save_config(self):
        """
        将当前配置保存到文件。

        将当前配置序列化为JSON并写入配置文件。
        如果写入失败，将打印错误消息。
        """
        try:
            # 将配置写入文件
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            print(f"配置已保存到 {CONFIG_FILE}")
        except Exception as e:
            print(f"保存配置时出错: {e}")

    def get(self, key, default=None):
        """
        获取配置值。

        Args:
            key (str): 配置键
            default: 如果键不存在，返回的默认值

        Returns:
            配置值或默认值（如果键不存在）
        """
        return self.config.get(key, default)

    def set(self, key, value):
        """
        设置配置值。

        Args:
            key (str): 配置键
            value: 配置值
        """
        self.config[key] = value

    def ensure_output_dir(self):
        """
        确保输出目录存在。

        检查输出目录是否存在，如果不存在则创建它。

        Returns:
            str: 输出目录路径
        """
        output_dir = self.get("output_dir")
        os.makedirs(output_dir, exist_ok=True)  # 创建目录（如果不存在）
        return output_dir

# 创建全局配置实例
# 这个实例将在整个应用程序中使用
config = Config()
