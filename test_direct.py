#!/usr/bin/env python3
"""
直接测试后端的多sheet翻译功能
"""

import sys
import os
sys.path.insert(0, '/app/backend')

from app.core.smart_translation_service import SmartTranslationService
import asyncio
import pandas as pd

async def test_multi_sheet():
    """测试多sheet翻译"""

    # 初始化服务
    service = SmartTranslationService()

    file_path = "/mnt/d/work/trans_excel/123.xlsx"
    sheets_to_translate = ["第一", "第二"]

    print(f"测试文件: {file_path}")
    print(f"要翻译的sheets: {sheets_to_translate}")

    # 分析文件
    print("\n=== 分析文件（指定sheets） ===")
    analysis = service.analyze_excel_file(file_path, sheets_to_translate)
    print(f"总行数: {analysis.total_rows}")
    print(f"非空行数: {analysis.non_empty_rows}")
    print(f"源列: {analysis.source_columns}")
    print(f"目标列: {analysis.target_columns}")

    # 创建翻译任务
    print("\n=== 创建翻译任务 ===")
    task = await service.create_translation_task(
        file_path=file_path,
        urgency='urgent',
        user_preference='speed',
        sheets_to_translate=sheets_to_translate
    )
    print(f"任务ID: {task.task_id}")
    print(f"策略: {task.strategy.method}")
    print(f"要翻译的sheets: {task.sheets_to_translate}")

    # 检查临时文件创建逻辑
    print("\n=== 测试临时文件创建 ===")

    import tempfile
    excel_file = pd.ExcelFile(file_path)
    all_sheets = excel_file.sheet_names
    print(f"文件中的所有sheets: {all_sheets}")

    # 过滤出存在的sheets
    sheets_to_process = [s for s in sheets_to_translate if s in all_sheets]
    print(f"要处理的sheets: {sheets_to_process}")

    if sheets_to_process and sheets_to_process != all_sheets:
        print("将创建临时文件")

        # 创建临时文件
        temp_fd, temp_file_path = tempfile.mkstemp(suffix='.xlsx')
        os.close(temp_fd)

        print(f"临时文件路径: {temp_file_path}")

        # 写入选中的sheets到临时文件
        with pd.ExcelWriter(temp_file_path, engine='openpyxl') as writer:
            for sheet_name in sheets_to_process:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                print(f"  写入sheet '{sheet_name}': {df.shape}")

        # 验证临时文件
        temp_excel = pd.ExcelFile(temp_file_path)
        print(f"临时文件的sheets: {temp_excel.sheet_names}")

        # 清理
        os.remove(temp_file_path)
        print("临时文件已清理")
    else:
        print("不需要创建临时文件")

    print("\n测试完成!")

if __name__ == "__main__":
    asyncio.run(test_multi_sheet())