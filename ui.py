"""
Pixiv Tag Downloader 应用程序的用户界面模块。
本模块负责处理与用户的交互，包括显示欢迎信息、获取用户输入、显示标签列表等。
"""

import sys
from utils import is_valid_uid

class PixivUI:
    """
    处理Pixiv Tag Downloader的用户交互。

    该类提供命令行界面，允许用户输入UID、选择标签，
    并显示下载结果摘要。
    """

    def __init__(self, api):
        """
        初始化UI模块。

        Args:
            api (PixivAPI): 用于获取数据的API实例
        """
        self.api = api  # 存储API实例，用于获取用户信息、作品和标签

    def display_welcome(self):
        """
        显示欢迎信息。

        在程序启动时向用户显示欢迎信息和简短的程序描述。
        """
        print("\n" + "=" * 60)
        print("欢迎使用 Pixiv Tag Downloader".center(58))
        print("=" * 60)
        print("本程序可以根据标签下载指定Pixiv用户的作品")
        print("=" * 60 + "\n")

    def get_user_uid(self):
        """
        提示用户输入Pixiv用户ID。

        循环提示用户输入UID，直到输入有效的UID为止。
        验证UID格式是否正确，并检查用户是否存在。

        Returns:
            str: 有效的Pixiv用户ID
        """
        while True:
            # 获取用户输入的UID
            uid = input("请输入Pixiv用户ID (UID): ").strip()

            # 检查UID是否为空
            if not uid:
                print("错误: UID不能为空")
                continue

            # 检查UID格式是否正确（纯数字）
            if not is_valid_uid(uid):
                print("错误: UID必须为纯数字")
                continue

            # 验证用户是否存在
            user_info = self.api.get_user_info(uid)
            if not user_info:
                print("错误: 无法获取该用户信息，请检查UID是否正确")
                continue

            # 显示成功获取用户信息的消息
            print(f"成功获取用户信息: {user_info['name']} (UID: {uid})")
            return uid

    def display_tags(self, tags):
        """
        显示带有索引的标签列表。

        将标签列表格式化为多列显示，每个标签前面有一个索引号。

        Args:
            tags (list): 要显示的标签列表
        """
        # 检查标签列表是否为空
        if not tags:
            print("未找到任何标签")
            return

        # 显示标签列表标题
        print("\n找到以下标签:")
        print("-" * 60)

        # 以多列方式显示标签
        col_width = 30  # 每列宽度
        num_cols = 2    # 列数

        # 按行遍历标签
        for i in range(0, len(tags), num_cols):
            row = []
            # 处理当前行的每一列
            for j in range(num_cols):
                idx = i + j
                if idx < len(tags):
                    # 格式化标签显示（索引号. 标签名）
                    tag_display = f"{idx + 1}. {tags[idx]}"
                    row.append(tag_display.ljust(col_width))  # 左对齐填充
            # 打印当前行
            print("".join(row))

        print("-" * 60)

    def select_tags(self, tags):
        """
        允许用户选择用于过滤的标签。

        显示标签列表，并提示用户选择要下载的标签。
        用户可以选择多个标签，或选择下载所有作品。

        Args:
            tags (list): 可用标签列表

        Returns:
            tuple: (selected_tags, tag_logic) - 选定的标签列表和标签过滤逻辑
        """
        # 检查标签列表是否为空
        if not tags:
            print("没有可选择的标签")
            return [], "OR"  # 返回空标签列表和默认逻辑

        # 显示标签列表
        self.display_tags(tags)

        # 显示选择提示
        print("\n请选择要下载的标签:")
        print("1. 输入标签编号，多个标签用逗号分隔 (例如: 1,3,5)")
        print("2. 输入 'all' 下载所有作品 (不进行标签过滤)")
        print("3. 输入 'q' 退出程序")

        # 循环直到用户输入有效选择
        while True:
            selection = input("\n请输入您的选择: ").strip().lower()

            # 处理退出命令
            if selection == 'q':
                print("程序已退出")
                sys.exit(0)

            # 处理下载所有作品的命令
            if selection == 'all':
                return [], "OR"  # 返回空标签列表和OR逻辑

            try:
                # 解析逗号分隔的索引
                indices = [int(idx.strip()) for idx in selection.split(',')]

                # 验证索引是否有效
                valid_indices = []
                for idx in indices:
                    if 1 <= idx <= len(tags):
                        valid_indices.append(idx - 1)  # 转换为0基索引
                    else:
                        print(f"警告: 索引 {idx} 超出范围，已忽略")

                # 检查是否有有效索引
                if not valid_indices:
                    print("错误: 没有有效的标签索引")
                    continue

                # 获取选定的标签
                selected_tags = [tags[idx] for idx in valid_indices]
                print(f"\n已选择标签: {', '.join(selected_tags)}")

                # 如果选择了多个标签，选择标签过滤逻辑
                tag_logic = "OR"  # 默认逻辑
                if len(selected_tags) > 1:
                    logic_selection = input("\n请选择标签过滤逻辑 (1: AND, 2: OR) [默认: OR]: ").strip()
                    if logic_selection == "1":
                        tag_logic = "AND"

                return selected_tags, tag_logic

            except ValueError:
                # 处理无效输入
                print("错误: 请输入有效的数字，多个数字用逗号分隔")

    def display_download_summary(self, total_works, successful_downloads):
        """
        显示下载结果摘要。

        在下载完成后显示总作品数、成功下载数和失败数。

        Args:
            total_works (int): 要下载的作品总数
            successful_downloads (int): 成功下载的作品数
        """
        # 显示下载摘要
        print("\n" + "=" * 60)
        print("下载完成".center(58))
        print("=" * 60)
        print(f"总计作品数: {total_works}")
        print(f"成功下载: {successful_downloads}")
        print(f"失败: {total_works - successful_downloads}")
        print("=" * 60)

        # 如果有成功下载的作品，显示保存位置
        if successful_downloads > 0:
            print("\n作品已保存到 Output 目录")

        # 显示结束消息
        print("\n感谢使用 Pixiv Tag Downloader!")

    def run(self):
        """
        运行用户界面流程。

        这是UI模块的主要方法，它协调整个用户交互流程：
        1. 显示欢迎信息
        2. 获取用户UID
        3. 获取用户作品
        4. 提取标签
        5. 让用户选择标签
        6. 返回用户选择的结果

        Returns:
            tuple: (uid, works, selected_tags, tag_logic) - 用户ID、作品列表、选定的标签和标签过滤逻辑
                   如果没有找到作品，则返回(None, None, None, None)
        """
        # 显示欢迎信息
        self.display_welcome()

        # 获取用户UID
        uid = self.get_user_uid()

        # 获取用户作品
        print("\n正在获取用户作品列表...")
        works = self.api.get_user_works(uid)

        # 检查是否找到作品
        if not works:
            print("错误: 未找到任何作品")
            return None, None, None, None

        print(f"找到 {len(works)} 个作品")

        # 提取所有标签
        print("\n正在提取标签...")
        all_tags = self.api.extract_all_tags(works)

        # 让用户选择标签
        selected_tags, tag_logic = self.select_tags(all_tags)

        # 返回用户选择的结果
        return uid, works, selected_tags, tag_logic
