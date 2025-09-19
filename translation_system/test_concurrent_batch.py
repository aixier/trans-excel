#!/usr/bin/env python3
"""
智能并发批量翻译 - 简化版
- 支持命令行 -f 参数指定输入文件
- 智能识别需要翻译的行（完全空的和部分空的）
- 每次LLM翻译20行，5个LLM并发
- 单批次失败重试2次，失败后继续后续批次
- 确保190行都完成翻译
- 输出文件名 = 输入文件名 + 完成时间戳
"""

import os
import json
import pandas as pd
import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv
import time
from datetime import datetime
import random
import argparse

load_dotenv("/mnt/d/work/trans_excel/.env")

API_KEY = os.getenv("DASHSCOPE_API_KEY")
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL = "qwen-plus"
BATCH_SIZE = 3  # 每批处理3行
MAX_CONCURRENT = 10  # 最大10个并发
TOTAL_ROWS = 190  # 提取前190行
MAX_RETRY_ATTEMPTS = 2  # 单批次最大重试2次
RETRY_BASE_DELAY = 3  # 重试基础延迟(秒)

class CompletionTranslator:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL)
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT)
        self.completed_batches = 0
        self.total_batches = 0
        self.failed_batches = []

    def create_translation_prompt(self):
        """创建翻译提示词"""
        return """你是专业的多语言翻译专家。将中文翻译成葡萄牙语、泰语、印尼语。

返回JSON格式：
{
  "translations": [
    {
      "id": "text_0",
      "original_text": "原文",
      "pt": "葡萄牙语翻译",
      "th": "泰语翻译",
      "ind": "印尼语翻译"
    }
  ]
}

要求：
1. 保持原文的语义和语气
2. 使用准确的术语翻译
3. 返回纯JSON格式，不要其他内容"""

    async def translate_batch_with_retry(self, batch_data, batch_id):
        """带重试机制的异步翻译单个批次"""
        async with self.semaphore:
            start_time = time.time()
            print(f"📦 批次{batch_id}: 开始处理 {len(batch_data)}行 [并发槽位已占用]")

            # 准备输入数据
            input_texts = []
            for i, (_, text) in enumerate(batch_data):
                input_texts.append({
                    "id": f"batch_{batch_id}_text_{i}",
                    "text": text
                })

            # 重试机制 - 最多2次重试
            for attempt in range(MAX_RETRY_ATTEMPTS + 1):
                try:
                    # 添加随机延迟避免同时重试
                    if attempt > 0:
                        retry_delay = RETRY_BASE_DELAY * (2 ** (attempt - 1)) + random.uniform(0, 2)
                        print(f"🔄 批次{batch_id}: 第{attempt + 1}次尝试，延迟{retry_delay:.1f}s后重试...")
                        await asyncio.sleep(retry_delay)

                    # 构建请求消息
                    messages = [
                        {"role": "system", "content": self.create_translation_prompt()},
                        {"role": "user", "content": f"请翻译以下中文文本：\n{json.dumps(input_texts, ensure_ascii=False, indent=2)}"}
                    ]

                    # 显示请求原始数据
                    print(f"🔗 批次{batch_id} API请求原始数据:")
                    print(f"   模型: {MODEL}")
                    print(f"   消息数: {len(messages)}")
                    print(f"   System prompt: {messages[0]['content']}")
                    print(f"   User content : {messages[1]['content']}")
                    print()

                    # 调用API
                    response = await self.client.chat.completions.create(
                        model=MODEL,
                        messages=messages,
                        temperature=0.3,
                        max_tokens=4000,
                        response_format={"type": "json_object"},
                        timeout=90  # 增加超时设置
                    )

                    # 显示响应原始数据
                    print(f"📥 批次{batch_id} API响应原始数据:")
                    print(f"   状态: 成功")
                    print(f"   模型: {response.model}")
                    print(f"   Token使用: {response.usage.total_tokens} (prompt: {response.usage.prompt_tokens}, completion: {response.usage.completion_tokens})")
                    print(f"   响应内容 (前300字符): {response.choices[0].message.content[:300]}...")
                    print()

                    result = json.loads(response.choices[0].message.content)
                    translations = result.get("translations", [])

                    # 处理结果
                    batch_results = {}
                    for i, translation in enumerate(translations):
                        if i < len(batch_data):
                            original_idx = batch_data[i][0]
                            batch_results[original_idx] = {
                                'pt': translation.get('pt', ''),
                                'th': translation.get('th', ''),
                                'ind': translation.get('ind', '')
                            }

                    elapsed = time.time() - start_time
                    self.completed_batches += 1

                    retry_info = f" (第{attempt + 1}次尝试)" if attempt > 0 else ""
                    print(f"✅ 批次{batch_id}: 完成翻译{retry_info} {len(translations)}条 | "
                          f"耗时{elapsed:.1f}s | tokens: {response.usage.total_tokens} | "
                          f"进度: {self.completed_batches}/{self.total_batches}")

                    return batch_results

                except Exception as e:
                    elapsed = time.time() - start_time

                    if attempt < MAX_RETRY_ATTEMPTS:
                        print(f"⚠️ 批次{batch_id}: 第{attempt + 1}次尝试失败 | 错误: {e}")
                    else:
                        print(f"❌ 批次{batch_id}: 重试{MAX_RETRY_ATTEMPTS}次后最终失败 | 总耗时{elapsed:.1f}s | 错误: {e}")
                        self.failed_batches.append(batch_id)

            return {}  # 重试失败，返回空结果，继续处理后续批次

