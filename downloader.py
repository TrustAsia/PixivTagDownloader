"""
Pixiv Tag Downloader 应用程序的下载模块。
本模块负责下载Pixiv作品（图片、插画、漫画、小说）并保存到本地文件系统。
支持直接下载和通过Aria2 RPC下载。
"""

import os
import concurrent.futures  # 用于多线程下载
from tqdm import tqdm      # 用于显示进度条
import requests

from config import config
from utils import random_delay, sanitize_filename, format_metadata, format_novel_content
from aria2_downloader import Aria2Downloader

class PixivDownloader:
    """
    处理Pixiv作品（图片、插画、漫画、小说）的下载。

    该类负责从Pixiv下载作品，并按照指定的目录结构保存到本地。
    它支持多线程下载以提高效率，并在请求之间添加随机延迟以避免触发Pixiv的访问频率限制。
    还支持通过Aria2 RPC接口进行下载。
    """

    def __init__(self, session, api, use_aria2=None):
        """
        初始化下载器模块。

        Args:
            session (requests.Session): 已认证的会话，用于发送HTTP请求
            api (PixivAPI): API实例，用于获取作品详情
            use_aria2 (bool, optional): 是否使用Aria2下载。如果为None，则检查配置文件。
        """
        self.session = session        # 存储已认证的会话
        self.api = api                # 存储API实例
        self.max_threads = config.get("max_threads")  # 从配置获取最大线程数
        self.output_dir = config.get("output_dir")    # 从配置获取输出目录

        # 初始化Aria2下载器
        self.aria2 = None
        self.use_aria2 = False

        # 检查是否存在Aria2配置文件
        if os.path.exists("aria2.yaml"):
            self.aria2 = Aria2Downloader("aria2.yaml")

            # 如果未指定是否使用Aria2，则询问用户
            if use_aria2 is None and self.aria2.is_available():
                self._ask_use_aria2()
            elif use_aria2:
                self.use_aria2 = self.aria2.is_available()
        elif use_aria2:
            print("警告: 指定使用Aria2，但未找到配置文件aria2.yaml")
            print("将使用直接下载方式")

    def _ask_use_aria2(self):
        """询问用户是否使用Aria2下载。"""
        print("\n检测到Aria2配置文件，是否使用Aria2进行下载？")
        print("使用Aria2可以提供更好的下载体验，支持断点续传和更高的并发下载。")

        while True:
            choice = input("是否使用Aria2下载？(y/n) [y]: ").strip().lower()

            if choice == "" or choice == "y":
                self.use_aria2 = True
                print("已选择使用Aria2下载")
                break
            elif choice == "n":
                self.use_aria2 = False
                print("已选择使用直接下载")
                break
            else:
                print("无效的选择，请输入 y 或 n")

    def download_image(self, url, save_path, referer="https://www.pixiv.net/"):
        """
        从Pixiv下载图片。

        此方法处理图片的实际下载过程，包括设置适当的HTTP头、处理重试和保存文件。
        支持直接下载和通过Aria2 RPC下载。

        Args:
            url (str): 图片URL
            save_path (str): 保存图片的路径
            referer (str): Referer头部值，Pixiv需要此头部以防止盗链

        Returns:
            bool: 如果下载成功则返回True，否则返回False
        """
        # 设置请求头，Pixiv需要Referer头部以防止盗链
        headers = {
            "Referer": referer,
            "User-Agent": config.get("user_agent")
        }

        # 检查是否使用Aria2下载
        if self.use_aria2 and self.aria2:
            return self._download_with_aria2(url, save_path, headers)
        else:
            return self._download_direct(url, save_path, headers)

    def _download_with_aria2(self, url, save_path, headers):
        """
        使用Aria2下载文件。

        立即提交下载任务到Aria2服务器，不等待下载完成。
        这样可以并行提交多个下载任务，提高下载效率。

        Args:
            url (str): 文件URL
            save_path (str): 保存路径
            headers (dict): 请求头

        Returns:
            bool: 如果成功提交下载任务则返回True，否则返回False
        """
        try:
            # 确保目录存在
            save_dir = os.path.dirname(save_path)
            os.makedirs(save_dir, exist_ok=True)

            # 使用Aria2下载
            gid = self.aria2.download_file(url, save_path, headers)

            if not gid:
                print(f"使用Aria2下载 {url} 失败，尝试直接下载...")
                return self._download_direct(url, save_path, headers)

            # 获取初始状态，确认任务已被添加
            status = self.aria2.get_download_status(gid)
            if status:
                status_text = status.get('status', '')
                if status_text == 'error':
                    error_code = status.get('errorCode', 'unknown')
                    error_message = status.get('errorMessage', 'unknown error')
                    print(f"Aria2下载错误: {error_code} - {error_message}")
                    return self._download_direct(url, save_path, headers)

                # 任务已成功提交，不等待完成
                file_name = os.path.basename(save_path)
                print(f"已提交到Aria2下载: {file_name} (GID: {gid})")
                return True
            else:
                print(f"无法获取下载状态，GID: {gid}，尝试直接下载...")
                return self._download_direct(url, save_path, headers)

        except Exception as e:
            print(f"使用Aria2下载时出错: {e}")
            print("尝试直接下载...")
            return self._download_direct(url, save_path, headers)

    def _download_direct(self, url, save_path, headers):
        """
        直接下载文件。

        Args:
            url (str): 文件URL
            save_path (str): 保存路径
            headers (dict): 请求头

        Returns:
            bool: 如果下载成功则返回True，否则返回False
        """
        # 确保目录存在
        save_dir = os.path.dirname(save_path)
        os.makedirs(save_dir, exist_ok=True)

        # 从配置获取最大重试次数
        max_retries = config.get("max_retries")
        retry_count = 0

        # 尝试下载，如果失败则重试
        while retry_count < max_retries:
            try:
                # 发送GET请求获取图片
                response = self.session.get(url, headers=headers, stream=True, timeout=config.get("timeout"))
                response.raise_for_status()  # 如果响应状态码不是200，则抛出异常

                # 以二进制模式写入文件
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):  # 分块下载以节省内存
                        if chunk:
                            f.write(chunk)

                return True  # 下载成功
            except requests.exceptions.RequestException as e:
                # 处理请求异常（如超时、连接错误等）
                retry_count += 1
                if retry_count < max_retries:
                    # 如果还有重试次数，则重试
                    print(f"下载 {url} 时出错: {e}。正在重试 ({retry_count}/{max_retries})...")
                    random_delay(config.get("min_delay"), config.get("max_delay"))  # 添加随机延迟
                else:
                    # 如果已达到最大重试次数，则放弃
                    print(f"在 {max_retries} 次尝试后无法下载 {url}: {e}")
                    return False  # 下载失败

    def save_metadata(self, metadata, save_path):
        """
        将元数据保存到文件。

        此方法将作品的元数据（如标题、作者、标签等）格式化并保存到文本文件。

        Args:
            metadata (dict): 要保存的元数据
            save_path (str): 保存元数据的路径

        Returns:
            bool: 如果保存成功则返回True，否则返回False
        """
        try:
            # 格式化元数据为字符串
            metadata_str = format_metadata(metadata)

            # 将格式化的元数据写入文件
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(metadata_str)

            return True  # 保存成功
        except Exception as e:
            # 处理保存过程中的异常
            print(f"保存元数据到 {save_path} 时出错: {e}")
            return False  # 保存失败

    def save_novel(self, novel, save_path):
        """
        将小说保存到文件。

        此方法将小说的元数据和内容组合并保存到文本文件。
        如果小说内容为空，会尝试重新获取内容。

        Args:
            novel (dict): 包含内容的小说数据
            save_path (str): 保存小说的路径

        Returns:
            bool: 如果保存成功则返回True，否则返回False
        """
        try:
            # 获取小说内容
            content = novel.get("content", "")

            # 如果内容为空，显示调试信息并尝试重新获取
            if not content:
                print(f"警告: 小说 {novel.get('pid', 'unknown')} 内容为空!")
                # 尝试再次获取内容
                print("正在尝试重新获取内容...")
                novel_content = self.api.get_novel_content(novel.get('pid', ''))
                if novel_content:
                    content = novel_content
                    novel["content"] = content
                    print(f"成功获取小说 {novel.get('pid', 'unknown')} 的内容")
                else:
                    print(f"无法获取小说 {novel.get('pid', 'unknown')} 的内容")

            # 格式化小说元数据和内容
            novel_str = format_novel_content(novel, content)

            # 将格式化的小说写入文件
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(novel_str)

            # 验证内容是否已写入
            if not content:
                print(f"注意: 小说 {novel.get('pid', 'unknown')} 保存时内容为空。")
            else:
                print(f"小说 {novel.get('pid', 'unknown')} 已保存，内容长度为 {len(content)} 个字符。")

            return True  # 保存成功
        except Exception as e:
            # 处理保存过程中的异常
            print(f"保存小说到 {save_path} 时出错: {e}")
            return False  # 保存失败

    def download_artwork(self, artwork):
        """
        下载作品（插画或漫画）。

        此方法处理作品的下载过程，包括创建目录结构、下载图片和保存元数据。

        Args:
            artwork (dict): 作品详情

        Returns:
            bool: 如果下载成功则返回True，否则返回False
        """
        # 提取作品信息
        pid = artwork["pid"]  # 作品ID
        title = sanitize_filename(artwork["title"])  # 净化后的作品标题
        author_uid = artwork["author_uid"]  # 作者UID
        author_name = sanitize_filename(artwork["author_name"])  # 净化后的作者名称
        artwork_type = artwork["type"]  # 作品类型（插画或漫画）

        # 确定系列信息
        series_info = artwork.get("series", {})
        series_title = sanitize_filename(series_info.get("title", "")) if series_info else ""

        # 创建基本目录路径
        # 目录结构: Output/用户ID_用户名/类型/系列/[作品子目录]
        user_dir = os.path.join(self.output_dir, f"{author_uid}_{author_name}")
        type_dir = os.path.join(user_dir, "Images" if artwork_type == "illust" else "Manga")
        series_dir = os.path.join(type_dir, series_title if series_title else "无系列")
        os.makedirs(series_dir, exist_ok=True)  # 创建目录（如果不存在）

        # 获取图片URL
        image_urls = self.api.get_artwork_urls(pid)
        if not image_urls:
            print(f"未找到作品 {pid} 的图片")
            return False

        # 确定是否需要为多图作品创建子目录
        is_multi_image = len(image_urls) > 1
        if is_multi_image:
            # 多图作品需要创建子目录
            artwork_dir = os.path.join(series_dir, f"{pid}_{title}")
            os.makedirs(artwork_dir, exist_ok=True)
            save_dir = artwork_dir
        else:
            # 单图作品直接保存在系列目录下
            save_dir = series_dir

        # 下载图片
        success = True
        total_images = len(image_urls)

        # 如果使用 Aria2 下载，可以一次性提交所有下载任务
        if self.use_aria2 and self.aria2 and total_images > 1:
            print(f"使用 Aria2 下载 {total_images} 张图片...")

        for i, image_data in enumerate(image_urls):
            image_url = image_data["url"]
            image_index = image_data["index"]

            # 从URL提取文件扩展名
            file_ext = os.path.splitext(image_url)[1]
            if not file_ext:
                file_ext = ".jpg"  # 如果未找到扩展名，默认为.jpg

            # 创建文件名
            # 格式: PID_p索引号_作品标题.扩展名
            filename = f"{pid}_p{image_index}_{title}{file_ext}"
            save_path = os.path.join(save_dir, filename)

            # 如果文件已存在，则跳过
            if os.path.exists(save_path):
                print(f"文件已存在: {save_path}")
                continue

            # 下载图片
            if self.use_aria2 and self.aria2:
                # 使用 Aria2 下载时，显示简洁的进度信息
                if total_images > 1:
                    print(f"提交下载任务 ({i+1}/{total_images}): {filename}")
                else:
                    print(f"正在下载 {filename}...")
            else:
                print(f"正在下载 {filename}...")

            if not self.download_image(image_url, save_path):
                success = False

            # 只有在直接下载时才添加随机延迟
            if not (self.use_aria2 and self.aria2):
                random_delay(config.get("min_delay"), config.get("max_delay"))

        # 保存元数据
        if is_multi_image:
            # 多图作品的元数据保存在子目录中
            metadata_path = os.path.join(save_dir, f"{pid}_metadata.txt")
        else:
            # 单图作品的元数据保存在系列目录下
            metadata_path = os.path.join(save_dir, f"{pid}_p0_{title}.txt")

        # 保存元数据
        self.save_metadata(artwork, metadata_path)

        return success  # 返回下载结果

    def download_novel(self, novel):
        """
        下载小说。

        此方法处理小说的下载过程，包括创建目录结构和保存小说内容。

        Args:
            novel (dict): 小说详情

        Returns:
            bool: 如果下载成功则返回True，否则返回False
        """
        # 提取小说信息
        pid = novel["pid"]  # 小说ID
        title = sanitize_filename(novel["title"])  # 净化后的小说标题
        author_uid = novel["author_uid"]  # 作者UID
        author_name = sanitize_filename(novel["author_name"])  # 净化后的作者名称

        # 确定系列信息
        series_info = novel.get("series", {})
        series_title = sanitize_filename(series_info.get("title", "")) if series_info else ""

        # 创建目录路径
        # 目录结构: Output/用户ID_用户名/Novels/系列
        user_dir = os.path.join(self.output_dir, f"{author_uid}_{author_name}")
        novels_dir = os.path.join(user_dir, "Novels")
        series_dir = os.path.join(novels_dir, series_title if series_title else "无系列")
        os.makedirs(series_dir, exist_ok=True)  # 创建目录（如果不存在）

        # 创建文件名和保存路径
        # 格式: PID_小说标题.txt
        filename = f"{pid}_{title}.txt"
        save_path = os.path.join(series_dir, filename)

        # 如果文件已存在，则跳过
        if os.path.exists(save_path):
            print(f"文件已存在: {save_path}")
            return True

        # 保存小说
        print(f"正在保存小说: {filename}")
        return self.save_novel(novel, save_path)  # 调用save_novel方法保存小说

    def download_works(self, works, selected_tags=None, tag_logic="OR"):
        """
        根据选定的标签下载多个作品。

        此方法是下载过程的主要协调者，它根据用户选择的标签过滤作品，
        然后使用多线程并行下载符合条件的作品。

        Args:
            works (list): 作品ID和类型的列表
            selected_tags (list): 用于过滤的标签列表，如果为None则下载所有作品
            tag_logic (str): 标签过滤逻辑（"AND"或"OR"）

        Returns:
            tuple: (total_works, successful_downloads) - 总作品数和成功下载数
        """
        filtered_works = []  # 存储过滤后的作品

        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)

        # 如果需要，根据标签过滤作品
        if selected_tags:
            print(f"正在根据标签过滤作品: {', '.join(selected_tags)} (逻辑: {tag_logic})")

            # 遍历所有作品，使用tqdm显示进度条
            for work in tqdm(works, desc="正在过滤作品"):
                work_id = work["id"]
                work_type = work["type"]

                # 获取作品详情
                if work_type in ["illust", "manga"]:
                    details = self.api.get_artwork_details(work_id)
                elif work_type == "novel":
                    details = self.api.get_novel_details(work_id)
                else:
                    continue

                # 如果无法获取详情，则跳过
                if not details:
                    continue

                # 检查作品是否匹配选定的标签
                work_tags = details.get("tags", [])

                if tag_logic.upper() == "AND":
                    # AND逻辑：作品必须包含所有选定的标签
                    if all(tag in work_tags for tag in selected_tags):
                        filtered_works.append((details, work_type))
                else:
                    # OR逻辑：作品只需包含任意一个选定的标签
                    if any(tag in work_tags for tag in selected_tags):
                        filtered_works.append((details, work_type))
        else:
            # 没有标签过滤，获取所有作品的详情
            print("没有标签过滤，正在下载所有作品")

            # 遍历所有作品，使用tqdm显示进度条
            for work in tqdm(works, desc="正在准备作品"):
                work_id = work["id"]
                work_type = work["type"]

                # 获取作品详情
                if work_type in ["illust", "manga"]:
                    details = self.api.get_artwork_details(work_id)
                elif work_type == "novel":
                    details = self.api.get_novel_details(work_id)
                else:
                    continue

                # 如果成功获取详情，则添加到过滤后的作品列表
                if details:
                    filtered_works.append((details, work_type))

        # 计算总作品数
        total_works = len(filtered_works)
        print(f"找到 {total_works} 个作品需要下载")

        # 使用线程池下载过滤后的作品
        successful = 0  # 成功下载计数
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = []  # 存储所有的Future对象

            # 为每个作品提交下载任务
            for details, work_type in filtered_works:
                if work_type in ["illust", "manga"]:
                    # 提交插画或漫画下载任务
                    future = executor.submit(self.download_artwork, details)
                elif work_type == "novel":
                    # 提交小说下载任务
                    future = executor.submit(self.download_novel, details)
                else:
                    continue

                futures.append(future)

            # 处理完成的任务，使用tqdm显示进度条
            for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="正在下载"):
                # 如果下载成功，增加成功计数
                if future.result():
                    successful += 1

        # 如果使用了 Aria2，显示下载任务状态摘要
        if self.use_aria2 and self.aria2:
            self._show_aria2_download_summary()

        # 返回总作品数和成功下载数
        return total_works, successful

    def _show_aria2_download_summary(self):
        """
        显示 Aria2 下载任务的状态摘要。
        """
        if not self.aria2:
            return

        try:
            # 获取所有活动下载任务
            active_downloads = self.aria2._send_request("aria2.tellActive", [])

            if active_downloads and 'result' in active_downloads:
                active_count = len(active_downloads['result'])
                if active_count > 0:
                    print(f"\n当前有 {active_count} 个 Aria2 下载任务正在进行")
                    print("您可以在 Aria2 Web 界面或客户端中查看下载进度")
                    print("下载完成后，文件将保存在指定的目录中")

            # 获取等待中的下载任务
            waiting_downloads = self.aria2._send_request("aria2.tellWaiting", [0, 1000])

            if waiting_downloads and 'result' in waiting_downloads:
                waiting_count = len(waiting_downloads['result'])
                if waiting_count > 0:
                    print(f"还有 {waiting_count} 个 Aria2 下载任务正在等待")

            # 获取已完成的下载任务
            completed_downloads = self.aria2._send_request("aria2.tellStopped", [0, 1000])

            if completed_downloads and 'result' in completed_downloads:
                completed_count = len(completed_downloads['result'])
                if completed_count > 0:
                    print(f"已完成 {completed_count} 个 Aria2 下载任务")

        except Exception as e:
            print(f"获取 Aria2 下载状态时出错: {e}")
