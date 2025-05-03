# Pixiv Tag Downloader

一个用于根据标签下载Pixiv用户作品的Python应用程序。

## 功能特点

- 根据用户ID (UID) 下载Pixiv用户的作品（图片、插画、漫画、小说）
- 支持按标签筛选作品
- 支持"与"(AND)和"或"(OR)逻辑的标签筛选
- 多线程下载，提高下载效率
- 随机延迟请求，避免触发Pixiv的访问频率限制
- 按照特定的目录结构和文件命名规则组织下载的内容
- 为图片/漫画类作品生成包含元数据的同名TXT文件
- 小说直接保存为包含元数据和内容的TXT文件

## 安装

### 前提条件

- Python 3.6 或更高版本
- pip (Python包管理器)

### 安装步骤

1. 克隆或下载本仓库

2. 安装依赖包

```bash
pip install -r requirements.txt
```

## 使用方法

### 准备Cookie文件

1. 登录Pixiv网站
2. 使用浏览器开发者工具获取Cookie
3. 将Cookie保存到程序目录下的`cookie.txt`文件中，格式为：`key1=value1; key2=value2; ...`

### 运行程序

程序支持三种使用方式：交互式模式、命令行模式和模块调用。

#### 交互式模式

```bash
python main.py
```

或者显式指定交互式模式：

```bash
python main.py --interactive
```

#### 命令行模式

命令行模式允许您直接指定下载参数，无需交互式输入：

```bash
python main.py --uid <用户ID> [选项]
```

##### 命令行参数

基本参数：

- `--uid <用户ID>` - 要下载的Pixiv用户ID
- `--cookie <文件路径>` - Cookie文件路径 (默认: cookie.txt)
- `--output <目录路径>` - 输出目录 (默认: Output)

标签过滤参数：

- `--tags <标签1,标签2,...>` - 要下载的标签，多个标签用逗号分隔
- `--tag-logic <AND|OR>` - 标签过滤逻辑 (默认: OR)
- `--all` - 下载所有作品，忽略标签过滤

下载控制参数：

- `--max-threads <数量>` - 最大下载线程数 (默认: 5)
- `--min-delay <秒>` - 请求之间的最小延迟 (默认: 1)
- `--max-delay <秒>` - 请求之间的最大延迟 (默认: 3)
- `--timeout <秒>` - HTTP请求超时 (默认: 30)
- `--max-retries <次数>` - 下载失败时的最大重试次数 (默认: 3)
- `--aria2` - 使用Aria2 RPC进行下载
- `--no-aria2` - 不使用Aria2 RPC进行下载

作品类型过滤：

- `--type <all|illustrations|manga|novels>` - 要下载的作品类型 (默认: all)

其他参数：

- `--interactive` - 使用交互式模式，忽略其他命令行参数
- `--version` - 显示版本信息并退出

##### 命令行示例

下载指定用户的所有作品：

```bash
python main.py --uid 12345678 --all
```

下载包含特定标签的作品：

```bash
python main.py --uid 12345678 --tags "风景,城市"
```

下载同时包含多个标签的作品（AND逻辑）：

```bash
python main.py --uid 12345678 --tags "风景,城市" --tag-logic AND
```

只下载小说：

```bash
python main.py --uid 12345678 --type novels
```

使用自定义配置：

```bash
python main.py --uid 12345678 --cookie my_cookie.txt --output Downloads --max-threads 10
```

#### 模块调用

您可以在自己的Python脚本中直接调用Pixiv Tag Downloader的API。这种方式提供了最大的灵活性，允许您将下载功能集成到自己的应用程序中。

##### 基本用法

```python
from pixiv_api import PixivTagDownloader

# 创建下载器实例
downloader = PixivTagDownloader()

# 登录Pixiv
if downloader.login():
    # 下载指定用户的作品
    downloader.download_by_uid(
        uid="12345678",
        tags=["风景", "城市"],
        tag_logic="OR",
        work_type="all"
    )
```

##### 获取用户标签

```python
# 获取用户的所有标签
tags = downloader.get_user_tags("12345678")
print(f"找到 {len(tags)} 个标签: {', '.join(tags)}")
```

##### 示例文件

项目包含多个示例文件，展示了如何使用API：

- `example_download_by_uid.py` - 直接指定UID和标签下载作品
- `example_get_tags_then_download.py` - 先获取用户的所有标签，然后选择特定标签进行下载
- `example_batch_download.py` - 批量下载多个用户的作品
- `example_interactive_tag_selection.py` - 使用交互式界面选择标签

### 使用流程（交互式模式）

1. 程序启动后，会验证Cookie是否有效
2. 输入要下载的Pixiv用户ID (UID)
3. 程序会获取该用户的所有作品并提取标签
4. 选择要下载的标签（或选择下载全部作品）
5. 如果选择了多个标签，可以选择标签过滤逻辑（AND或OR）
6. 程序开始下载符合条件的作品
7. 下载完成后，会显示下载结果摘要

## 目录结构

下载的内容将保存在程序运行目录下的`Output`文件夹中，按照以下结构组织：

