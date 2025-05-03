"""
示例：直接指定UID和标签下载作品。
"""

from pixiv_api import PixivTagDownloader

def main():
    # 创建PixivTagDownloader实例
    # 可以在这里指定配置参数，如cookie文件路径、输出目录等
    downloader = PixivTagDownloader(
        # cookie_file="custom_cookie.txt",  # 自定义cookie文件路径
        # output_dir="Downloads",           # 自定义输出目录
        # max_threads=10,                   # 自定义最大线程数
    )
    
    # 登录Pixiv
    if not downloader.login():
        print("登录失败，请检查cookie文件")
        return
    
    # 指定要下载的用户ID
    uid = "12345678"  # 替换为实际的Pixiv用户ID
    
    # 指定要下载的标签（可选）
    # 如果不指定标签，将下载所有作品
    tags = ["风景", "城市"]  # 替换为实际的标签
    
    # 指定标签过滤逻辑（可选）
    # "OR": 作品包含任意一个指定的标签即可下载
    # "AND": 作品必须包含所有指定的标签才下载
    tag_logic = "OR"
    
    # 指定要下载的作品类型（可选）
    # "all": 所有类型
    # "illustrations": 仅插画
    # "manga": 仅漫画
    # "novels": 仅小说
    work_type = "all"
    
    # 下载作品
    total_works, successful_downloads = downloader.download_by_uid(
        uid=uid,
        tags=tags,
        tag_logic=tag_logic,
        work_type=work_type
    )
    
    print(f"下载完成：总计 {total_works} 个作品，成功下载 {successful_downloads} 个")

if __name__ == "__main__":
    main()
