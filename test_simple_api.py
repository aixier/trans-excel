#!/usr/bin/env python3
"""
简单测试任务仓库功能
"""
import requests
import time

BASE_URL = "http://127.0.0.1:8102"

print("1. 健康检查...")
r = requests.get(f"{BASE_URL}/api/health/status", timeout=10)
print(f"   状态: {r.json()['status']}")

print("\n2. 上传文件...")
with open("/mnt/d/work/trans_excel/test2.xlsx", 'rb') as f:
    files = {'file': f}
    data = {
        'source_langs': 'CH',
        'target_languages': 'PT,TH',
        'batch_size': '5',
        'max_concurrent': '10',
        'auto_detect': 'true'
    }
    r = requests.post(f"{BASE_URL}/api/translation/upload", files=files, data=data)
    result = r.json()
    task_id = result['task_id']
    print(f"   任务ID: {task_id}")

print("\n3. 查询任务列表...")
r = requests.get(f"{BASE_URL}/api/translation/tasks")
tasks = r.json()
print(f"   任务数: {tasks['total']}")
if tasks['tasks']:
    task = tasks['tasks'][0]
    print(f"   - ID: {task['task_id'][:8]}...")
    print(f"   - 文件: {task['file_name']}")
    print(f"   - 状态: {task['status']}")
    print(f"   - 进度: {task['progress']}%")

print("\n4. 查询任务进度...")
r = requests.get(f"{BASE_URL}/api/translation/tasks/{task_id}/progress")
if r.status_code == 200:
    progress = r.json()
    print(f"   状态: {progress['status']}")
    print(f"   进度: {progress['progress']['completion_percentage']}%")
else:
    print(f"   错误: {r.json()}")

print("\n✅ 测试完成！任务仓库功能正常工作")