def load_smart_data(file_path):
    """智能加载数据 - 支持不同类型的文件"""

    print(f"🔍 智能文件检测: {file_path}")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    df = pd.read_excel(file_path)
    print(f"📁 加载文件: {file_path}")
    print(f"   总行数: {len(df)}行")
    print(f"   列名: {list(df.columns)}")

    # 确保取前190行
    df = df.head(TOTAL_ROWS).copy()
    print(f"   处理数据: {len(df)}行")

    # 确保翻译列存在
    for col in ['PT', 'TH', 'IND']:
        if col not in df.columns:
            df[col] = ''

    # 分析翻译状态
    def count_translated(column):
        if column not in df.columns:
            return 0
        return df[column].notna().sum() - (df[column] == '').sum()

    pt_count = count_translated('PT')
    th_count = count_translated('TH')
    ind_count = count_translated('IND')
    total_translated = pt_count + th_count + ind_count
    total_possible = len(df) * 3

    print(f"   📊 翻译状态分析:")
    print(f"     葡萄牙语(PT): {pt_count}/{len(df)} 行")
    print(f"     泰语(TH): {th_count}/{len(df)} 行")
    print(f"     印尼语(IND): {ind_count}/{len(df)} 行")
    print(f"     总完成度: {total_translated}/{total_possible} ({total_translated/total_possible*100:.1f}%)")

    if total_translated == total_possible:
        print("   ✅ 所有翻译已完成！")
        return df, []
    else:
        print(f"   ⚠️  发现 {total_possible - total_translated} 个缺失翻译，将进行补充")
        return df, find_missing_translations(df)

def find_missing_translations(df):
    """找出需要翻译的行"""
    def is_translated(value):
        return pd.notna(value) and str(value).strip() != '' and str(value) != 'nan'

    missing_translations = []

    for idx, row in df.iterrows():
        pt_missing = not is_translated(row.get('PT'))
        th_missing = not is_translated(row.get('TH'))
        ind_missing = not is_translated(row.get('IND'))

        # 如果任何一个语言缺失，就需要重新翻译该行
        if pt_missing or th_missing or ind_missing:
            missing_translations.append({
                'index': idx,
                'chinese': row['CH'],
                'missing_languages': {
                    'pt': pt_missing,
                    'th': th_missing,
                    'ind': ind_missing
                }
            })

    return missing_translations

def create_translation_batches(missing_translations):
    """将缺失翻译转换为批次数据"""
    # 按批次大小分组
    batches = []
    for i in range(0, len(missing_translations), BATCH_SIZE):
        batch = missing_translations[i:i + BATCH_SIZE]
        # 转换为 (index, chinese_text) 格式
        batch_data = [(item['index'], item['chinese']) for item in batch]
        batches.append(batch_data)

    return batches

def generate_output_filename(input_file):
    """生成输出文件名: 清理基础名称 + 完成时间戳"""
    # 获取文件名（不含路径和扩展名）
    base_name = os.path.splitext(os.path.basename(input_file))[0]

    # 清理基础名称，移除之前的completed和时间戳部分
    # 匹配模式：_completed_YYYYMMDD_HHMMSS
    import re
    clean_base = re.sub(r'_completed_\d{8}_\d{6}', '', base_name)

    # 如果清理后为空或者太短，使用原始名称的前部分
    if len(clean_base) < 3:
        # 取原始名称的前面部分，最多20个字符
        clean_base = base_name.split('_')[0][:20]

    # 生成时间戳
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 生成输出文件名
    output_filename = f"{clean_base}_completed_{timestamp}.xlsx"

    return output_filename

async def run_translation(missing_translations, translator):
    """执行翻译任务"""
    if not missing_translations:
        print("🎉 所有翻译都已完成，无需进一步处理！")
        return {}

    translation_batches = create_translation_batches(missing_translations)

    print(f"🚀 开始智能翻译...")
    print(f"   📊 需要翻译行数: {len(missing_translations)}")
    print(f"   📦 分成批次数: {len(translation_batches)}")
    print()

    # 手动处理批次
    all_translations = {}
    translator.total_batches = len(translation_batches)

    # 执行翻译
    start_time = time.time()
    print(f"🎯 {datetime.now().strftime('%H:%M:%S')} 开始翻译...")

    tasks = []
    for batch_id, batch_data in enumerate(translation_batches, 1):
        tasks.append(translator.translate_batch_with_retry(batch_data, batch_id))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 合并结果
    for result in results:
        if isinstance(result, dict):
            all_translations.update(result)

    elapsed = time.time() - start_time
    successful_batches = sum(1 for r in results if isinstance(r, dict) and r)

    print()
    print(f"🏁 {datetime.now().strftime('%H:%M:%S')} 翻译完成!")
    print(f"   ⏱️  总耗时: {elapsed:.1f}秒")
    print(f"   📊 成功批次: {successful_batches}/{len(translation_batches)}")
    print(f"   📝 新增翻译: {len(all_translations)}行")

    return all_translations

