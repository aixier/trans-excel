#!/usr/bin/env python3
"""
n8n API 配置读取工具
"""

import os
from pathlib import Path

def get_api_key():
    """
    获取 n8n API Key

    优先级：
    1. 环境变量 N8N_API_KEY
    2. .env.local 文件
    3. 返回 None（需要交互输入）
    """
    # 方式1：环境变量
    api_key = os.getenv('N8N_API_KEY')
    if api_key:
        return api_key

    # 方式2：.env.local 文件
    env_file = Path(__file__).parent.parent / '.env.local'
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line.startswith('N8N_API_KEY='):
                    api_key = line.split('=', 1)[1].strip()
                    if api_key:
                        return api_key

    return None

def get_api_headers():
    """获取带认证的请求头"""
    api_key = get_api_key()
    if not api_key:
        raise ValueError(
            "未找到 API Key！请设置环境变量或创建 .env.local 文件\n"
            "参考：n8n/scripts/N8N_API_KEY_SETUP.md"
        )

    return {
        'X-N8N-API-KEY': api_key,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

def get_n8n_url():
    """获取 n8n 基础 URL"""
    return os.getenv('N8N_URL', 'http://localhost:5678')

# 使用示例
if __name__ == '__main__':
    try:
        headers = get_api_headers()
        print(f"✅ API Key 已加载")
        print(f"📍 n8n URL: {get_n8n_url()}")
        print(f"\n示例用法:")
        print(f"  from config import get_api_headers")
        print(f"  headers = get_api_headers()")
        print(f"  response = requests.get('http://localhost:5678/api/v1/workflows', headers=headers)")
    except ValueError as e:
        print(f"❌ {e}")
