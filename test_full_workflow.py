#!/usr/bin/env python3
"""
完全模拟 task_management.html 的API调用流程
包括：文件分析、上传翻译、状态查询、文件下载
"""

import requests
import json
import time
import os
from pathlib import Path

# 配置
BASE_URL = "http://localhost:8703"
EXCEL_FILE = "/mnt/d/work/trans_excel/123.xlsx"
OUTPUT_DIR = "/mnt/d/work/trans_excel/test_results"

def log(msg):
    """打印日志"""
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def analyze_file(file_path):
    """Step 1: 分析文件 - 模拟页面的 analyzeFile() 方法"""
    log("=" * 60)
    log("Step 1: 分析文件")
    log("=" * 60)

    with open(file_path, 'rb') as f:
        files = {'file': (os.path.basename(file_path), f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}

        response = requests.post(f"{BASE_URL}/api/v1/analyze/sheets", files=files)

        if response.status_code != 200:
            log(f"错误: {response.status_code} - {response.text}")
            return None

        data = response.json()

        log(f"文件分析成功:")
        log(f"  - Sheets: {data['sheets']}")
        log(f"  - 检测到的语言: {data.get('detected_languages', [])}")

        for sheet_name, info in data['sheet_info'].items():
            log(f"  - {sheet_name}: {info['rows']}行 × {info['columns']}列")

        return data

def upload_and_translate(file_path, selected_sheets):
    """Step 2: 上传文件并开始翻译 - 模拟页面的 uploadFile() 方法"""
    log("=" * 60)
    log("Step 2: 上传文件并开始翻译")
    log("=" * 60)

    log(f"选中的sheets: {selected_sheets}")

    with open(file_path, 'rb') as f:
        # 准备文件
        files = {
            'file': (os.path.basename(file_path), f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }

        # 准备表单数据 - 完全模拟页面的FormData
        data = {
            'selected_sheets': json.dumps(selected_sheets),  # JSON字符串
            'urgency': 'urgent',  # 极速模式
            'user_preference': 'speed',
            'strategy': 'realtime_concurrent',  # MODE_CONFIGS[selectedMode].strategy
            'batch_size': '100',
            'concurrent_limit': '50'
        }

        log("发送的参数:")
        for key, value in data.items():
            log(f"  {key}: {value}")

        response = requests.post(
            f"{BASE_URL}/api/v1/translate/upload",
            files=files,
            data=data
        )

        if response.status_code != 200:
            log(f"错误: {response.status_code} - {response.text}")
            return None

        result = response.json()

        log(f"任务创建成功:")
        log(f"  - 任务ID: {result['task_id']}")
        log(f"  - 文件名: {result['filename']}")
        log(f"  - 策略: {result.get('strategy', 'unknown')}")
        log(f"  - 消息: {result['message']}")

        return result['task_id']

def monitor_task_status(task_id):
    """Step 3: 监控任务状态 - 模拟页面的 WebSocket 消息处理"""
    log("=" * 60)
    log("Step 3: 监控任务进度")
    log("=" * 60)

    completed = False
    result_file = None

    while not completed:
        response = requests.get(f"{BASE_URL}/api/v1/task/{task_id}/status")

        if response.status_code != 200:
            log(f"获取状态失败: {response.status_code}")
            break

        status = response.json()

        # 提取进度信息
        task_status = status.get('status', 'unknown')
        progress = status.get('progress', 0)
        current_step = status.get('current_step', '')
        processed_rows = status.get('processed_rows')
        total_rows = status.get('total_rows')

        # 显示进度 - 模拟页面的进度显示
        if processed_rows and total_rows:
            log(f"[{task_status}] {processed_rows}/{total_rows}行 ({progress:.1f}%) - {current_step}")
        else:
            log(f"[{task_status}] {progress:.1f}% - {current_step}")

        # 检查完成状态
        if task_status == 'completed':
            log("✅ 翻译完成!")
            result_file = status.get('result_file') or status.get('output_file')
            if result_file:
                log(f"  结果文件: {result_file}")
            completed = True

        elif task_status == 'failed':
            log(f"❌ 翻译失败: {status.get('error', 'Unknown error')}")
            completed = True

        else:
            # 继续等待
            time.sleep(2)

    return result_file

def download_result(task_id):
    """Step 4: 下载结果文件 - 模拟页面的下载功能"""
    log("=" * 60)
    log("Step 4: 下载结果文件")
    log("=" * 60)

    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 构建下载URL
    download_url = f"{BASE_URL}/api/v1/download/{task_id}"
    log(f"下载URL: {download_url}")

    response = requests.get(download_url)

    if response.status_code != 200:
        log(f"下载失败: {response.status_code} - {response.text}")
        return None

    # 保存文件
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(OUTPUT_DIR, f"translated_{timestamp}.xlsx")

    with open(output_file, 'wb') as f:
        f.write(response.content)

    log(f"文件已保存: {output_file}")

    # 验证文件
    import pandas as pd
    try:
        excel = pd.ExcelFile(output_file)
        log(f"下载的文件包含sheets: {excel.sheet_names}")

        for sheet in excel.sheet_names:
            df = pd.read_excel(output_file, sheet_name=sheet)
            log(f"  - {sheet}: {len(df)}行 × {len(df.columns)}列")

    except Exception as e:
        log(f"验证文件失败: {e}")

    return output_file

def verify_translation_result(original_file, translated_file):
    """Step 5: 验证翻译结果"""
    log("=" * 60)
    log("Step 5: 验证翻译结果")
    log("=" * 60)

    import pandas as pd

    # 读取原始文件
    original_excel = pd.ExcelFile(original_file)
    translated_excel = pd.ExcelFile(translated_file)

    log(f"原始文件sheets: {original_excel.sheet_names}")
    log(f"翻译后sheets: {translated_excel.sheet_names}")

    # 检查是否所有sheets都被翻译了
    missing_sheets = set(original_excel.sheet_names) - set(translated_excel.sheet_names)
    if missing_sheets:
        log(f"⚠️ 缺失的sheets: {missing_sheets}")

    # 检查每个sheet的翻译情况
    for sheet_name in translated_excel.sheet_names:
        log(f"\n检查sheet: {sheet_name}")

        if sheet_name in original_excel.sheet_names:
            original_df = pd.read_excel(original_file, sheet_name=sheet_name)
            translated_df = pd.read_excel(translated_file, sheet_name=sheet_name)

            log(f"  原始: {len(original_df)}行 × {len(original_df.columns)}列")
            log(f"  翻译后: {len(translated_df)}行 × {len(translated_df.columns)}列")

            # 统计非空单元格
            original_non_empty = original_df.notna().sum().sum()
            translated_non_empty = translated_df.notna().sum().sum()

            new_cells = translated_non_empty - original_non_empty
            if new_cells > 0:
                log(f"  ✅ 新增翻译内容: {new_cells} 个单元格")
            else:
                log(f"  ⚠️ 没有新增翻译内容")

            # 显示前几行的翻译结果
            log(f"  前3行数据预览:")
            for i in range(min(3, len(translated_df))):
                row_data = translated_df.iloc[i].to_dict()
                # 只显示非空值
                non_empty = {k: v for k, v in row_data.items() if pd.notna(v)}
                if non_empty:
                    log(f"    行{i+1}: {non_empty}")

def main():
    """主流程 - 完全模拟页面操作"""
    log("=" * 60)
    log("多Sheet Excel翻译测试 - 模拟页面完整流程")
    log("=" * 60)

    # 检查文件
    if not os.path.exists(EXCEL_FILE):
        log(f"错误: 文件不存在 {EXCEL_FILE}")
        return

    try:
        # Step 1: 分析文件
        analysis = analyze_file(EXCEL_FILE)
        if not analysis:
            log("文件分析失败")
            return

        # 选择所有sheets（模拟用户勾选所有复选框）
        all_sheets = analysis['sheets']
        log(f"\n用户选择翻译所有 {len(all_sheets)} 个sheets")

        # Step 2: 上传并开始翻译
        task_id = upload_and_translate(EXCEL_FILE, all_sheets)
        if not task_id:
            log("创建翻译任务失败")
            return

        # Step 3: 监控进度
        result_file = monitor_task_status(task_id)
        if not result_file:
            log("翻译任务未生成结果文件")
            # 仍然尝试下载

        # Step 4: 下载结果
        downloaded_file = download_result(task_id)
        if not downloaded_file:
            log("下载结果失败")
            return

        # Step 5: 验证结果
        verify_translation_result(EXCEL_FILE, downloaded_file)

        log("\n" + "=" * 60)
        log("测试完成!")
        log("=" * 60)

    except Exception as e:
        log(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()