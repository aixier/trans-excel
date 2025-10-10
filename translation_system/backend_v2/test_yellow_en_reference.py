"""测试黄色重翻新逻辑：EN作为参考源"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import PatternFill
from services.excel_loader import ExcelLoader
from services.task_splitter import TaskSplitter

print("=" * 80)
print("测试黄色重翻新逻辑：EN列双重角色")
print("=" * 80)

# 创建测试Excel（模拟）
test_data = {
    'CH': ['攻击力+100', '生命值不足', '防御力提升'],
    'EN': ['ATK+100', 'HP Low', None],  # 前两个有EN翻译，第三个没有
    'PT': [None, None, None]
}

df = pd.DataFrame(test_data)

print("\n模拟Excel:")
print(df)

# 场景1：CH标黄 + EN标黄（EN作为参考）
print("\n" + "=" * 80)
print("场景1：CH标黄 + EN标黄 → EN作为参考源")
print("=" * 80)

print("""
Excel状态:
  CH: 攻击力+100 🟨 (黄色)
  EN: ATK+100 🟨 (黄色，手动翻译了)
  PT: (空)

预期逻辑:
  ✅ CH标黄 → 需要重译
  ✅ EN标黄 → EN作为参考源（不生成EN任务）
  ✅ 只为PT生成任务
  ✅ 任务包含 reference_en='ATK+100'

预期Prompt:
  【原文】攻击力+100
  【英文参考】ATK+100 ← 注入
  请参考英文翻译成葡萄牙语
""")

# 场景2：CH标黄 + EN未标黄（EN也是目标）
print("\n" + "=" * 80)
print("场景2：CH标黄 + EN未标黄 → EN也是目标语言")
print("=" * 80)

print("""
Excel状态:
  CH: 防御力提升 🟨 (黄色)
  EN: (空，未手动翻译)
  PT: (空)

预期逻辑:
  ✅ CH标黄 → 需要重译
  ✅ EN未标黄 → EN也作为目标语言
  ✅ 为EN和PT都生成任务
  ✅ 任务不包含reference_en

预期Prompt:
  【原文】防御力提升
  （无英文参考）
  请翻译成英文/葡萄牙语
""")

# 场景对比
print("\n" + "=" * 80)
print("场景对比总结:")
print("=" * 80)

print("""
┌────────────┬────────────┬────────────┬────────────────────────┐
│ CH状态     │ EN状态     │ EN角色     │ 生成的任务             │
├────────────┼────────────┼────────────┼────────────────────────┤
│ 🟨 标黄    │ 🟨 标黄    │ 参考源     │ 只生成PT/TH/VN任务     │
│            │            │            │ + reference_en         │
├────────────┼────────────┼────────────┼────────────────────────┤
│ 🟨 标黄    │ ⚪ 未标黄  │ 目标语言   │ 生成EN/PT/TH/VN任务    │
│            │            │            │ 无reference_en         │
├────────────┼────────────┼────────────┼────────────────────────┤
│ ⚪ 未标黄  │ -          │ 目标语言   │ 正常翻译（空格填充）   │
└────────────┴────────────┴────────────┴────────────────────────┘

关键判断:
  if CH标黄 and EN标黄:
      EN = 参考源 → reference_en字段
  else:
      EN = 目标语言 → 正常任务
""")

print("\n✅ 逻辑设计完成")
print("   修改文件:")
print("   1. models/task_dataframe.py - 添加reference_en字段")
print("   2. services/task_splitter.py - 检测EN黄色并跳过EN任务")
print("   3. services/llm/prompt_template.py - 双源语言Prompt")
print("   4. services/executor/batch_executor.py - 传递reference_en")