```text
Output/
├── 用户ID_用户名/
│   ├── Images/
│   │   ├── 系列名称/
│   │   │   ├── PID_p0_作品标题.jpg
│   │   │   ├── PID_p0_作品标题.txt (元数据)
│   │   │   └── ...
│   │   └── 无系列/
│   │       ├── PID_作品标题/ (多图作品)
│   │       │   ├── PID_p0_作品标题.jpg
│   │       │   ├── PID_p1_作品标题.jpg
│   │       │   ├── ...
│   │       │   └── PID_metadata.txt (元数据)
│   │       └── ...
│   ├── Manga/
│   │   ├── 系列名称/
│   │   │   └── ...
│   │   └── 无系列/
│   │       └── ...
│   └── Novels/
│       ├── 系列名称/
│       │   ├── PID_小说标题.txt (包含元数据和内容)
│       │   └── ...
│       └── 无系列/
│           └── ...
└── ...
```

## 配置

程序支持通过`config.json`文件进行配置。如果该文件不存在，程序将使用默认配置。

### 基本配置

默认配置：

```json
{
    "output_dir": "Output",
    "cookie_file": "cookie.txt",
    "max_threads": 5,
    "min_delay": 1,
    "max_delay": 3,
    "timeout": 30,
    "max_retries": 3,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
```

### Aria2 配置

程序支持使用 Aria2 RPC 进行下载。如果检测到 `aria2.yaml` 配置文件，程序会询问用户是否使用 Aria2 进行下载。

示例配置文件 `aria2.example.yaml`：

```yaml
# Aria2 RPC 配置示例文件
# 将此文件重命名为 aria2.yaml 并根据需要修改配置

# 是否启用 Aria2 RPC 下载
enabled: true

# Aria2 RPC 服务器地址
host: "localhost"

# Aria2 RPC 服务器端口
port: 6800

# 使用的协议 (http、https、ws 或 wss)
# - http/https: 标准 HTTP/HTTPS 协议
# - ws/wss: WebSocket 协议，适用于远程服务器或需要更好的连接稳定性
protocol: "http"

# RPC 路径 (通常为 /jsonrpc)
path: "/jsonrpc"

# RPC 密钥 (如果设置了 --rpc-secret)
# 如果未设置密钥，请将此值留空或删除此行
secret: ""

# 是否跳过 SSL 证书验证 (仅在使用 https 或 wss 协议时有效)
# 对于自签名证书设置为 true
skip_cert_verify: false

# Aria2 RPC 服务器的默认下载路径前缀
# 当使用远程 Aria2 RPC 服务器时，此路径将作为下载路径的前缀
# 例如：如果 Aria2 服务器的默认下载目录是 "/downloads"，则设置为 "/downloads"
# 如果不设置，则使用相对路径
download_path_prefix: ""

# 下载选项
options:
  # 最大同时下载数
  max_concurrent_downloads: 5

  # 单个文件最大连接数
  split: 5

  # 最小分片大小 (单位: 字节)
  min_split_size: "1M"

  # 下载位置 (如果为空，则使用程序的输出目录)
  # 如果指定，将覆盖程序的输出目录设置
  dir: ""

  # 用户代理
  user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

  # 是否启用断点续传
  continue: true

  # 最大重试次数
  max_tries: 5

  # 重试等待时间 (秒)
  retry_wait: 10

  # 连接超时时间 (秒)
  connect_timeout: 30

  # 是否遵循重定向
  follow_location: true

  # 最大重定向次数
  max_redirects: 5

  # 是否自动重命名文件
  auto_file_renaming: false
```

要使用 Aria2 下载功能，您需要：

1. 安装并运行 Aria2 服务器：

   ```bash
   # 本地服务器（HTTP协议）
   aria2c --enable-rpc --rpc-listen-all=true --rpc-allow-origin-all

   # 或者使用 HTTPS/WSS 协议（需要证书）
   aria2c --enable-rpc --rpc-listen-all=true --rpc-allow-origin-all --rpc-secure=true --rpc-certificate=/path/to/cert.pem --rpc-private-key=/path/to/key.pem
   ```

2. 将 `aria2.example.yaml` 重命名为 `aria2.yaml` 并根据需要修改配置

3. 对于远程服务器使用自签名证书的情况：
   - 设置 `protocol` 为 "https" 或 "wss"（WebSocket Secure）
   - 设置 `skip_cert_verify` 为 `true`（如果使用自签名证书）
   - 确保服务器地址和端口正确配置
   - 设置 `download_path_prefix` 为 Aria2 服务器的默认下载目录（例如："/downloads"）
     - 这样程序会正确处理远程服务器上的文件路径
     - 如果不设置，程序会使用相对路径，可能导致文件保存在错误的位置

4. 运行程序，当检测到 Aria2 配置文件时，程序会询问是否使用 Aria2 进行下载

您也可以通过命令行参数 `--aria2` 或 `--no-aria2` 来控制是否使用 Aria2 下载。

## 注意事项

- 本程序仅供个人学习和备份用途
- 请遵守Pixiv的使用条款
- 请合理设置下载延迟和线程数，避免对Pixiv服务器造成过大负担
- 程序依赖于当前Pixiv网站结构和API，如果Pixiv进行重大更新，可能需要修改程序
