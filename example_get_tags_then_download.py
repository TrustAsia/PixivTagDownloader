"""
示例：先获取用户的所有标签，然后选择特定标签进行下载。
"""

from pixiv_api import PixivTagDownloader

def main():
    # 创建PixivTagDownloader实例
    downloader = PixivTagDownloader()
    
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
    
    print(f"找到 {len(tags)} 个标签:")
    for i, tag in enumerate(tags):
        print(f"{i+1}. {tag}")
    
    # 在实际应用中，可以在这里让用户选择标签
    # 这里我们直接选择前两个标签作为示例
    selected_indices = [0, 1]  # 选择第1个和第2个标签
    
    if len(tags) < 2:
        # 如果标签数量不足，则使用所有标签
        selected_tags = tags
    else:
        # 否则使用选定的标签
        selected_tags = [tags[i] for i in selected_indices]
    
    print(f"\n已选择标签: {', '.join(selected_tags)}")
    
    # 下载包含选定标签的作品
    total_works, successful_downloads = downloader.download_by_uid(
        uid=uid,
        tags=selected_tags,
        tag_logic="OR",  # 可以根据需要更改为"AND"
        work_type="all"
    )
    
    print(f"下载完成：总计 {total_works} 个作品，成功下载 {successful_downloads} 个")

if __name__ == "__main__":
    main()
