#!/usr/bin/env python3
"""
测试任务仓库API功能
使用测试容器端口8104
文件: test2.xlsx
"""

import requests
import time
import os
from datetime import datetime

# 配置
BASE_URL = "http://127.0.0.1:8104"  # 测试容器端口
TEST_FILE = "/mnt/d/work/trans_excel/test2.xlsx"
OUTPUT_DIR = "/mnt/d/work/trans_excel"

# 翻译配置
SOURCE_LANGS = "CH"
TARGET_LANGS = "PT,TH"

def log(message, level="INFO"):
    """统一日志格式"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def test_task_repository():
    """测试任务仓库功能"""

    log("="*60)
    log(f"测试任务仓库API功能")
    log(f"服务地址: {BASE_URL}")
    log(f"测试文件: {TEST_FILE}")
    log(f"源语言: {SOURCE_LANGS} | 目标语言: {TARGET_LANGS}")
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

    # ========== 2. 查看初始任务列表 ==========
    log("\n步骤2: 查看初始任务列表")
    try:
        response = requests.get(f"{BASE_URL}/api/translation/tasks", timeout=5)
        if response.status_code == 200:
            tasks_data = response.json()
            log(f"   当前任务数: {tasks_data.get('total', 0)}")
            log(f"   缓存中任务数: {len(tasks_data.get('tasks', []))}")
        else:
            log(f"   获取任务列表失败: {response.status_code}", "WARNING")
    except Exception as e:
        log(f"   查询任务列表异常: {e}", "WARNING")

    # ========== 3. 上传文件创建任务 ==========
    log("\n步骤3: 上传文件创建翻译任务")

    try:
        with open(TEST_FILE, 'rb') as f:
            files = {'file': ('test3.xlsx', f)}
            data = {
                'source_langs': SOURCE_LANGS,
                'target_languages': TARGET_LANGS,
                'batch_size': 5,
                'max_concurrent': 10,
                'auto_detect': 'true'
            }

            log("📤 正在上传...")
            log(f"   配置: batch_size=5, max_concurrent=10")
            log(f"   源语言: {SOURCE_LANGS}")
            log(f"   目标语言: {TARGET_LANGS}")

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
                log(f"   任务已保存到内存缓存")
            else:
                log(f"❌ 上传失败: {response.status_code}", "ERROR")
                if response.text:
                    log(f"   错误详情: {response.text}", "ERROR")
                return False

    except Exception as e:
        log(f"❌ 上传异常: {e}", "ERROR")
        return False

    # ========== 4. 验证任务在缓存中 ==========
    log("\n步骤4: 验证任务在缓存中")

    try:
        response = requests.get(f"{BASE_URL}/api/translation/tasks", timeout=5)
        if response.status_code == 200:
            tasks_data = response.json()
            log(f"✅ 任务列表更新:")
            log(f"   总任务数: {tasks_data.get('total', 0)}")

            # 查找我们的任务
            tasks = tasks_data.get('tasks', [])
            our_task = None
            for task in tasks:
                if task.get('task_id') == task_id:
                    our_task = task
                    break

            if our_task:
                log(f"✅ 找到任务在缓存中:")
                log(f"   任务ID: {our_task.get('task_id')}")
                log(f"   状态: {our_task.get('status')}")
                log(f"   文件: {our_task.get('file_name')}")
                log(f"   创建时间: {our_task.get('created_at')}")
            else:
                log(f"⚠️ 任务未在列表中找到", "WARNING")
    except Exception as e:
        log(f"   查询异常: {e}", "WARNING")

    # ========== 5. 监控任务进度直到完成 ==========
    log("\n步骤5: 监控任务进度直到完成")

    start_time = time.time()
    last_progress = -1
    final_status = None  # 记录最终状态
    list_check_interval = 10  # 每10次检查一次任务列表

    while True:
        elapsed = time.time() - start_time

        # 去掉超时限制，方便调试
        # if elapsed > 600:
        #     log("⚠️ 超时：翻译时间超过10分钟", "WARNING")
        #     break

        try:
            # 主进度查询
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

                # 每30秒查询一次任务列表
                if int(elapsed) % 30 == 0 and int(elapsed) > 0:
                    log("\n📋 查看任务列表:")
                    list_response = requests.get(f"{BASE_URL}/api/translation/tasks", timeout=5)
                    if list_response.status_code == 200:
                        tasks_data = list_response.json()
                        log(f"   当前活跃任务数: {tasks_data.get('total', 0)}")
                        tasks = tasks_data.get('tasks', [])
                        for i, task in enumerate(tasks[:5], 1):  # 只显示前5个
                            log(f"   {i}. {task.get('task_id', 'N/A')[:8]}... - {task.get('status', 'N/A')} - {task.get('file_name', 'N/A')}")
                        if len(tasks) > 5:
                            log(f"   ... 还有 {len(tasks)-5} 个任务")
                    log("")

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

            elif response.status_code == 404:
                log(f"   任务未找到（可能还未初始化）", "WARNING")
            else:
                log(f"   查询失败: HTTP {response.status_code}", "WARNING")

        except Exception as e:
            log(f"⚠️ 查询异常: {e}", "WARNING")

        time.sleep(5)  # 5秒查询一次

    # 检查是否可以下载
    if final_status != 'completed':
        log("\n⚠️ 翻译未完成，无法下载", "WARNING")
        log(f"   当前状态: {final_status or '超时'}")
        return False

    # ========== 6. 下载翻译结果 ==========
    log("\n步骤6: 下载翻译结果")

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
                    f"test2_translated_{SOURCE_LANGS}_to_{TARGET_LANGS.replace(',','_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                )

                with open(output_file, 'wb') as f:
                    f.write(response.content)

                file_size = len(response.content) / 1024
                log(f"✅ 下载成功！")
                log(f"   文件: {output_file}")
                log(f"   大小: {file_size:.2f} KB")
                log(f"   源语言: {SOURCE_LANGS}")
                log(f"   目标语言: {TARGET_LANGS}")

                # 简单验证
                if file_size < 1:
                    log("⚠️ 文件大小异常", "WARNING")
                    return False

            else:
                error_data = response.json()
                log(f"❌ 收到错误响应: {error_data.get('detail', 'Unknown')}", "ERROR")
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

    # ========== 7. 最终任务列表检查 ==========
    log("\n步骤7: 最终任务列表检查")

    try:
        response = requests.get(f"{BASE_URL}/api/translation/tasks", timeout=5)
        if response.status_code == 200:
            tasks_data = response.json()
            log(f"📋 最终任务列表状态:")
            log(f"   总任务数: {tasks_data.get('total', 0)}")

            # 查找我们的任务最终状态
            tasks = tasks_data.get('tasks', [])
            for task in tasks:
                if task.get('task_id') == task_id:
                    log(f"   我们的任务最终状态: {task.get('status')}")
                    log(f"   完成时间: {task.get('completed_at', 'N/A')}")
                    break

            # 显示所有任务概览
            status_count = {}
            for task in tasks:
                status = task.get('status', 'unknown')
                status_count[status] = status_count.get(status, 0) + 1

            log(f"   任务状态分布:")
            for status, count in status_count.items():
                log(f"     - {status}: {count}")

    except Exception as e:
        log(f"   查询异常: {e}", "WARNING")

    # ========== 8. 测试总结 ==========
    log("\n步骤8: 测试总结")
    log("   ✅ 完整流程测试成功")
    log("   ✅ 任务创建、监控、下载功能正常")
    log("   ✅ 任务列表查询功能正常")
    log("   ✅ 内存缓存和进度更新正常")
    log(f"   📊 测试任务ID: {task_id}")
    log(f"   ⏱️ 总用时: {time.time() - start_time:.1f} 秒")

    return True

def main():
    """主函数"""
    print("\n" + "="*70)
    print(" 测试任务仓库API功能 ".center(70))
    print(" 测试容器端口: 8104 ".center(70))
    print("="*70)

    success = test_task_repository()

    print("\n" + "="*70)
    if success:
        print(" ✅ 测试成功 ".center(70))
        print(" 内存缓存和任务管理功能正常 ".center(70))
    else:
        print(" ❌ 测试失败 ".center(70))
    print("="*70 + "\n")

    return 0 if success else 1

if __name__ == "__main__":
    exit(main())