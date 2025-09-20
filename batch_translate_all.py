#!/usr/bin/env python3
"""
批量翻译teach目录下所有Excel文件
基于test_123.py的成功经验，逐个文件处理
"""

import requests
import time
import os
from datetime import datetime
from pathlib import Path

# 配置
BASE_URL = "http://localhost:8101"
TEACH_DIR = "/mnt/d/work/trans_excel/teach"
OUTPUT_DIR = "/mnt/d/work/trans_excel"

def log(message, level="INFO"):
    """统一日志格式"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def get_excel_files():
    """获取teach目录下所有Excel文件"""
    teach_path = Path(TEACH_DIR)
    excel_files = []

    if not teach_path.exists():
        log(f"目录不存在: {TEACH_DIR}", "ERROR")
        return []

    for file_path in teach_path.glob("*.xlsx"):
        if file_path.is_file():
            file_size = file_path.stat().st_size / 1024
            excel_files.append({
                'path': str(file_path),
                'name': file_path.name,
                'size_kb': file_size
            })

    # 按文件大小排序，小文件先处理
    excel_files.sort(key=lambda x: x['size_kb'])
    return excel_files

def test_health():
    """健康检查"""
    log("执行健康检查...")
    try:
        response = requests.get(f"{BASE_URL}/api/health/status", timeout=10)
        if response.status_code == 200:
            health = response.json()
            log(f"✅ 服务状态: {health['status']}")
            return True
        else:
            log(f"❌ 健康检查失败: HTTP {response.status_code}", "ERROR")
            return False
    except Exception as e:
        log(f"❌ 无法连接到服务: {e}", "ERROR")
        return False

def translate_single_file(file_info):
    """翻译单个文件"""
    file_path = file_info['path']
    file_name = file_info['name']
    file_size = file_info['size_kb']

    log("="*80)
    log(f"开始处理文件: {file_name}")
    log(f"文件路径: {file_path}")
    log(f"文件大小: {file_size:.2f} KB")
    log("="*80)

    # ========== 1. 上传文件 ==========
    log("\n步骤1: 上传文件")

    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_name, f)}
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
                timeout=60  # 只给上传一个合理的超时时间
            )

            if response.status_code == 200:
                result = response.json()
                task_id = result.get('task_id')
                log(f"✅ 上传成功! 任务ID: {task_id}")
            else:
                log(f"❌ 上传失败: HTTP {response.status_code}", "ERROR")
                if response.text:
                    log(f"错误详情: {response.text}", "ERROR")
                return False, None

    except Exception as e:
        log(f"❌ 上传异常: {e}", "ERROR")
        return False, None

    # ========== 2. 监控进度 - 无超时限制 ==========
    log("\n步骤2: 监控翻译进度 (无超时限制)")

    start_time = time.time()
    last_progress = -1
    last_log_time = 0
    log_interval = 30  # 每30秒输出一次状态

    while True:
        elapsed = time.time() - start_time

        try:
            response = requests.get(
                f"{BASE_URL}/api/translation/tasks/{task_id}/progress",
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                progress = data.get('progress', {})

                total_rows = progress.get('total_rows', 0)
                translated_rows = progress.get('translated_rows', 0)
                percentage = progress.get('completion_percentage', 0)
                current_iteration = progress.get('current_iteration', 0)

                # 显示进度变化或定期输出状态
                should_log = (translated_rows != last_progress or
                             elapsed - last_log_time >= log_interval)

                if should_log:
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
                    last_log_time = elapsed

                # 检查完成状态
                if status == 'completed':
                    log(f"\n✅ 翻译完成！")
                    log(f"   总耗时: {elapsed:.1f} 秒 ({elapsed/60:.1f} 分钟)")
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

                    break

                elif status == 'failed':
                    error_msg = data.get('error_message', 'Unknown')
                    log(f"\n❌ 翻译失败: {error_msg}", "ERROR")
                    return False, task_id

        except Exception as e:
            log(f"⚠️ 查询异常: {e}", "WARNING")

        time.sleep(5)  # 5秒查询一次

    # ========== 3. 下载结果 ==========
    log("\n步骤3: 下载翻译结果")

    try:
        response = requests.get(
            f"{BASE_URL}/api/translation/tasks/{task_id}/download",
            timeout=120  # 下载给个较长超时
        )

        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')

            if 'application/json' not in content_type:
                # 生成输出文件名（包含原文件名和时间戳）
                base_name = Path(file_name).stem
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = os.path.join(
                    OUTPUT_DIR,
                    f"{base_name}_translated_{timestamp}.xlsx"
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
                    return False, task_id

                return True, task_id
            else:
                log("❌ 收到JSON响应而非文件", "ERROR")
                return False, task_id

        elif response.status_code == 404:
            log("❌ 文件不存在", "ERROR")
            return False, task_id
        else:
            log(f"❌ 下载失败: HTTP {response.status_code}", "ERROR")
            return False, task_id

    except Exception as e:
        log(f"❌ 下载异常: {e}", "ERROR")
        return False, task_id

def main():
    """主函数"""
    print("\n" + "="*80)
    print(" 批量翻译teach目录下所有Excel文件 ".center(80))
    print("="*80)

    # 1. 健康检查
    if not test_health():
        log("服务不可用，退出程序", "ERROR")
        return 1

    # 2. 获取所有Excel文件
    excel_files = get_excel_files()
    if not excel_files:
        log("未找到Excel文件", "ERROR")
        return 1

    log(f"\n发现 {len(excel_files)} 个Excel文件:")
    for i, file_info in enumerate(excel_files, 1):
        log(f"  {i}. {file_info['name']} ({file_info['size_kb']:.2f} KB)")

    # 3. 确认处理
    log(f"\n开始批量处理，按文件大小从小到大处理...")

    # 4. 逐个处理文件
    success_count = 0
    failed_files = []
    total_start_time = time.time()

    for i, file_info in enumerate(excel_files, 1):
        log(f"\n🔄 处理进度: {i}/{len(excel_files)}")

        file_start_time = time.time()
        success, task_id = translate_single_file(file_info)
        file_elapsed = time.time() - file_start_time

        if success:
            success_count += 1
            log(f"✅ 文件 {file_info['name']} 处理成功 (耗时: {file_elapsed/60:.1f}分钟)")
        else:
            failed_files.append({
                'name': file_info['name'],
                'task_id': task_id,
                'error_time': datetime.now()
            })
            log(f"❌ 文件 {file_info['name']} 处理失败", "ERROR")

        # 处理间隔（给服务器一点休息时间）
        if i < len(excel_files):
            log("⏸️ 等待5秒后处理下一个文件...")
            time.sleep(5)

    # 5. 总结报告
    total_elapsed = time.time() - total_start_time

    print("\n" + "="*80)
    print(" 批量翻译完成 ".center(80))
    print("="*80)

    log(f"📊 处理统计:")
    log(f"   总文件数: {len(excel_files)}")
    log(f"   成功数量: {success_count}")
    log(f"   失败数量: {len(failed_files)}")
    log(f"   总耗时: {total_elapsed/60:.1f} 分钟 ({total_elapsed/3600:.1f} 小时)")

    if failed_files:
        log(f"\n❌ 失败文件列表:")
        for file_info in failed_files:
            log(f"   - {file_info['name']} (任务ID: {file_info.get('task_id', 'N/A')})")

    success_rate = (success_count / len(excel_files)) * 100
    log(f"\n✅ 成功率: {success_rate:.1f}%")

    print("="*80 + "\n")

    return 0 if success_count == len(excel_files) else 1

if __name__ == "__main__":
    exit(main())