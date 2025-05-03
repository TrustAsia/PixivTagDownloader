"""
示例：使用Aria2 RPC下载Pixiv作品。
"""

from pixiv_api import PixivTagDownloader
import os

def main():
    # 检查是否存在aria2.yaml配置文件
    if not os.path.exists("aria2.yaml"):
        print("未找到aria2.yaml配置文件")
        print("请将aria2.example.yaml重命名为aria2.yaml并根据需要修改配置")
        return
    
    # 创建PixivTagDownloader实例，指定使用Aria2下载
    downloader = PixivTagDownloader(use_aria2=True)
    
    # 登录Pixiv
    if not downloader.login():
        print("登录失败，请检查cookie文件")
        return
    
    # 指定要下载的用户ID
    uid = "12345678"  # 替换为实际的Pixiv用户ID
    
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
    
    print(f"找到 {len(tags)} 个标签")
    
    # 选择前两个标签（如果有）
    selected_tags = tags[:2] if len(tags) >= 2 else tags
    
    print(f"\n已选择标签: {', '.join(selected_tags)}")
    
    # 下载包含选定标签的作品，使用Aria2
    total_works, successful_downloads = downloader.download_by_uid(
        uid=uid,
        tags=selected_tags,
        tag_logic="OR"
    )
    
    print(f"下载完成：总计 {total_works} 个作品，成功下载 {successful_downloads} 个")

if __name__ == "__main__":
    main()
