#!/usr/bin/env python3
"""
测试API的analyze接口是否正确检测所有空列
"""

import requests
import json

# API endpoint - v2路由
url = "http://localhost:8703/api/v2/analyze/sheets"

# 上传文件
file_path = "/mnt/d/work/trans_excel/123.xlsx"

with open(file_path, 'rb') as f:
    files = {'file': ('123.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
    response = requests.post(url, files=files)

print("=" * 60)
print("API Analyze Response (v2):")
print("=" * 60)

if response.status_code == 200:
    result = response.json()
    print(json.dumps(result, indent=2, ensure_ascii=False))

    print("\n分析结果:")
    print(f"源语言: {result.get('source_language')}")
    print(f"目标语言: {result.get('target_languages')}")
    print(f"检测到的列:")
    print(f"  - 源列: {result.get('detected_columns', {}).get('source')}")
    print(f"  - 目标列(空列): {result.get('detected_columns', {}).get('targets')}")
else:
    print(f"Error: {response.status_code}")
    print(response.text)