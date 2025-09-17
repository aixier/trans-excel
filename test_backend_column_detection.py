#!/usr/bin/env python3
"""
测试后端的SmartTranslationService是否正确检测所有空列
"""

import pandas as pd
import sys
import os

# 添加backend路径
sys.path.insert(0, '/mnt/d/work/trans_excel/excel_processor/backend')

from app.core.smart_translation_service import SmartTranslationService

def test_column_detection():
    """测试列检测功能"""
    file_path = "/mnt/d/work/trans_excel/123.xlsx"

    # 创建服务实例
    api_key = os.getenv("DASHSCOPE_API_KEY", "sk-4c89a24b73d24731b86bf26337398cef")
    service = SmartTranslationService(api_key)

    # 读取Excel文件
    excel_file = pd.ExcelFile(file_path)

    print("=" * 60)
    print("测试后端列检测功能")
    print("=" * 60)

    # 检查每个sheet
    for sheet_name in excel_file.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet_name)

        print(f"\nSheet: {sheet_name}")
        print(f"列: {list(df.columns)}")

        # 检测空列
        empty_columns = []
        non_empty_columns = []

        for col in df.columns:
            if df[col].isna().all() or (df[col].astype(str).str.strip() == '').all():
                empty_columns.append(col)
            else:
                non_empty_columns.append(col)

        print(f"非空列（源列）: {non_empty_columns}")
        print(f"空列（需要翻译）: {empty_columns}")

    # 测试服务的_identify_columns方法
    print("\n" + "=" * 60)
    print("测试SmartTranslationService._identify_columns方法")
    print("=" * 60)

    # 模拟第一个sheet的数据
    df = pd.read_excel(file_path, sheet_name=excel_file.sheet_names[0])

    # 调用私有方法进行测试
    columns_info = service._identify_columns(df, None)

    print(f"源列: {columns_info['source_column']}")
    print(f"目标列: {columns_info['target_columns']}")
    print(f"所有语言映射: {columns_info['lang_mapping']}")

if __name__ == "__main__":
    test_column_detection()