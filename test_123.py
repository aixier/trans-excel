#!/usr/bin/env python3
"""
测试123.xlsx文件的完整翻译流程
"""

import requests
import time
import os
from datetime import datetime

# 配置
BASE_URL = "http://127.0.0.1:8101"
TEST_FILE = "/mnt/d/work/trans_excel/test_text_targ3_5tab_normall_有注释.xlsx"
OUTPUT_DIR = "/mnt/d/work/trans_excel"

def log(message, level="INFO"):
    """统一日志格式"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def test_123_file():
    """测试123.xlsx文件"""

    log("="*60)
    log(f"开始测试文件: {TEST_FILE}")
    log("="*60)

    # 检查文件
    if not os.path.exists(TEST_FILE):
        log(f"文件不存在: {TEST_FILE}", "ERROR")
        return False

    file_size = os.path.getsize(TEST_FILE) / 1024
    log(f"文件大小: {file_size:.2f} KB")

    # ========== 1. 健康检查 ==========
    log("\n步骤1: 健康检查")
    try:
        response = requests.get(f"{BASE_URL}/api/health/status", timeout=5)
        if response.status_code == 200:
            health = response.json()
            log(f"✅ 服务状态: {health['status']}")
        else:
            log(f"❌ 健康检查失败", "ERROR")
            return False
    except Exception as e:
        log(f"❌ 无法连接到服务: {e}", "ERROR")
        return False

    # ========== 2. 上传文件 ==========
    log("\n步骤2: 上传文件")

    try:
        with open(TEST_FILE, 'rb') as f:
            files = {'file': ('123.xlsx', f)}
            data = {
                'batch_size': 10,
                'max_concurrent': 20,
                'auto_detect': 'true'
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
                log(f"✅ 上传成功! 任务ID: {task_id}")
            else:
                log(f"❌ 上传失败: {response.status_code}", "ERROR")
                return False

    except Exception as e:
        log(f"❌ 上传异常: {e}", "ERROR")
        return False

    # ========== 3. 监控进度 ==========
    log("\n步骤3: 监控翻译进度")

    start_time = time.time()
    last_progress = -1
    final_status = None  # 记录最终状态

    while True:
        elapsed = time.time() - start_time

        try:
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
                percentage = progress.get('completion_percentage', 0)
                current_iteration = progress.get('current_iteration', 0)

                # 显示进度变化
                if translated_rows != last_progress:
                    log(f"📊 进度: {translated_rows}/{total_rows} ({percentage:.1f}%)")
                    log(f"   状态: {status} | 迭代: {current_iteration} | 用时: {elapsed:.1f}秒")

                    # 显示Sheet进度（如果有）
                    sheet_progress = data.get('sheet_progress', [])
                    if sheet_progress:
                        log("   Sheet进度:")
                        for sheet in sheet_progress:
                            sheet_name = sheet.get('name', 'Unknown')
                            sheet_total = sheet.get('total_rows', 0)
                            sheet_translated = sheet.get('translated_rows', 0)
                            sheet_pct = sheet.get('percentage', 0)
                            log(f"     - {sheet_name}: {sheet_translated}/{sheet_total} ({sheet_pct:.1f}%)")

                    last_progress = translated_rows

                # 检查完成状态
                if status == 'completed':
                    log(f"\n✅ 翻译完成！")
                    log(f"   总耗时: {elapsed:.1f} 秒")
                    log(f"   翻译行数: {translated_rows}")

                    # 显示统计信息
                    statistics = data.get('statistics', {})
                    if statistics:
                        api_calls = statistics.get('total_api_calls', 0)
                        tokens = statistics.get('total_tokens_used', 0)
                        cost = statistics.get('total_cost', 0)
                        log(f"   API调用: {api_calls}")
                        log(f"   Token使用: {tokens}")
                        log(f"   成本: ${cost:.4f}")
                    final_status = 'completed'
                    break

                elif status == 'failed':
                    error_msg = data.get('error_message', 'Unknown')
                    log(f"\n❌ 翻译失败: {error_msg}", "ERROR")
                    final_status = 'failed'
                    return False

        except Exception as e:
            log(f"⚠️ 查询异常: {e}", "WARNING")

        time.sleep(5)  # 5秒查询一次

    # 检查是否可以下载
    if final_status != 'completed':
        log("\n⚠️ 翻译未完成，无法下载", "WARNING")
        log(f"   当前状态: {final_status or '超时'}")
        return False

    # ========== 4. 下载结果 ==========
    log("\n步骤4: 下载翻译结果")

    try:
        response = requests.get(
            f"{BASE_URL}/api/translation/tasks/{task_id}/download",
            timeout=60
        )

        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')

            if 'application/json' not in content_type:
                # 保存文件
                output_file = os.path.join(
                    OUTPUT_DIR,
                    f"456_translated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                )

                with open(output_file, 'wb') as f:
                    f.write(response.content)

                file_size = len(response.content) / 1024
                log(f"✅ 下载成功！")
                log(f"   文件: {output_file}")
                log(f"   大小: {file_size:.2f} KB")

                # 简单验证
                if file_size < 1:
                    log("⚠️ 文件大小异常", "WARNING")
                    return False

                return True
            else:
                log("❌ 收到JSON响应而非文件", "ERROR")
                return False

        elif response.status_code == 404:
            log("❌ 文件不存在", "ERROR")
            return False
        else:
            log(f"❌ 下载失败: HTTP {response.status_code}", "ERROR")
            return False

    except Exception as e:
        log(f"❌ 下载异常: {e}", "ERROR")
        return False

def main():
    """主函数"""
    print("\n" + "="*70)
    print(" 测试 123.xlsx 文件翻译 ".center(70))
    print("="*70)

    success = test_123_file()

    print("\n" + "="*70)
    if success:
        print(" ✅ 测试成功 ".center(70))
    else:
        print(" ❌ 测试失败 ".center(70))
    print("="*70 + "\n")

    return 0 if success else 1

if __name__ == "__main__":
    exit(main())