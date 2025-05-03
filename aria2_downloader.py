"""
Aria2 RPC 下载器模块。
提供通过 Aria2 RPC 接口下载文件的功能。
支持 HTTP、HTTPS 和 WebSocket (WS/WSS) 协议。
"""

import os
import json
import yaml
import requests
import uuid
import ssl
import websocket

class Aria2Downloader:
    """
    Aria2 RPC 下载器类。

    使用 Aria2 的 JSON-RPC 接口下载文件。
    """

    def __init__(self, config_file="aria2.yaml"):
        """
        初始化 Aria2 下载器。

        Args:
            config_file (str, optional): Aria2 配置文件路径。默认为 "aria2.yaml"。
        """
        self.config_file = config_file
        self.config = None
        self.rpc_url = None
        self.enabled = False
        self.use_websocket = False
        self.skip_cert_verify = False
        self.ws_connection = None
        self.download_path_prefix = None  # Aria2 RPC 服务器的默认下载路径前缀
        self.load_config()

    def load_config(self):
        """
        从配置文件加载 Aria2 配置。

        Returns:
            bool: 如果配置加载成功并启用了 Aria2，则返回 True，否则返回 False。
        """
        if not os.path.exists(self.config_file):
            print(f"Aria2 配置文件 '{self.config_file}' 不存在。")
            return False

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)

            # 检查配置是否启用 Aria2
            self.enabled = self.config.get('enabled', False)

            if not self.enabled:
                print("Aria2 下载功能已在配置文件中禁用。")
                return False

            # 获取协议配置
            protocol = self.config.get('protocol', 'http')
            host = self.config.get('host', 'localhost')
            port = self.config.get('port', 6800)
            path = self.config.get('path', '/jsonrpc')

            # 检查是否使用 WebSocket 协议
            if protocol.lower() in ['ws', 'wss']:
                self.use_websocket = True
                ws_protocol = protocol.lower()
                self.rpc_url = f"{ws_protocol}://{host}:{port}{path}"
            else:
                self.use_websocket = False
                self.rpc_url = f"{protocol}://{host}:{port}{path}"

            # 获取 SSL 证书验证设置
            self.skip_cert_verify = self.config.get('skip_cert_verify', False)

            # 获取下载路径前缀设置
            self.download_path_prefix = self.config.get('download_path_prefix', '')
            if self.download_path_prefix:
                print(f"Aria2 下载路径前缀: {self.download_path_prefix}")

            print(f"已加载 Aria2 配置，RPC URL: {self.rpc_url}，协议: {protocol}")
            return True

        except Exception as e:
            print(f"加载 Aria2 配置时出错: {e}")
            self.enabled = False
            return False

    def is_available(self):
        """
        检查 Aria2 RPC 服务是否可用。

        Returns:
            bool: 如果 Aria2 RPC 服务可用，则返回 True，否则返回 False。
        """
        if not self.enabled:
            print("Aria2 下载功能已在配置文件中禁用")
            return False

        if not self.rpc_url:
            print("Aria2 RPC URL 未配置")
            return False

        try:
            # 发送 getVersion 请求检查服务是否可用
            print(f"正在连接 Aria2 服务器: {self.rpc_url}")
            response = self._send_request("aria2.getVersion", [])

            if response and 'result' in response:
                version = response['result'].get('version', 'unknown')
                print(f"Aria2 服务可用，版本: {version}")
                return True
            elif response and 'error' in response:
                error = response['error']
                print(f"Aria2 服务返回错误: 代码 {error.get('code', '未知')}, 消息: {error.get('message', '未知错误')}")
            else:
                print("Aria2 服务返回无效响应")

            return False
        except Exception as e:
            print(f"检查 Aria2 服务时出错: {e}")
            return False

    def download_file(self, url, save_path, headers=None):
        """
        使用 Aria2 下载文件。

        Args:
            url (str): 要下载的文件 URL。
            save_path (str): 文件保存路径。
            headers (dict, optional): 请求头。默认为 None。

        Returns:
            str: 下载任务的 GID，如果下载失败则返回 None。
        """
        if not self.enabled or not self.rpc_url:
            print("Aria2 下载功能未启用或配置不正确。")
            return None

        try:
            # 准备下载选项
            options = self.config.get('options', {}).copy()

            # 获取文件名和目录
            filename = os.path.basename(save_path)
            save_dir = os.path.dirname(save_path)

            # 处理下载路径
            if self.download_path_prefix:
                # 如果设置了下载路径前缀，使用相对路径
                if options.get('dir'):
                    # 配置中已指定目录，只使用文件名
                    out_path = filename
                else:
                    # 将本地相对路径与远程路径前缀拼接
                    # 移除本地输出目录前缀，只保留相对路径部分
                    from config import config
                    local_output_dir = config.get("output_dir")

                    # 如果保存路径以本地输出目录开头，则提取相对路径部分
                    if save_dir.startswith(local_output_dir):
                        relative_dir = save_dir[len(local_output_dir):].lstrip(os.sep)
                        # 拼接远程路径前缀和相对路径
                        remote_dir = os.path.join(self.download_path_prefix, relative_dir)
                        options['dir'] = remote_dir.replace('\\', '/')  # 确保使用正斜杠
                    else:
                        # 如果不是以输出目录开头，直接使用远程路径前缀
                        options['dir'] = self.download_path_prefix

                    out_path = filename
            else:
                # 没有设置下载路径前缀，使用原来的逻辑
                if options.get('dir'):
                    # 使用文件名而不是完整路径
                    out_path = filename
                else:
                    # 使用完整路径
                    options['dir'] = save_dir
                    out_path = filename

            # 添加文件名
            options['out'] = out_path

            # 添加请求头
            if headers:
                options['header'] = [f"{k}: {v}" for k, v in headers.items()]

            # 发送下载请求
            # Aria2 需要将 URL 作为数组传递，即使只有一个 URL
            params = [[url]]  # URL 必须是数组的第一个元素，且本身也是一个数组
            if options:
                params.append(options)

            response = self._send_request("aria2.addUri", params)

            if response and 'result' in response:
                gid = response['result']
                print(f"Aria2 下载任务已创建，GID: {gid}")
                return gid

            print(f"创建 Aria2 下载任务失败: {response}")
            return None

        except Exception as e:
            print(f"使用 Aria2 下载文件时出错: {e}")
            return None

    def get_download_status(self, gid):
        """
        获取下载任务的状态。

        Args:
            gid (str): 下载任务的 GID。

        Returns:
            dict: 下载任务的状态信息，如果获取失败则返回 None。
        """
        if not self.enabled or not self.rpc_url:
            return None

        try:
            response = self._send_request("aria2.tellStatus", [gid])
            if response and 'result' in response:
                return response['result']
            return None
        except Exception as e:
            print(f"获取下载状态时出错: {e}")
            return None

    def _send_request(self, method, params):
        """
        发送 JSON-RPC 请求到 Aria2。
        支持 HTTP/HTTPS 和 WebSocket (WS/WSS) 协议。

        Args:
            method (str): RPC 方法名。
            params (list): 方法参数。

        Returns:
            dict: 响应数据，如果请求失败则返回 None。
        """
        if not self.rpc_url:
            return None

        # 添加密钥（如果有）
        secret = self.config.get('secret')
        if secret:
            params.insert(0, f"token:{secret}")

        # 准备请求数据
        request_id = str(uuid.uuid4())
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        }

        # 根据协议类型选择发送方式
        if self.use_websocket:
            return self._send_websocket_request(payload, request_id)
        else:
            return self._send_http_request(payload)

    def _send_http_request(self, payload):
        """
        通过 HTTP/HTTPS 发送 JSON-RPC 请求。

        Args:
            payload (dict): JSON-RPC 请求数据。

        Returns:
            dict: 响应数据，如果请求失败则返回 None。
        """
        try:
            response = requests.post(
                self.rpc_url,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"},
                verify=not self.skip_cert_verify
            )

            if response.status_code == 200:
                return response.json()

            print(f"Aria2 HTTP RPC 请求失败: HTTP {response.status_code}")
            return None

        except Exception as e:
            print(f"发送 Aria2 HTTP RPC 请求时出错: {e}")
            return None

    def _send_websocket_request(self, payload, _):
        """
        通过 WebSocket 发送 JSON-RPC 请求。

        Args:
            payload (dict): JSON-RPC 请求数据。
            _ (str): 请求ID（未使用，保留参数以保持接口一致性）。

        Returns:
            dict: 响应数据，如果请求失败则返回 None。
        """
        try:
            # 配置 WebSocket 选项
            ws_options = {}

            # 处理自签名证书
            if self.skip_cert_verify:
                ws_options["sslopt"] = {"cert_reqs": ssl.CERT_NONE}

            # 创建 WebSocket 连接
            ws = websocket.create_connection(
                self.rpc_url,
                **ws_options
            )

            # 发送请求
            ws.send(json.dumps(payload))

            # 接收响应
            response = ws.recv()
            ws.close()

            if response:
                return json.loads(response)

            return None

        except Exception as e:
            print(f"发送 Aria2 WebSocket RPC 请求时出错: {e}")
            return None
