"""
示例：批量下载多个用户的作品。
"""

from pixiv_api import PixivTagDownloader

def main():
    # 创建PixivTagDownloader实例
    downloader = PixivTagDownloader()
    
    # 登录Pixiv
    if not downloader.login():
        print("登录失败，请检查cookie文件")
        return
    
    # 定义要下载的用户列表
    # 每个用户可以指定不同的标签和过滤逻辑
    users = [
        {
            "uid": "12345678",  # 替换为实际的Pixiv用户ID
            "tags": ["风景", "城市"],
            "tag_logic": "OR",
            "work_type": "all"
        },
        {
            "uid": "87654321",  # 替换为实际的Pixiv用户ID
            "tags": ["人物", "肖像"],
            "tag_logic": "AND",
            "work_type": "illustrations"
        },
        {
            "uid": "11223344",  # 替换为实际的Pixiv用户ID
            "tags": None,  # 下载所有作品
            "tag_logic": "OR",
            "work_type": "novels"
        }
    ]
    
    # 批量下载
    total_all = 0
    successful_all = 0
    
    for i, user in enumerate(users):
        print(f"\n[{i+1}/{len(users)}] 处理用户 {user['uid']}...")
        
        # 获取用户信息
        user_info = downloader.get_user_info(user["uid"])
        if not user_info:
            print(f"无法获取用户 {user['uid']} 的信息，跳过")
            continue
        
        print(f"用户信息: {user_info['name']} (UID: {user['uid']})")
        
        # 下载作品
        total, successful = downloader.download_by_uid(
            uid=user["uid"],
            tags=user["tags"],
            tag_logic=user["tag_logic"],
            work_type=user["work_type"]
        )
        
        total_all += total
        successful_all += successful
    
    # 显示总结果
    print("\n" + "=" * 60)
    print("批量下载完成".center(58))
    print("=" * 60)
    print(f"总计用户数: {len(users)}")
    print(f"总计作品数: {total_all}")
    print(f"成功下载: {successful_all}")
    print(f"失败: {total_all - successful_all}")
    print("=" * 60)

if __name__ == "__main__":
    main()
