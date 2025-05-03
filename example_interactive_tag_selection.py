"""
示例：使用交互式界面选择标签。
"""

from pixiv_api import PixivTagDownloader

def display_tags(tags):
    """显示标签列表。"""
    if not tags:
        print("未找到任何标签")
        return
    
    print("\n找到以下标签:")
    print("-" * 60)
    
    # 显示标签（每行两列）
    col_width = 30
    num_cols = 2
    
    for i in range(0, len(tags), num_cols):
        row = []
        for j in range(num_cols):
            idx = i + j
            if idx < len(tags):
                tag_display = f"{idx + 1}. {tags[idx]}"
                row.append(tag_display.ljust(col_width))
        print("".join(row))
    
    print("-" * 60)

def select_tags(tags):
    """让用户选择标签。"""
    if not tags:
        print("没有可选择的标签")
        return [], "OR"
    
    display_tags(tags)
    
    print("\n请选择要下载的标签:")
    print("1. 输入标签编号，多个标签用逗号分隔 (例如: 1,3,5)")
    print("2. 输入 'all' 下载所有作品 (不进行标签过滤)")
    print("3. 输入 'q' 退出程序")
    
    while True:
        selection = input("\n请输入您的选择: ").strip().lower()
        
        if selection == 'q':
            print("程序已退出")
            return None, None
        
        if selection == 'all':
            return [], "OR"
        
        try:
            # 解析逗号分隔的索引
            indices = [int(idx.strip()) for idx in selection.split(',')]
            
            # 验证索引
            valid_indices = []
            for idx in indices:
                if 1 <= idx <= len(tags):
                    valid_indices.append(idx - 1)  # 转换为0基索引
                else:
                    print(f"警告: 索引 {idx} 超出范围，已忽略")
            
            if not valid_indices:
                print("错误: 没有有效的标签索引")
                continue
            
            # 获取选定的标签
            selected_tags = [tags[idx] for idx in valid_indices]
            print(f"\n已选择标签: {', '.join(selected_tags)}")
            
            # 选择标签过滤逻辑
            tag_logic = "OR"
            if len(selected_tags) > 1:
                logic_selection = input("\n请选择标签过滤逻辑 (1: AND, 2: OR) [默认: OR]: ").strip()
                if logic_selection == "1":
                    tag_logic = "AND"
            
            return selected_tags, tag_logic
        
        except ValueError:
            print("错误: 请输入有效的数字，多个数字用逗号分隔")

def main():
    # 创建PixivTagDownloader实例
    downloader = PixivTagDownloader()
    
    # 登录Pixiv
    if not downloader.login():
        print("登录失败，请检查cookie文件")
        return
    
    # 获取用户ID
    while True:
        uid = input("请输入Pixiv用户ID (UID): ").strip()
        
        if not uid:
            print("错误: UID不能为空")
            continue
        
        # 验证用户是否存在
        user_info = downloader.get_user_info(uid)
        if not user_info:
            print("错误: 无法获取该用户信息，请检查UID是否正确")
            continue
        
        print(f"成功获取用户信息: {user_info['name']} (UID: {uid})")
        break
    
    # 获取用户作品
    print("\n正在获取用户作品列表...")
    works = downloader.get_user_works(uid)
    
    if not works:
        print("错误: 未找到任何作品")
        return
    
    print(f"找到 {len(works)} 个作品")
    
    # 提取标签
    print("\n正在提取标签...")
    tags = downloader.get_user_tags(uid)
    
    # 让用户选择标签
    selected_tags, tag_logic = select_tags(tags)
    
    if selected_tags is None:  # 用户选择退出
        return
    
    # 下载作品
    total_works, successful_downloads = downloader.download_by_uid(
        uid=uid,
        tags=selected_tags,
        tag_logic=tag_logic
    )
    
    print(f"下载完成：总计 {total_works} 个作品，成功下载 {successful_downloads} 个")

if __name__ == "__main__":
    main()