async def test_llm_connection():
    """测试LLM连接"""
    print("🔧 测试LLM连接...")

    try:
        client = AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL)

        # 测试简单请求
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": "hello"}],
            max_tokens=50
        )

        print(f"✅ LLM连接测试成功:")
        print(f"   模型: {response.model}")
        print(f"   响应: {response.choices[0].message.content}")
        print(f"   Token使用: {response.usage.total_tokens} (prompt: {response.usage.prompt_tokens}, completion: {response.usage.completion_tokens})")
        print()

        return True

    except Exception as e:
        print(f"❌ LLM连接测试失败: {e}")
        return False

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='智能并发翻译工具')
    parser.add_argument('-f', '--file', required=True, help='输入Excel文件路径')
    args = parser.parse_args()

    input_file = args.file

    print("🔵 智能并发翻译 - 简化版")
    print(f"📋 配置信息:")
    print(f"   目标行数: {TOTAL_ROWS}")
    print(f"   批次大小: {BATCH_SIZE}行/批次")
    print(f"   并发数: {MAX_CONCURRENT}")
    print(f"   重试次数: {MAX_RETRY_ATTEMPTS}")
    print(f"   模型: {MODEL}")
    print(f"   API地址: {BASE_URL}")
    print(f"   输入文件: {input_file}")
    print("=" * 70)

    # 先测试LLM连接
    print("🔧 初始化测试...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        connection_ok = loop.run_until_complete(test_llm_connection())
        if not connection_ok:
            print("❌ LLM连接失败，无法继续执行翻译任务")
            return
    finally:
        loop.close()

    try:
        # 智能加载数据
        df, missing_translations = load_smart_data(input_file)

        if not missing_translations:
            print("🎉 所有翻译都已完成，无需进一步处理！")
            return

        print(f"📊 翻译任务分析:")
        print(f"   数据总行数: {len(df)}")
        print(f"   需要翻译: {len(missing_translations)}行")
        print()

        # 显示需要翻译的行（前5行示例）
        print("📋 需要翻译的行 (前5行示例):")
        for i, item in enumerate(missing_translations[:5]):
            missing_langs = [lang for lang, is_missing in item['missing_languages'].items() if is_missing]
            print(f"   行{item['index']+1}: {item['chinese']} -> 缺失: {', '.join(missing_langs)}")

        if len(missing_translations) > 5:
            print(f"   ... 还有 {len(missing_translations) - 5} 行需要翻译")
        print()

        # 检查数据有效性
        has_content = df['CH'].notna() & (df['CH'].astype(str).str.strip() != '')
        valid_rows = has_content.sum()

        if valid_rows == 0:
            print("❌ 没有有效的中文数据需要翻译")
            return

        # 执行并发翻译
        translator = CompletionTranslator()

        # 使用asyncio运行异步任务
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            translations = loop.run_until_complete(run_translation(missing_translations, translator))
        finally:
            loop.close()

        # 写回结果
        print(f"💾 更新翻译结果...")
        result_df = df.copy()

        # 确保列存在且为正确类型
        for col in ['PT', 'TH', 'IND']:
            if col not in result_df.columns:
                result_df[col] = ''
            result_df[col] = result_df[col].astype('object')

        # 填充新翻译
        filled_count = 0
        for idx, translation in translations.items():
            if idx < len(result_df):
                result_df.at[idx, 'PT'] = translation.get('pt', '')
                result_df.at[idx, 'TH'] = translation.get('th', '')
                result_df.at[idx, 'IND'] = translation.get('ind', '')
                filled_count += 1

        # 生成输出文件名
        output_path = generate_output_filename(input_file)
        result_df.to_excel(output_path, index=False)

        # 最终统计
        def count_final_translated(column):
            return result_df[column].notna().sum() - (result_df[column] == '').sum()

        final_pt = count_final_translated('PT')
        final_th = count_final_translated('TH')
        final_ind = count_final_translated('IND')
        total_final = final_pt + final_th + final_ind
        total_possible = len(result_df) * 3

        print(f"✅ 智能翻译完成!")
        print(f"   📄 输出文件: {output_path}")
        print(f"   📊 本次新增: {filled_count * 3}个翻译")
        print(f"   🎯 最终完成度: {total_final}/{total_possible} ({total_final/total_possible*100:.1f}%)")
        print()

        # 显示翻译示例
        if filled_count > 0:
            print("📋 翻译示例 (前3行):")
            translated_indices = list(translations.keys())
            sample_count = min(3, len(translated_indices))

            for i in range(sample_count):
                idx = translated_indices[i]
                row = result_df.iloc[idx]
                print(f"   行{idx+1}. 中文: {row['CH']}")
                print(f"      葡语: {row['PT']}")
                print(f"      泰语: {row['TH']}")
                print(f"      印尼: {row['IND']}")
                print()

        print(f"🎉 处理完成! 输出文件: {output_path}")

    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()