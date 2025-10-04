#!/usr/bin/env python3
"""测试分析输出的JSON结构"""

import json
from services.excel_loader import ExcelLoader
from services.excel_analyzer import ExcelAnalyzer

def test_analysis_output():
    # 使用一个测试Excel文件
    test_file = "/mnt/d/work/trans_excel/test1.xlsx"  # 或其他可用的测试文件

    try:
        # 加载Excel
        loader = ExcelLoader()
        excel_df = loader.load_excel(test_file)

        # 分析
        analyzer = ExcelAnalyzer()
        analysis_result = analyzer.analyze(excel_df)

        # 打印JSON结构
        print("=" * 80)
        print("分析结果的JSON结构：")
        print("=" * 80)
        print(json.dumps(analysis_result, indent=2, ensure_ascii=False, default=str))

        print("\n" + "=" * 80)
        print("语言检测部分详情：")
        print("=" * 80)
        if 'language_detection' in analysis_result:
            lang_data = analysis_result['language_detection']
            print(f"源语言列表: {lang_data.get('source_langs', [])}")
            print(f"目标语言列表: {lang_data.get('target_langs', [])}")

            if 'sheet_details' in lang_data:
                for sheet in lang_data['sheet_details']:
                    print(f"\nSheet: {sheet['sheet_name']}")
                    print(f"  - 源语言: {sheet.get('source_languages', [])}")
                    print(f"  - 目标语言: {sheet.get('target_languages', [])}")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_analysis_output()