"""
示例：使用远程 Aria2 RPC 服务器下载 Pixiv 作品。
本示例演示如何通过 WSS 或 HTTPS 协议连接到远程 Aria2 服务器。
"""

from pixiv_api import PixivTagDownloader
import os
import yaml

def main():
    # 检查是否存在 aria2.yaml 配置文件
    if not os.path.exists("aria2.yaml"):
        print("未找到 aria2.yaml 配置文件")
        print("请将 aria2.example.yaml 重命名为 aria2.yaml 并根据需要修改配置")
        return

    # 读取配置文件，检查是否为远程服务器配置
    try:
        with open("aria2.yaml", 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        host = config.get('host', 'localhost')
        protocol = config.get('protocol', 'http')
        port = config.get('port', 6800)

        print(f"Aria2 服务器配置: {protocol}://{host}:{port}")

        if host == 'localhost' or host == '127.0.0.1':
            print("警告: 当前配置为本地服务器。如需连接远程服务器，请修改 host 参数。")

        if protocol not in ['https', 'wss']:
            print("警告: 连接远程服务器建议使用 HTTPS 或 WSS 协议以确保安全。")

        if protocol in ['https', 'wss'] and not config.get('skip_cert_verify', False):
            print("提示: 如果使用自签名证书，请将 skip_cert_verify 设置为 true。")

        # 检查 Aria2 连接
        print("\n正在检查 Aria2 服务器连接...")
        from aria2_downloader import Aria2Downloader
        aria2 = Aria2Downloader("aria2.yaml")
        if not aria2.is_available():
            print("错误: 无法连接到 Aria2 服务器，请检查配置和服务器状态")
            return
        print("Aria2 服务器连接正常，可以使用 Aria2 下载")

    except Exception as e:
        print(f"读取配置文件时出错: {e}")
        return

    # 创建 PixivTagDownloader 实例，指定使用 Aria2 下载
    downloader = PixivTagDownloader(use_aria2=True)

    # 登录 Pixiv
    if not downloader.login():
        print("登录失败，请检查 cookie 文件")
        return

    # 指定要下载的用户 ID
    uid = input("请输入要下载的 Pixiv 用户 ID: ").strip()

    # 获取用户信息
    user_info = downloader.get_user_info(uid)
    if not user_info:
        print(f"无法获取用户 {uid} 的信息")
        return

    print(f"用户信息: {user_info['name']} (UID: {uid})")

    # 获取用户的所有标签
    tags = downloader.get_user_tags(uid)

    if not tags:
        print(f"未找到用户 {uid} 的标签")
        return

    print(f"找到 {len(tags)} 个标签:")

    # 显示所有标签
    for i, tag in enumerate(tags):
        print(f"{i+1}. {tag}")

    # 让用户选择标签
    print("\n请选择要下载的标签 (输入标签编号，多个标签用逗号分隔，输入 'all' 下载所有):")
    choice = input("> ").strip().lower()

    selected_tags = []
    if choice != 'all':
        try:
            # 解析用户选择
            indices = [int(idx.strip()) - 1 for idx in choice.split(',')]
            selected_tags = [tags[idx] for idx in indices if 0 <= idx < len(tags)]

            if not selected_tags:
                print("未选择有效标签，将下载所有作品")
            else:
                print(f"\n已选择标签: {', '.join(selected_tags)}")

                # 选择标签逻辑
                print("\n请选择标签过滤逻辑:")
                print("1. OR - 包含任一标签的作品 (默认)")
                print("2. AND - 同时包含所有标签的作品")

                logic_choice = input("> ").strip()
                tag_logic = "AND" if logic_choice == "2" else "OR"

                print(f"已选择标签逻辑: {tag_logic}")
        except Exception as e:
            print(f"解析选择时出错: {e}")
            print("将下载所有作品")
            selected_tags = []
    else:
        print("将下载所有作品")

    # 下载作品
    total_works, successful_downloads = downloader.download_by_uid(
        uid=uid,
        tags=selected_tags,
        tag_logic="OR" if not selected_tags or len(selected_tags) <= 1 else tag_logic
    )

    print(f"下载完成：总计 {total_works} 个作品，成功下载 {successful_downloads} 个")

if __name__ == "__main__":
    main()
