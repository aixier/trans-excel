#!/usr/bin/env python3
"""
Direct complete translation of 123.xlsx
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

# Add backend to path
sys.path.append('/mnt/d/work/trans_excel/excel_processor/backend')

# Set environment variables
os.environ['DASHSCOPE_API_KEY'] = 'sk-4c89a24b73d24731b86bf26337398cef'

async def main():
    print("=" * 60)
    print("Complete Translation of 123.xlsx")
    print("=" * 60)

    # Import after setting environment
    from app.core.smart_translation_service import SmartTranslationService
    from datetime import datetime

    # Initialize service
    api_key = os.getenv('DASHSCOPE_API_KEY')
    service = SmartTranslationService(api_key=api_key)

    input_file = '/mnt/d/work/trans_excel/123.xlsx'
    output_file = f'/mnt/d/work/trans_excel/full_translation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'

    print(f"Input: {input_file}")
    print(f"Output: {output_file}")

    # Process file
    try:
        # Create task
        task = await service.create_translation_task(
            file_path=input_file,
            sheets_to_translate=None,  # Process all sheets
            urgency='urgent',
            user_preference='speed'
        )

        print(f"\nTask created: {task.task_id}")
        print(f"Strategy: {task.strategy.method.value}")
        print(f"Sheets to translate: {task.sheets_to_translate}")

        # Execute task
        result = await service.execute_translation_task(task)

        print(f"\n✅ Translation completed!")
        print(f"Result file: {task.result_file}")

        # Use actual result file
        output_file = task.result_file or output_file

        # Verify result
        import pandas as pd
        excel = pd.ExcelFile(output_file)
        print(f"\nVerification:")
        print(f"Sheets in result: {excel.sheet_names}")

        total_rows = 0
        for sheet in excel.sheet_names:
            df = pd.read_excel(output_file, sheet_name=sheet)
            total_rows += len(df)
            print(f"  - {sheet}: {len(df)} rows")

        print(f"\nTotal rows processed: {total_rows}")

    except Exception as e:
        print(f"\n❌ Translation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())