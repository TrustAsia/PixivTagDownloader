"""
Pixiv Tag Downloader 应用程序的实用工具函数。
本模块提供各种辅助函数，用于文件名处理、延迟生成、目录创建、格式化等操作。
"""

import os
import re
import random
import time

def sanitize_filename(filename):
    """
    通过移除无效字符并限制长度来净化文件名。

    Windows文件系统不允许某些特殊字符出现在文件名中，
    且有文件名长度限制。此函数确保文件名符合这些要求。

    Args:
        filename (str): 原始文件名

    Returns:
        str: 净化后的文件名
    """
    # 用下划线替换无效字符
    invalid_chars = r'[\\/*?:"<>|]'
    sanitized = re.sub(invalid_chars, '_', filename)

    # 限制文件名长度（Windows的路径长度限制为255个字符）
    # 为安全起见，我们将文件名限制为100个字符
    if len(sanitized) > 100:
        name_parts = sanitized.rsplit('.', 1)
        if len(name_parts) > 1:
            # 如果有文件扩展名，保留它
            name, ext = name_parts
            sanitized = f"{name[:96]}...{ext}"
        else:
            sanitized = f"{sanitized[:96]}..."

    return sanitized

def random_delay(min_delay=1, max_delay=3):
    """
    在min_delay和max_delay秒之间随机休眠一段时间。

    这个函数用于在请求之间添加随机延迟，以避免触发Pixiv的访问频率限制。

    Args:
        min_delay (float): 最小延迟（秒）
        max_delay (float): 最大延迟（秒）
    """
    delay = random.uniform(min_delay, max_delay)  # 生成随机延迟
    time.sleep(delay)  # 休眠指定时间

def create_directory(directory_path):
    """
    如果目录不存在，则创建它。

    Args:
        directory_path (str): 目录路径

    Returns:
        str: 创建的目录路径
    """
    os.makedirs(directory_path, exist_ok=True)  # 创建目录（如果不存在）
    return directory_path

def format_tags(tags):
    """
    将标签列表格式化为字符串。

    Args:
        tags (list): 标签字符串列表

    Returns:
        str: 逗号分隔的标签字符串
    """
    return ', '.join(tags) if tags else ""  # 用逗号连接标签，如果标签为空则返回空字符串

def is_valid_uid(uid):
    """
    检查UID是否有效（仅包含数字）。

    Pixiv的用户ID应该只包含数字。此函数验证输入的UID是否符合此要求。

    Args:
        uid (str): 要检查的UID

    Returns:
        bool: 如果有效则返回True，否则返回False
    """
    return bool(re.match(r'^\d+$', uid))  # 检查UID是否只包含数字

def format_metadata(metadata):
    """
    将元数据格式化为用于写入文件的字符串。

    此函数将作品的元数据（如标题、作者、标签等）格式化为结构化文本。

    Args:
        metadata (dict): 包含元数据的字典

    Returns:
        str: 格式化的元数据字符串
    """
    formatted = []  # 存储格式化行的列表

    # 添加标题
    if 'title' in metadata:
        formatted.append(f"标题 (Title): {metadata['title']}")

    # 添加作者信息
    if 'author_uid' in metadata:
        formatted.append(f"作者UID (Author UID): {metadata['author_uid']}")
    if 'author_name' in metadata:
        formatted.append(f"作者用户名 (Author Username): {metadata['author_name']}")

    # 添加作品/小说ID
    if 'pid' in metadata:
        formatted.append(f"作品PID (Artwork/Novel PID): {metadata['pid']}")

    # 添加标签
    if 'tags' in metadata:
        tags_str = format_tags(metadata['tags'])
        formatted.append(f"标签 (Tags): {tags_str}")

    # 如果有系列信息，添加它
    if 'series_title' in metadata and metadata['series_title']:
        series_info = f"{metadata['series_title']}"
        if 'series_id' in metadata and metadata['series_id']:
            series_info += f" / {metadata['series_id']}"
        formatted.append(f"系列信息 (Series): {series_info}")

    # 添加描述
    if 'description' in metadata:
        formatted.append(f"描述 (Description):\n{metadata['description']}")

    # 添加图片URL（可选）
    if 'url' in metadata:
        formatted.append(f"原始URL (Original URL): {metadata['url']}")

    # 将所有行连接成一个字符串
    return '\n'.join(formatted)

def format_novel_content(metadata, content):
    """
    将小说元数据和内容格式化为用于写入文件的字符串。

    此函数将小说的元数据和正文内容组合成一个格式化的文本，
    元数据和正文之间用分隔符分隔。

    Args:
        metadata (dict): 包含元数据的字典
        content (str): 小说内容

    Returns:
        str: 格式化的小说字符串
    """
    # 格式化元数据
    metadata_str = format_metadata(metadata)
    # 组合元数据和内容，中间用分隔符分隔
    return f"{metadata_str}\n\n--- (分隔符) ---\n\n正文 (Content):\n{content}"
