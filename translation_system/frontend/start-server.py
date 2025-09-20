#!/usr/bin/env python3
"""
简单的HTTP服务器，用于运行前端应用
不需要Node.js，纯Python实现
"""

import http.server
import socketserver
import os
import sys
from urllib.parse import urlparse

class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """支持CORS的HTTP请求处理器"""

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        print(f"🌐 [Server] {format % args}")

def start_server(port=3000):
    """启动HTTP服务器"""
    # 切换到当前目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    print(f"🚀 [Server] 启动前端服务器...")
    print(f"📍 [Server] 目录: {os.getcwd()}")
    print(f"🔗 [Server] 地址: http://localhost:{port}")
    print(f"🎯 [Server] 后端API: http://127.0.0.1:8101")
    print(f"📄 [Server] 主页面: http://localhost:{port}/index.html")
    print(f"🐛 [Server] 调试页面: http://localhost:{port}/index-debug.html")
    print("=" * 50)

    try:
        with socketserver.TCPServer(("", port), CORSHTTPRequestHandler) as httpd:
            print(f"✅ [Server] 服务器启动成功，监听端口 {port}")
            print("📝 [Server] 按 Ctrl+C 停止服务器")
            print("🌐 [Server] 等待请求...")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 [Server] 服务器已停止")
    except OSError as e:
        if e.errno == 98:  # Address already in use
            print(f"❌ [Server] 端口 {port} 已被占用，尝试端口 {port + 1}")
            start_server(port + 1)
        else:
            print(f"❌ [Server] 启动失败: {e}")
            sys.exit(1)

if __name__ == "__main__":
    port = 3000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("❌ 端口号必须是数字")
            sys.exit(1)

    start_server(port)