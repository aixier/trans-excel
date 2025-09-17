#!/usr/bin/env python3
"""
Direct translation script - bypasses web service
"""

import os
import sys
import asyncio
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add backend to path
sys.path.append('/mnt/d/work/trans_excel/excel_processor/backend')

# Check required environment variables
required_vars = ['DASHSCOPE_API_KEY', 'OSS_ACCESS_KEY_ID', 'OSS_ACCESS_KEY_SECRET']
for var in required_vars:
    if not os.getenv(var):
        raise ValueError(f"Required environment variable {var} not set")

async def main():
    print("Starting direct translation...")

    # Import after setting environment
    from app.core.smart_translation_service import SmartTranslationService, TranslationTask

    # Initialize service
    api_key = os.getenv('DASHSCOPE_API_KEY')
    service = SmartTranslationService(api_key=api_key)

    # Create task
    input_file = '/mnt/d/work/trans_excel/123.xlsx'
    output_file = '/mnt/d/work/trans_excel/complete_translation_direct.xlsx'

    # Read file info
    excel_file = pd.ExcelFile(input_file)
    print(f"File has {len(excel_file.sheet_names)} sheets: {excel_file.sheet_names}")

    # Count total rows
    total_rows = 0
    for sheet in excel_file.sheet_names:
        df = pd.read_excel(input_file, sheet_name=sheet)
        total_rows += len(df)
    print(f"Total rows to translate: {total_rows}")

    # Import strategy config and file analysis
    from app.core.smart_translation_service import StrategyConfig, FileAnalysis

    # Create strategy
    strategy = StrategyConfig(
        strategy="realtime_concurrent",
        batch_size=10,  # Small batch size to avoid timeout
        concurrent_limit=5,  # Low concurrency
        priority="urgent"
    )

    # Create file analysis
    file_analysis = FileAnalysis(
        total_rows=total_rows,
        total_sheets=len(excel_file.sheet_names),
        file_size=Path(input_file).stat().st_size
    )

    # Create task
    task = TranslationTask(
        task_id="direct_translate",
        file_path=input_file,
        strategy=strategy,
        file_analysis=file_analysis,
        sheets_to_translate=list(excel_file.sheet_names)
    )

    print("\nStarting translation with:")
    print(f"  Strategy: {task.strategy.strategy}")
    print(f"  Batch size: {task.strategy.batch_size}")
    print(f"  Concurrent limit: {task.strategy.concurrent_limit}")
    print(f"  Sheets: {task.sheets_to_translate}")

    # Execute translation
    try:
        result = await service.execute_translation(task)
        print(f"\n✅ Translation completed!")
        print(f"Result saved to: {output_file}")

        # Verify result
        result_excel = pd.ExcelFile(output_file)
        print(f"\nResult contains {len(result_excel.sheet_names)} sheets")
        for sheet in result_excel.sheet_names:
            df = pd.read_excel(output_file, sheet_name=sheet)
            print(f"  {sheet}: {len(df)} rows")

    except Exception as e:
        print(f"\n❌ Translation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())