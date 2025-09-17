#!/usr/bin/env python3
"""
Translate ALL empty columns automatically
"""

import os
import sys
import asyncio
import pandas as pd
import logging
from pathlib import Path
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

# Add backend to path
sys.path.append('/mnt/d/work/trans_excel/excel_processor/backend')

# Set environment variables
os.environ['DASHSCOPE_API_KEY'] = 'sk-4c89a24b73d24731b86bf26337398cef'

async def detect_empty_columns(file_path):
    """Detect all empty columns that need translation"""
    print("\n检测空列...")

    excel_file = pd.ExcelFile(file_path)
    empty_columns = set()
    source_column = None

    for sheet_name in excel_file.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        print(f"\n分析sheet: {sheet_name}")
        print(f"列: {df.columns.tolist()}")

        # 检测源列（中文列）
        for col in df.columns:
            col_upper = str(col).upper()
            if 'CH' in col_upper or '中' in str(col) or '文' in str(col):
                source_column = col
                print(f"源列: {col}")
                break

        # 检测空列（排除源列）
        for col in df.columns:
            if col != source_column:
                # 检查列是否全为空
                if df[col].isna().all() or (df[col].astype(str).str.strip() == '').all():
                    empty_columns.add(col)
                    print(f"空列需要翻译: {col}")

    return source_column, list(empty_columns)

async def main():
    print("=" * 60)
    print("翻译所有空列")
    print("=" * 60)

    # Import after setting environment
    from app.core.smart_translation_service import SmartTranslationService
    from app.core.smart_translation_service import TranslationTask, StrategyConfig, FileAnalysis

    # Initialize service
    api_key = os.getenv('DASHSCOPE_API_KEY')
    service = SmartTranslationService(api_key=api_key)

    input_file = '/mnt/d/work/trans_excel/123.xlsx'
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f'/mnt/d/work/trans_excel/all_columns_translated_{timestamp}.xlsx'

    print(f"输入: {input_file}")
    print(f"输出: {output_file}")

    # Detect empty columns
    source_col, empty_cols = await detect_empty_columns(input_file)

    print(f"\n检测结果:")
    print(f"  源列: {source_col}")
    print(f"  需要翻译的空列: {empty_cols}")

    if not empty_cols:
        print("没有检测到空列需要翻译")
        return

    # Read file info
    excel_file = pd.ExcelFile(input_file)

    # Count total rows
    total_rows = 0
    for sheet in excel_file.sheet_names:
        df = pd.read_excel(input_file, sheet_name=sheet)
        total_rows += len(df)

    print(f"\n总行数: {total_rows}")

    # 修改文件分析，确保包含所有空列作为目标列
    file_analysis = FileAnalysis(
        total_rows=total_rows,
        non_empty_rows=total_rows,
        source_columns=[source_col] if source_col else [],
        target_columns=empty_cols,  # 使用检测到的所有空列
        estimated_tokens=total_rows * len(empty_cols) * 10,  # 估算token数
        file_complexity='medium'
    )

    # Import TranslationMethod and ProgressType
    from app.core.translation_strategy import TranslationMethod, ProgressType

    # Create strategy
    strategy = StrategyConfig(
        method=TranslationMethod.REALTIME_CONCURRENT,
        reason="快速并发翻译",
        estimated_time="约5-10分钟",
        estimated_seconds=600,
        cost_multiplier=1.0,
        progress_type=ProgressType.BATCH_PROGRESS,
        batch_size=10,
        concurrent_limit=5,
        priority_score=1.0
    )

    # Create task
    task = TranslationTask(
        task_id=f"translate_all_empty_{timestamp}",
        file_path=input_file,
        strategy=strategy,
        file_analysis=file_analysis,
        sheets_to_translate=list(excel_file.sheet_names)
    )

    print("\n开始翻译:")
    print(f"  策略: {task.strategy.method.value}")
    print(f"  批大小: {task.strategy.batch_size}")
    print(f"  并发限制: {task.strategy.concurrent_limit}")
    print(f"  目标列: {task.file_analysis.target_columns}")

    # Execute translation
    try:
        # 直接调用执行方法
        if task.strategy.method == TranslationMethod.REALTIME_CONCURRENT:
            result = await service._execute_realtime_concurrent(task)
        else:
            result = await service._execute_realtime_serial(task)

        print(f"\n✅ 翻译完成!")
        print(f"结果保存到: {task.result_file or output_file}")

        # 验证结果
        result_file = task.result_file or output_file
        if os.path.exists(result_file):
            result_excel = pd.ExcelFile(result_file)
            print(f"\n验证结果:")
            print(f"Sheets: {result_excel.sheet_names}")

            for sheet in result_excel.sheet_names:
                df = pd.read_excel(result_file, sheet_name=sheet)
                print(f"\n  {sheet}:")
                print(f"    行数: {len(df)}")

                # 检查每个目标列
                for col in empty_cols:
                    if col in df.columns:
                        non_empty = df[col].notna().sum()
                        print(f"    {col}: {non_empty} 个非空值")
                    else:
                        print(f"    {col}: 列不存在")

    except Exception as e:
        print(f"\n❌ 翻译失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())