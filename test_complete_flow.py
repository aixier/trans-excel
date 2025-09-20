#!/usr/bin/env python3
"""
完整的翻译流程测试脚本
测试文件: /mnt/d/work/trans_excel/teach/sfdaf.xlsx
流程: 上传 -> 状态查询 -> 下载
"""

import requests
import time
import os
import json
from datetime import datetime

# 配置
BASE_URL = "http://localhost:8101"
TEST_FILE = "/mnt/d/work/trans_excel/teach/sfdaf.xlsx"
OUTPUT_DIR = "/mnt/d/work/trans_excel"

def log(message, level="INFO"):
    """统一日志格式"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def test_complete_flow():
    """测试完整的翻译流程"""

    log("="*60)
    log(f"开始测试文件: {TEST_FILE}")
    log("="*60)

    # 检查文件是否存在
    if not os.path.exists(TEST_FILE):
        log(f"文件不存在: {TEST_FILE}", "ERROR")
        return False

    file_size = os.path.getsize(TEST_FILE) / 1024
    log(f"文件大小: {file_size:.2f} KB")

    # =====================================
    # 步骤1: 健康检查
    # =====================================
    log("\n步骤1: 健康检查")
    try:
        response = requests.get(f"{BASE_URL}/api/health/status", timeout=5)
        if response.status_code == 200:
            health = response.json()
            log(f"✅ 服务状态: {health['status']}")
            log(f"   版本: {health.get('version', 'unknown')}")

            # 检查各个组件状态
            checks = health.get('checks', {})
            for component, status in checks.items():
                log(f"   {component}: {status.get('status', 'unknown')}")
        else:
            log(f"❌ 健康检查失败: HTTP {response.status_code}", "ERROR")
            return False
    except Exception as e:
        log(f"❌ 无法连接到服务: {e}", "ERROR")
        return False

    # =====================================
    # 步骤2: 上传文件
    # =====================================
    log("\n步骤2: 上传文件")
    task_id = None

    try:
        with open(TEST_FILE, 'rb') as f:
            files = {'file': ('sfdaf.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}

            # 不传递target_languages，让系统自动检测
            data = {
                'batch_size': 5,
                'max_concurrent': 10,
                'region_code': 'cn-hangzhou',
                'auto_detect': 'true'  # 自动检测需要翻译的内容
            }

            log("📤 正在上传...")
            response = requests.post(
                f"{BASE_URL}/api/translation/upload",
                files=files,
                data=data,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                task_id = result.get('task_id')
                status = result.get('status')
                message = result.get('message')

                log(f"✅ 上传成功!")
                log(f"   任务ID: {task_id}")
                log(f"   状态: {status}")
                log(f"   消息: {message}")
            else:
                log(f"❌ 上传失败: HTTP {response.status_code}", "ERROR")
                if response.text:
                    log(f"   响应: {response.text}", "ERROR")
                return False

    except Exception as e:
        log(f"❌ 上传异常: {e}", "ERROR")
        return False

    # =====================================
    # 步骤3: 查询进度
    # =====================================
    log("\n步骤3: 监控翻译进度")

    if not task_id:
        log("没有有效的任务ID", "ERROR")
        return False

    start_time = time.time()
    last_progress = -1
    max_wait_time = 300  # 最多等待5分钟
    check_interval = 3   # 每3秒查询一次

    while True:
        elapsed = time.time() - start_time

        if elapsed > max_wait_time:
            log(f"⏰ 超时: 已等待 {elapsed:.1f} 秒", "WARNING")
            break

        try:
            # 查询详细进度
            response = requests.get(
                f"{BASE_URL}/api/translation/tasks/{task_id}/progress",
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                progress = data.get('progress', {})

                total_rows = progress.get('total_rows', 0)
                translated_rows = progress.get('translated_rows', 0)
                current_iteration = progress.get('current_iteration', 0)
                max_iterations = progress.get('max_iterations', 0)
                percentage = progress.get('completion_percentage', 0)

                # 只在进度有变化时显示
                if translated_rows != last_progress:
                    log(f"📊 进度: {translated_rows}/{total_rows} ({percentage:.1f}%)")
                    log(f"   状态: {status} | 迭代: {current_iteration}/{max_iterations} | 用时: {elapsed:.1f}秒")

                    # 显示统计信息（如果有）
                    statistics = data.get('statistics')
                    if statistics:
                        api_calls = statistics.get('total_api_calls', 0)
                        tokens = statistics.get('total_tokens_used', 0)
                        cost = statistics.get('total_cost', 0)
                        if api_calls > 0:
                            log(f"   API调用: {api_calls} | Tokens: {tokens} | 成本: ${cost:.4f}")

                    last_progress = translated_rows

                # 检查是否完成
                if status == 'completed':
                    log(f"\n✅ 翻译完成!")
                    log(f"   总耗时: {elapsed:.1f} 秒")
                    log(f"   翻译行数: {translated_rows}")
                    break

                elif status == 'failed':
                    error_msg = data.get('error_message', 'Unknown error')
                    log(f"\n❌ 翻译失败!", "ERROR")
                    log(f"   错误: {error_msg}", "ERROR")
                    return False

            elif response.status_code == 404:
                log(f"❌ 任务不存在: {task_id}", "ERROR")
                return False
            else:
                log(f"⚠️ 查询失败: HTTP {response.status_code}", "WARNING")

        except Exception as e:
            log(f"⚠️ 查询异常: {e}", "WARNING")

        time.sleep(check_interval)

    # =====================================
    # 步骤4: 下载结果
    # =====================================
    log("\n步骤4: 下载翻译结果")

    try:
        response = requests.get(
            f"{BASE_URL}/api/translation/tasks/{task_id}/download",
            timeout=60
        )

        if response.status_code == 200:
            # 检查响应类型
            content_type = response.headers.get('content-type', '')

            if 'application/json' in content_type:
                # JSON响应可能是错误或下载链接
                json_data = response.json()
                log(f"⚠️ 收到JSON响应: {json_data}", "WARNING")

                # 如果有download_url，尝试下载
                if 'download_url' in json_data:
                    download_url = json_data['download_url']
                    log(f"尝试从URL下载: {download_url}")
                    # 这里可以添加额外的下载逻辑
                    return False
            else:
                # 直接是文件内容
                output_file = os.path.join(OUTPUT_DIR, f"sfdaf_translated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")

                with open(output_file, 'wb') as f:
                    f.write(response.content)

                file_size = len(response.content) / 1024
                log(f"✅ 下载成功!")
                log(f"   文件: {output_file}")
                log(f"   大小: {file_size:.2f} KB")

                # 验证是否为有效的Excel文件
                if file_size < 1:
                    log("⚠️ 文件大小异常，可能下载失败", "WARNING")
                    return False

                return True

        elif response.status_code == 404:
            log("❌ 翻译结果文件不存在", "ERROR")
            return False
        else:
            log(f"❌ 下载失败: HTTP {response.status_code}", "ERROR")
            if response.text:
                log(f"   响应: {response.text}", "ERROR")
            return False

    except Exception as e:
        log(f"❌ 下载异常: {e}", "ERROR")
        return False

def main():
    """主函数"""
    print("\n" + "="*70)
    print(" 翻译系统完整流程测试 ".center(70))
    print("="*70)

    success = test_complete_flow()

    print("\n" + "="*70)
    if success:
        print(" ✅ 测试成功 ".center(70))
    else:
        print(" ❌ 测试失败 ".center(70))
    print("="*70 + "\n")

    return 0 if success else 1

if __name__ == "__main__":
    exit(main())