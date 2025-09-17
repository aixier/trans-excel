#!/usr/bin/env python3
"""
测试多sheet Excel翻译的完整流程
模拟前端页面的调用时序
"""

import asyncio
import aiohttp
import json
import os
import time
from pathlib import Path
import pandas as pd

# 配置
BASE_URL = "http://localhost:8703"
EXCEL_FILE = "/mnt/d/work/trans_excel/123.xlsx"
OUTPUT_DIR = "/mnt/d/work/trans_excel/test_results"

async def analyze_file(session, file_path):
    """Step 1: 分析文件获取sheets信息"""
    print("\n=== Step 1: 分析文件 ===")

    with open(file_path, 'rb') as f:
        data = aiohttp.FormData()
        data.add_field('file', f, filename=os.path.basename(file_path),
                      content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

        async with session.post(f"{BASE_URL}/api/v1/analyze/sheets", data=data) as resp:
            result = await resp.json()
            print(f"文件包含 {len(result['sheets'])} 个sheets: {result['sheets']}")

            for sheet_name, info in result['sheet_info'].items():
                print(f"  - {sheet_name}: {info['rows']}行 x {info['columns']}列")

            return result

async def upload_and_translate(session, file_path, selected_sheets):
    """Step 2: 上传文件并开始翻译"""
    print(f"\n=== Step 2: 上传文件并翻译选中的sheets: {selected_sheets} ===")

    with open(file_path, 'rb') as f:
        data = aiohttp.FormData()
        data.add_field('file', f, filename=os.path.basename(file_path),
                      content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

        # 添加选中的sheets（模拟前端的FormData）
        data.add_field('selected_sheets', json.dumps(selected_sheets))

        # 添加其他参数（模拟极速模式）
        data.add_field('urgency', 'urgent')
        data.add_field('user_preference', 'speed')
        data.add_field('batch_size', '100')
        data.add_field('concurrent_limit', '50')

        async with session.post(f"{BASE_URL}/api/v1/translate/upload", data=data) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                print(f"错误: {resp.status} - {error_text}")
                return None

            result = await resp.json()
            print(f"任务ID: {result['task_id']}")
            print(f"策略: {result.get('strategy', 'unknown')}")
            return result['task_id']

async def monitor_progress(session, task_id):
    """Step 3: 监控翻译进度"""
    print(f"\n=== Step 3: 监控任务进度 ===")

    while True:
        async with session.get(f"{BASE_URL}/api/v1/task/{task_id}/status") as resp:
            if resp.status != 200:
                print(f"获取状态失败: {resp.status}")
                break

            status = await resp.json()

            # 打印进度信息
            progress = status.get('progress', 0)
            current_step = status.get('current_step', '')
            processed_rows = status.get('processed_rows', 0)
            total_rows = status.get('total_rows', 0)

            if processed_rows and total_rows:
                print(f"进度: {processed_rows}/{total_rows}行 ({progress:.1f}%) - {current_step}")
            else:
                print(f"进度: {progress:.1f}% - {current_step}")

            # 检查是否完成
            if status.get('status') == 'completed':
                print("\n✅ 翻译完成!")
                return status.get('result_file') or status.get('output_file')
            elif status.get('status') == 'failed':
                print(f"\n❌ 翻译失败: {status.get('error')}")
                return None

            await asyncio.sleep(2)

async def download_result(session, task_id, result_file):
    """Step 4: 下载结果文件"""
    print(f"\n=== Step 4: 下载结果 ===")

    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 下载文件
    download_url = f"{BASE_URL}/api/v1/download/{task_id}"
    print(f"下载URL: {download_url}")

    async with session.get(download_url) as resp:
        if resp.status != 200:
            print(f"下载失败: {resp.status}")
            return None

        # 保存文件
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(OUTPUT_DIR, f"translated_{timestamp}.xlsx")

        with open(output_file, 'wb') as f:
            f.write(await resp.read())

        print(f"文件已保存: {output_file}")
        return output_file

def verify_result(original_file, result_file):
    """Step 5: 验证翻译结果"""
    print(f"\n=== Step 5: 验证结果 ===")

    # 读取原始文件
    original_excel = pd.ExcelFile(original_file)
    print(f"\n原始文件sheets: {original_excel.sheet_names}")

    # 读取结果文件
    result_excel = pd.ExcelFile(result_file)
    print(f"结果文件sheets: {result_excel.sheet_names}")

    # 对比每个sheet
    for sheet_name in result_excel.sheet_names:
        print(f"\n检查sheet: {sheet_name}")

        original_df = pd.read_excel(original_file, sheet_name=sheet_name)
        result_df = pd.read_excel(result_file, sheet_name=sheet_name)

        print(f"  原始: {len(original_df)}行 x {len(original_df.columns)}列")
        print(f"  结果: {len(result_df)}行 x {len(result_df.columns)}列")

        # 检查是否有新列（翻译结果）
        new_columns = set(result_df.columns) - set(original_df.columns)
        if new_columns:
            print(f"  新增列: {new_columns}")

        # 统计翻译的单元格数量
        translated_cells = 0
        for col in result_df.columns:
            if col not in original_df.columns:
                continue

            # 比较每列的非空值
            original_non_empty = original_df[col].notna().sum()
            result_non_empty = result_df[col].notna().sum()

            if result_non_empty > original_non_empty:
                diff = result_non_empty - original_non_empty
                translated_cells += diff
                print(f"  列 '{col}': 新增 {diff} 个翻译")

        print(f"  总计翻译: {translated_cells} 个单元格")

async def main():
    """主流程"""
    print("=" * 60)
    print("多Sheet Excel翻译测试")
    print("=" * 60)

    # 检查文件是否存在
    if not os.path.exists(EXCEL_FILE):
        print(f"错误: 文件不存在 {EXCEL_FILE}")
        return

    async with aiohttp.ClientSession() as session:
        try:
            # Step 1: 分析文件
            analysis = await analyze_file(session, EXCEL_FILE)

            # 选择所有sheets进行翻译
            all_sheets = analysis['sheets']
            print(f"\n将翻译所有 {len(all_sheets)} 个sheets")

            # Step 2: 上传并开始翻译
            task_id = await upload_and_translate(session, EXCEL_FILE, all_sheets)
            if not task_id:
                print("翻译任务创建失败")
                return

            # Step 3: 监控进度
            result_file = await monitor_progress(session, task_id)
            if not result_file:
                print("翻译失败或未生成结果文件")
                return

            # Step 4: 下载结果
            downloaded_file = await download_result(session, task_id, result_file)
            if not downloaded_file:
                print("下载结果文件失败")
                return

            # Step 5: 验证结果
            verify_result(EXCEL_FILE, downloaded_file)

            print("\n" + "=" * 60)
            print("测试完成!")
            print("=" * 60)

        except Exception as e:
            print(f"\n错误: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())