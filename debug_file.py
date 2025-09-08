#!/usr/bin/env python3
"""
调试sfdaf.xlsx文件的语言检测
"""

import pandas as pd
from pathlib import Path

def debug_file_analysis(file_path):
    """调试文件分析"""
    print(f"分析文件: {file_path}")
    
    try:
        excel_file = pd.ExcelFile(file_path)
        print(f"Sheets: {excel_file.sheet_names}")
        
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            print(f"\nSheet: {sheet_name}")
            print(f"  行数: {len(df)}")
            print(f"  列数: {len(df.columns)}")
            print(f"  列名原始: {df.columns.tolist()}")
            print(f"  列名大写: {[str(col).upper() for col in df.columns]}")
            
            # 显示前几行数据
            print("  前5行数据:")
            for i in range(min(5, len(df))):
                row_data = {}
                for col in df.columns:
                    value = df.iloc[i][col]
                    if pd.notna(value):
                        row_data[col] = str(value)[:50]  # 限制显示长度
                print(f"    行{i+1}: {row_data}")
            
            # 详细分析列名
            print("\n  列名语言检测分析:")
            for col in df.columns:
                col_str = str(col).upper()
                print(f"    '{col}' -> '{col_str}'")
                
                detected = []
                if ':CH:' in col_str or 'CHINESE' in col_str or '中文' in col_str or any(char in col_str for char in ['中', '文']):
                    detected.append('zh')
                if ':EN:' in col_str or 'ENGLISH' in col_str or '英文' in col_str or '英语' in col_str:
                    detected.append('en')
                if ':TR:' in col_str or 'TURKISH' in col_str or '土耳其' in col_str:
                    detected.append('tr')
                if ':PT:' in col_str or 'PORTUGUESE' in col_str or '葡萄牙' in col_str:
                    detected.append('pt')
                if col_str == 'CH':
                    detected.append('zh')
                if col_str == 'EN':
                    detected.append('en')
                if col_str == 'TR':
                    detected.append('tr')
                
                print(f"      检测到的语言: {detected}")
            
            # 分析内容
            print("\n  内容语言检测分析:")
            for col in df.columns:
                print(f"    列 '{col}':")
                sample_values = df[col].dropna().head(3)
                for idx, value in sample_values.items():
                    text = str(value)
                    detected_content = []
                    if any('\u4e00' <= char <= '\u9fff' for char in text):
                        detected_content.append('zh')
                    if any(char.isascii() and char.isalpha() for char in text):
                        if len(text.split()) > 1:
                            detected_content.append('en')
                    # 土耳其语特殊字符检测
                    turkish_chars = ['ğ', 'ü', 'ş', 'ı', 'ö', 'ç', 'Ğ', 'Ü', 'Ş', 'İ', 'Ö', 'Ç']
                    if any(char in text for char in turkish_chars):
                        detected_content.append('tr')
                    
                    print(f"      '{text[:30]}...' -> {detected_content}")
                    
    except Exception as e:
        print(f"文件分析失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_file = Path("/mnt/d/work/trans_excel/sfdaf.xlsx")
    if test_file.exists():
        debug_file_analysis(test_file)
    else:
        print(f"文件不存在: {test_file}")