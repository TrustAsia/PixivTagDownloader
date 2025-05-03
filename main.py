"""
Pixiv Tag Downloader 应用程序的主入口点。
本模块作为程序的启动点，协调各个组件的工作流程。
支持交互式使用和命令行参数直接调用。
"""

import sys
import argparse
from auth import PixivAuth  # 导入认证模块
from api import PixivAPI  # 导入API交互模块
from downloader import PixivDownloader  # 导入下载器模块
from ui import PixivUI  # 导入用户界面模块
from config import config, DEFAULT_CONFIG  # 导入配置模块

def parse_arguments():
    """
    解析命令行参数。

    Returns:
        argparse.Namespace: 解析后的命令行参数
    """
    parser = argparse.ArgumentParser(description='Pixiv Tag Downloader - 根据标签下载Pixiv用户作品')

    # 基本参数
    parser.add_argument('--uid', type=str, help='要下载的Pixiv用户ID')
    parser.add_argument('--cookie', type=str, help='Cookie文件路径 (默认: cookie.txt)')
    parser.add_argument('--output', type=str, help=f'输出目录 (默认: {DEFAULT_CONFIG["output_dir"]})')

    # 标签过滤参数
    parser.add_argument('--tags', type=str, help='要下载的标签，多个标签用逗号分隔 (例如: tag1,tag2,tag3)')
    parser.add_argument('--tag-logic', type=str, choices=['AND', 'OR'], default='OR',
                        help='标签过滤逻辑: AND(且)或OR(或) (默认: OR)')
    parser.add_argument('--all', action='store_true', help='下载所有作品，忽略标签过滤')

    # 下载控制参数
    parser.add_argument('--max-threads', type=int, help=f'最大下载线程数 (默认: {DEFAULT_CONFIG["max_threads"]})')
    parser.add_argument('--min-delay', type=float, help=f'请求之间的最小延迟(秒) (默认: {DEFAULT_CONFIG["min_delay"]})')
    parser.add_argument('--max-delay', type=float, help=f'请求之间的最大延迟(秒) (默认: {DEFAULT_CONFIG["max_delay"]})')
    parser.add_argument('--timeout', type=int, help=f'HTTP请求超时(秒) (默认: {DEFAULT_CONFIG["timeout"]})')
    parser.add_argument('--max-retries', type=int, help=f'下载失败时的最大重试次数 (默认: {DEFAULT_CONFIG["max_retries"]})')

    # Aria2 参数
    parser.add_argument('--aria2', action='store_true', help='使用Aria2 RPC进行下载')
    parser.add_argument('--no-aria2', action='store_true', help='不使用Aria2 RPC进行下载')

    # 作品类型过滤
    parser.add_argument('--type', type=str, choices=['all', 'illustrations', 'manga', 'novels'], default='all',
                        help='要下载的作品类型 (默认: all)')

    # 交互模式
    parser.add_argument('--interactive', action='store_true', help='使用交互式模式，忽略其他命令行参数')

    # 版本信息
    parser.add_argument('--version', action='version', version='Pixiv Tag Downloader v1.0.0')

    return parser.parse_args()

def update_config_from_args(args):
    """
    根据命令行参数更新配置。

    Args:
        args (argparse.Namespace): 解析后的命令行参数
    """
    # 更新配置
    if args.cookie:
        config.set("cookie_file", args.cookie)

    if args.output:
        config.set("output_dir", args.output)

    if args.max_threads:
        config.set("max_threads", args.max_threads)

    if args.min_delay:
        config.set("min_delay", args.min_delay)

    if args.max_delay:
        config.set("max_delay", args.max_delay)

    if args.timeout:
        config.set("timeout", args.timeout)

    if args.max_retries:
        config.set("max_retries", args.max_retries)

