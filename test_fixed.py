#!/usr/bin/env python3
"""
测试修复后的语言检测功能
"""

import pandas as pd
from pathlib import Path

def detect_languages_from_columns(columns):
    """从列名检测语言 (修复后的版本)"""
    detected = set()
    for col in columns:
        col_str = str(col).upper().strip()
        
        # 检测中文 (使用if而不是elif，允许多语言检测)
        if (':CH:' in col_str or 'CHINESE' in col_str or '中文' in col_str or 
            any(char in col_str for char in ['中', '文']) or col_str == 'CH' or col_str == 'ZH'):
            detected.add('zh')
        
        # 检测英文
        if (':EN:' in col_str or 'ENGLISH' in col_str or '英文' in col_str or 
            '英语' in col_str or col_str == 'EN' or col_str == 'ENG'):
            detected.add('en')
        
        # 检测葡萄牙语
        if (':PT:' in col_str or 'PORTUGUESE' in col_str or '葡萄牙' in col_str or 
            col_str == 'PT' or col_str == 'POR'):
            detected.add('pt')
        
        # 检测西班牙语
        if (':ES:' in col_str or 'SPANISH' in col_str or '西班牙' in col_str or 
            col_str == 'ES' or col_str == 'ESP'):
            detected.add('es')
        
        # 检测日语
        if (':JA:' in col_str or 'JAPANESE' in col_str or '日语' in col_str or 
            '日文' in col_str or col_str == 'JA' or col_str == 'JP' or col_str == 'JPN'):
            detected.add('ja')
        
        # 检测泰语
        if (':TH:' in col_str or 'THAI' in col_str or '泰语' in col_str or 
            '泰文' in col_str or col_str == 'TH'):
            detected.add('th')
        
        # 检测印尼语
        if (':IND:' in col_str or ':ID:' in col_str or 'INDONESIAN' in col_str or 
            '印尼' in col_str or col_str == 'ID' or col_str == 'IND'):
            detected.add('id')
        
        # 检测土耳其语
        if (':TR:' in col_str or 'TURKISH' in col_str or '土耳其' in col_str or 
            col_str == 'TR' or col_str == 'TUR'):
            detected.add('tr')
        
        # 检测韩语
        if (':KO:' in col_str or 'KOREAN' in col_str or '韩语' in col_str or 
            '韩文' in col_str or col_str == 'KO' or col_str == 'KR'):
            detected.add('ko')
            
    return detected

def test_file_analysis(file_path):
    """测试修复后的文件分析"""
    print(f"测试修复后的语言检测: {file_path}")
    
    try:
        excel_file = pd.ExcelFile(file_path)
        print(f"Sheets: {excel_file.sheet_names}")
        
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            print(f"\nSheet: {sheet_name}")
            print(f"  列名: {df.columns.tolist()}")
            
            # 测试修复后的列名检测
            detected_languages = detect_languages_from_columns(df.columns)
            print(f"  修复后检测到的语言: {sorted(list(detected_languages))}")
            
            # 详细分析每个列名
            for col in df.columns:
                col_str = str(col).upper().strip()
                print(f"    列 '{col}' -> '{col_str}'")
                
                matches = []
                if col_str == 'CH' or col_str == 'ZH':
                    matches.append('zh')
                if col_str == 'EN' or col_str == 'ENG':
                    matches.append('en')
                if col_str == 'TR' or col_str == 'TUR':
                    matches.append('tr')
                if col_str == 'PT' or col_str == 'POR':
                    matches.append('pt')
                if col_str == 'ES' or col_str == 'ESP':
                    matches.append('es')
                    
                print(f"      -> 匹配的语言: {matches}")
        
        # 生成完整的结果
        global_detected_languages = set()
        sheet_info = {}
        
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            sheet_languages = detect_languages_from_columns(df.columns)
            global_detected_languages.update(sheet_languages)
            
            sheet_info[sheet_name] = {
                "rows": len(df),
                "columns": len(df.columns),
                "detected_languages": sorted(list(sheet_languages))
            }
        
        result = {
            "sheets": list(excel_file.sheet_names),
            "sheet_info": sheet_info,
            "detected_languages": sorted(list(global_detected_languages))
        }
        
        print("\n=== 修复后的API响应 ===")
        import json
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        return result
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_file = Path("/mnt/d/work/trans_excel/123.xlsx")
    if test_file.exists():
        test_file_analysis(test_file)
    else:
        print(f"文件不存在: {test_file}")