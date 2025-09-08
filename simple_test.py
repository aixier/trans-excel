#!/usr/bin/env python3
"""
简单测试语言检测功能
"""

import pandas as pd
from pathlib import Path

def detect_languages_from_columns(columns):
    """从列名检测语言"""
    detected = set()
    for col in columns:
        col_str = str(col).upper()
        # 检测中文
        if ':CH:' in col_str or 'CHINESE' in col_str or '中文' in col_str or any(char in col_str for char in ['中', '文']):
            detected.add('zh')
        # 检测英文
        elif ':EN:' in col_str or 'ENGLISH' in col_str or '英文' in col_str or '英语' in col_str:
            detected.add('en')
        # 检测葡萄牙语
        elif ':PT:' in col_str or 'PORTUGUESE' in col_str or '葡萄牙' in col_str:
            detected.add('pt')
        # 检测西班牙语
        elif ':ES:' in col_str or 'SPANISH' in col_str or '西班牙' in col_str:
            detected.add('es')
        # 检测日语
        elif ':JA:' in col_str or 'JAPANESE' in col_str or '日语' in col_str or '日文' in col_str:
            detected.add('ja')
        # 检测泰语
        elif ':TH:' in col_str or 'THAI' in col_str or '泰语' in col_str or '泰文' in col_str:
            detected.add('th')
        # 检测印尼语
        elif ':IND:' in col_str or ':ID:' in col_str or 'INDONESIAN' in col_str or '印尼' in col_str:
            detected.add('id')
        # 检测土耳其语
        elif ':TR:' in col_str or 'TURKISH' in col_str or '土耳其' in col_str:
            detected.add('tr')
        # 检测韩语
        elif ':KO:' in col_str or 'KOREAN' in col_str or '韩语' in col_str or '韩文' in col_str:
            detected.add('ko')
    return detected

def detect_languages_from_content(df, sample_rows=5):
    """从内容检测语言（基于字符特征）"""
    detected = set()
    if len(df) == 0:
        return detected
    
    # 只检查前几行以提高性能
    sample_df = df.head(sample_rows)
    
    for col in sample_df.columns:
        for _, value in sample_df[col].items():
            if pd.isna(value):
                continue
            text = str(value)
            if len(text.strip()) == 0:
                continue
            
            # 检测中文字符
            if any('\u4e00' <= char <= '\u9fff' for char in text):
                detected.add('zh')
            # 检测日文假名
            elif any('\u3040' <= char <= '\u309f' or '\u30a0' <= char <= '\u30ff' for char in text):
                detected.add('ja')
            # 检测韩文
            elif any('\uac00' <= char <= '\ud7af' for char in text):
                detected.add('ko')
            # 检测泰文
            elif any('\u0e00' <= char <= '\u0e7f' for char in text):
                detected.add('th')
            # 基本拉丁字母（可能是英语、葡语、西语等）
            elif any(char.isascii() and char.isalpha() for char in text):
                # 暂时标记为英语，更精确的检测需要NLP库
                if len(text.split()) > 1:  # 只有多个单词才认为可能是英语
                    detected.add('en')
    
    return detected

def test_file_analysis(file_path):
    """测试文件分析"""
    print(f"分析文件: {file_path}")
    
    try:
        excel_file = pd.ExcelFile(file_path)
        print(f"Sheets: {excel_file.sheet_names}")
        
        global_detected_languages = set()
        sheet_info = {}
        
        for sheet_name in excel_file.sheet_names:
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                print(f"\nSheet: {sheet_name}")
                print(f"  行数: {len(df)}")
                print(f"  列数: {len(df.columns)}")
                print(f"  列名: {list(df.columns)}")
                
                # 从列名检测语言
                column_languages = detect_languages_from_columns(df.columns)
                print(f"  从列名检测到的语言: {sorted(list(column_languages))}")
                
                # 从内容检测语言
                content_languages = detect_languages_from_content(df, sample_rows=3)
                print(f"  从内容检测到的语言: {sorted(list(content_languages))}")
                
                # 合并检测结果
                sheet_languages = column_languages.union(content_languages)
                global_detected_languages.update(sheet_languages)
                print(f"  该Sheet最终检测到的语言: {sorted(list(sheet_languages))}")
                
                # 显示前几行数据样本
                if len(df) > 0:
                    print("  前3行数据样本:")
                    for i, (idx, row) in enumerate(df.head(3).iterrows()):
                        print(f"    行{idx+1}: {dict(row)}")
                        if i >= 2:  # 限制显示行数
                            break
                
                sheet_info[sheet_name] = {
                    "rows": len(df),
                    "columns": len(df.columns),
                    "detected_languages": sorted(list(sheet_languages))
                }
            except Exception as e:
                print(f"  错误: {e}")
                sheet_info[sheet_name] = {
                    "rows": 0,
                    "columns": 0,
                    "detected_languages": [],
                    "error": str(e)
                }
        
        print(f"\n=== 分析结果 ===")
        print(f"全局检测到的语言: {sorted(list(global_detected_languages))}")
        
        # 模拟API响应
        result = {
            "sheets": list(excel_file.sheet_names),
            "sheet_info": sheet_info,
            "detected_languages": sorted(list(global_detected_languages))
        }
        
        import json
        print("\n=== 模拟API响应 ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        return result
        
    except Exception as e:
        print(f"文件分析失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # 测试文件
    test_file = Path("/mnt/d/work/trans_excel/text_BR.xlsx")
    if test_file.exists():
        test_file_analysis(test_file)
    else:
        print(f"测试文件不存在: {test_file}")
        
        # 列出可用的xlsx文件
        excel_files = list(Path("/mnt/d/work/trans_excel").glob("*.xlsx"))
        if excel_files:
            print("可用的Excel文件:")
            for f in excel_files:
                print(f"  {f}")
            print(f"使用第一个文件进行测试: {excel_files[0]}")
            test_file_analysis(excel_files[0])