def run_interactive_mode():
    """
    运行交互式模式。

    Returns:
        tuple: (total_works, successful_downloads) 或 None（如果出错）
    """
    try:
        # 初始化配置，确保输出目录存在
        config.ensure_output_dir()

        # 使用cookie认证Pixiv
        print("正在验证登录信息...")
        auth = PixivAuth()
        session = auth.authenticate()

        # 如果认证失败，退出程序
        if not session:
            print("错误: 无法登录Pixiv，请检查cookie.txt文件")
            sys.exit(1)

        # 初始化API和用户界面
        api = PixivAPI(session)
        ui = PixivUI(api)

        # 运行用户界面获取用户输入
        uid, works, selected_tags, tag_logic = ui.run()

        # 检查是否有作品可下载
        if works is None:
            print("程序已退出")
            return None

        # 初始化下载器（交互式模式下自动检测Aria2）
        # 先检查 Aria2 连接
        from aria2_downloader import Aria2Downloader
        import os
        use_aria2 = None
        if os.path.exists("aria2.yaml"):
            print("\n正在检查 Aria2 服务器连接...")
            aria2 = Aria2Downloader("aria2.yaml")
            if aria2.is_available():
                print("Aria2 服务器连接正常，可以使用 Aria2 下载")
            else:
                print("警告: 无法连接到 Aria2 服务器，将使用直接下载方式")
                use_aria2 = False

        downloader = PixivDownloader(session, api, use_aria2)

        # 下载符合条件的作品
        total_works, successful_downloads = downloader.download_works(
            works, selected_tags, tag_logic
        )

        # 显示下载结果摘要
        ui.display_download_summary(total_works, successful_downloads)

        return total_works, successful_downloads

    except Exception as e:
        print(f"\n程序发生错误: {e}")
        return None

def run_command_line_mode(args):
    """
    运行命令行模式。

    Args:
        args (argparse.Namespace): 解析后的命令行参数

    Returns:
        tuple: (total_works, successful_downloads) 或 None（如果出错）
    """
    try:
        # 确保输出目录存在
        config.ensure_output_dir()

        # 检查必要参数
        if not args.uid:
            print("错误: 命令行模式需要指定 --uid 参数")
            return None

        # 使用cookie认证Pixiv
        print("正在验证登录信息...")
        auth = PixivAuth()
        session = auth.authenticate()

        # 如果认证失败，退出程序
        if not session:
            print("错误: 无法登录Pixiv，请检查cookie文件")
            return None

        # 初始化API
        api = PixivAPI(session)

        # 获取用户信息
        user_info = api.get_user_info(args.uid)
        if not user_info:
            print(f"错误: 无法获取用户 {args.uid} 的信息")
            return None

        print(f"成功获取用户信息: {user_info['name']} (UID: {args.uid})")

        # 获取用户作品
        print("\n正在获取用户作品列表...")
        works = api.get_user_works(args.uid, args.type)

        if not works:
            print("错误: 未找到任何作品")
            return None

        print(f"找到 {len(works)} 个作品")

        # 处理标签
        selected_tags = []
        if not args.all and args.tags:
            # 解析标签
            selected_tags = [tag.strip() for tag in args.tags.split(',') if tag.strip()]
            print(f"\n已选择标签: {', '.join(selected_tags)}")
            print(f"标签过滤逻辑: {args.tag_logic}")

        # 确定是否使用Aria2
        use_aria2 = None
        if args.aria2:
            use_aria2 = True
            # 检查 Aria2 连接
            from aria2_downloader import Aria2Downloader
            import os
            if os.path.exists("aria2.yaml"):
                print("\n正在检查 Aria2 服务器连接...")
                aria2 = Aria2Downloader("aria2.yaml")
                if not aria2.is_available():
                    print("警告: 无法连接到 Aria2 服务器，将使用直接下载方式")
                    use_aria2 = False
            else:
                print("警告: 未找到 aria2.yaml 配置文件，将使用直接下载方式")
                use_aria2 = False
        elif args.no_aria2:
            use_aria2 = False

        # 初始化下载器
        downloader = PixivDownloader(session, api, use_aria2)

        # 下载符合条件的作品
        total_works, successful_downloads = downloader.download_works(
            works, selected_tags, args.tag_logic
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

        print("\n感谢使用 Pixiv Tag Downloader!")

        return total_works, successful_downloads

    except Exception as e:
        print(f"\n程序发生错误: {e}")
        return None

def main():
    """
    Pixiv Tag Downloader的主函数。

    该函数协调整个应用程序的工作流程，支持交互式模式和命令行参数直接调用。
    """
    try:
        # 解析命令行参数
        args = parse_arguments()

        # 根据命令行参数更新配置
        update_config_from_args(args)

        # 根据模式运行程序
        if args.interactive or len(sys.argv) == 1:
            # 交互式模式
            run_interactive_mode()
        else:
            # 命令行模式
            run_command_line_mode(args)

    except KeyboardInterrupt:
        # 处理用户中断（Ctrl+C）
        print("\n程序已被用户中断")
        sys.exit(0)
    except Exception as e:
        # 处理其他异常
        print(f"\n程序发生错误: {e}")
        sys.exit(1)

# 程序入口点
if __name__ == "__main__":
    main()
