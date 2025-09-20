# 当前系统问题分析

## 1. target_languages 参数问题

### 现状：
- `TranslationDetector.detect_translation_tasks()` 已经为每个任务检测了需要的目标语言
- 每个 `TranslationTask` 对象包含 `target_language` 属性（单数）
- 但翻译引擎仍在使用全局的 `target_languages` 参数（复数）

### 问题：
1. 系统试图一次性翻译到所有目标语言，而不是按需翻译
2. 如果文件有 PT、TH、IND 等多个语言列，系统会尝试全部翻译，即使某些列已经有内容

### 正确的流程应该是：
```python
# 当前错误的做法：
batch = [task1, task2, task3]  # 不同的任务可能需要不同的目标语言
translate_batch(batch, target_languages=['pt', 'th', 'ind'])  # 批量翻译到所有语言

# 正确的做法：
# 方案1：按目标语言分组批次
batches_by_lang = {
    'pt': [task1, task3],  # 需要翻译到PT的任务
    'th': [task2],          # 需要翻译到TH的任务
}

# 方案2：每个任务单独处理其目标语言
for task in batch:
    translate(task.source_text, task.target_language)
```

## 2. 批处理逻辑问题

### 当前实现：
```python
# translation_engine.py 第364行
system_prompt = self.localization_engine.create_batch_prompt(
    [task.source_text for task in batch],
    target_languages,  # 全局目标语言列表
    region_code,
    game_background,
    batch[0].task_type if batch else 'new'
)
```

### 问题：
- 假设批次中所有任务都要翻译到相同的目标语言
- 实际上不同任务可能需要不同的目标语言

## 3. 解决方案

### 方案A：按语言分组批次（推荐）
修改 `group_tasks_by_batch` 方法，按目标语言分组：
```python
def group_tasks_by_language_and_batch(tasks, batch_size):
    tasks_by_lang = {}
    for task in tasks:
        lang = task.target_language
        if lang not in tasks_by_lang:
            tasks_by_lang[lang] = []
        tasks_by_lang[lang].append(task)

    # 每个语言单独分批
    all_batches = []
    for lang, lang_tasks in tasks_by_lang.items():
        batches = group_into_batches(lang_tasks, batch_size)
        all_batches.extend(batches)
    return all_batches
```

### 方案B：修改翻译逻辑
让每个任务单独指定其目标语言，而不是批量处理。

## 4. 影响范围

需要修改的文件：
1. **translation_engine.py**
   - `_process_batches_concurrent_with_timeout()` - 移除target_languages参数
   - `_translate_batch_with_retry()` - 从batch中提取目标语言

2. **localization_engine.py**
   - `create_batch_prompt()` - 适配单一目标语言

3. **translation_detector.py**
   - 可能需要新增按语言分组的方法

## 5. 临时解决方案

如果不想大规模重构，可以：
1. 保持现有结构
2. 在检测时只返回真正需要翻译的语言
3. 确保不会重复翻译已有内容的列