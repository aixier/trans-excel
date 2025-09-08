#!/usr/bin/env python3
"""
测试analyze/sheets API的语言检测功能
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目路径
project_path = Path(__file__).parent / "excel_processor" / "backend"
sys.path.insert(0, str(project_path))

# 设置环境变量
os.environ.setdefault('PYTHONPATH', str(project_path))

from fastapi import UploadFile
# 测试核心函数，不导入main
import tempfile
import shutil

async def test_analyze_sheets():
    """测试analyze_sheets函数"""
    
    # 测试文件路径
    test_file = Path("/mnt/d/work/trans_excel/text_BR.xlsx")
    
    if not test_file.exists():
        print(f"测试文件不存在: {test_file}")
        return
    
    print(f"测试文件: {test_file}")
    
    try:
        # 创建模拟的UploadFile
        with open(test_file, 'rb') as f:
            file_content = f.read()
        
        # 创建临时文件来模拟UploadFile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        # 模拟UploadFile对象
        class MockUploadFile:
            def __init__(self, file_path):
                self.filename = os.path.basename(file_path)
                self.file_path = file_path
            
            async def read(self):
                with open(self.file_path, 'rb') as f:
                    return f.read()
        
        mock_file = MockUploadFile(temp_file_path)
        
        # 调用analyze_sheets函数
        result = await analyze_sheets(mock_file)
        
        # 清理临时文件
        os.unlink(temp_file_path)
        
        # 打印结果
        print("=== API 测试结果 ===")
        print(f"状态码: {result.status_code}")
        
        if hasattr(result, 'body'):
            import json
            body = json.loads(result.body)
            print("响应内容:")
            print(json.dumps(body, ensure_ascii=False, indent=2))
            
            # 检查是否包含语言检测结果
            if 'detected_languages' in body:
                print(f"\n✅ 全局检测到的语言: {body['detected_languages']}")
            else:
                print("❌ 缺少全局语言检测结果")
            
            if 'sheet_info' in body:
                for sheet_name, sheet_data in body['sheet_info'].items():
                    if 'detected_languages' in sheet_data:
                        print(f"✅ Sheet '{sheet_name}' 检测到的语言: {sheet_data['detected_languages']}")
                    else:
                        print(f"❌ Sheet '{sheet_name}' 缺少语言检测结果")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_analyze_sheets())