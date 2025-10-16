# 独立模块测试页面

## 📋 概述

这是一套**完全独立**的模块测试页面，每个页面代表管道架构中的**一个转换阶段**。

### 设计理念

✅ **禁止综合测试** - 每个模块完全独立
✅ **Session ID连接** - 模块间唯一连接方式
✅ **架构原则遵循** - 严格符合 `ARCHITECTURE_PRINCIPLES.md`
✅ **独立可测试** - 任何阶段都可以单独运行

---

## 🏗️ 架构原则

遵循 `/mnt/d/work/trans_excel/translation_system_v2/.claude/ARCHITECTURE_PRINCIPLES.md`:

```
数据状态N → [拆分器] → 任务表 → [转换器] → 数据状态N+1
```

**核心原则**:
- **数据状态连续性**: 原始数据 = 结果数据 = 数据状态（无区别）
- **任务表唯一中间数据**: TaskDataFrame 描述如何从状态N变成状态N+1
- **无限链式支持**: 任何输出状态都可以作为下一个转换的输入
- **拆分器与转换器分离**: 任务拆分和执行转换完全独立

---

## 📁 文件结构

```
test_pages/
├── index.html                      # 导航页 + 架构说明
├── 1_upload_and_split.html         # 阶段1: 上传 + 拆分
├── 2_execute_transformation.html   # 阶段2: 执行转换
├── 3_download_results.html         # 阶段3: 下载结果
├── 4_caps_transformation.html      # 阶段4: CAPS大写转换（链式）
└── README.md                       # 本文档
```

---

## 🔬 测试页面详解

### 🎯 阶段1: 上传文件 + 任务拆分
**文件**: `1_upload_and_split.html`

**架构阶段**: `CREATED → INPUT_LOADED → SPLIT_COMPLETE`

**输入**: Excel文件（数据状态0）
**输出**: Session ID（包含任务表）

**架构实现**:
```
数据状态0 → [拆分器] → 任务表
```

**测试内容**:
- 上传Excel文件并加载为数据状态0
- 根据 `rule_set` 拆分任务
  - `translation`: 标准翻译任务（空单元格、黄色重翻、蓝色缩短、普通翻译）
  - `caps_only`: 仅CAPS表格的大写转换任务
- 提取上下文信息（可选）
- 生成任务表（描述转换指令）

**API端点**: `POST /api/tasks/split`

**返回**: Session ID（用于阶段2）

---

### ⚡ 阶段2: 执行转换
**文件**: `2_execute_transformation.html`

**架构阶段**: `SPLIT_COMPLETE → EXECUTING → COMPLETED`

**输入**: Session ID（来自阶段1，包含任务表）
**输出**: Session ID（数据状态1）

**架构实现**:
```
任务表 → [转换器] → 数据状态1
```

**测试内容**:
- 从阶段1获取Session ID
- 自动选择或手动指定Processor
  - `rule_set=translation` → `processor=llm_qwen`（LLM翻译）
  - `rule_set=caps_only` → `processor=uppercase`（大写转换）
- 执行转换并实时监控进度
- 生成数据状态1

**API端点**:
- `POST /api/execute/start` - 开始执行
- `GET /api/execute/status/{session_id}` - 状态轮询

**返回**: 完成的Session ID（用于阶段3或阶段4）

---

### 📥 阶段3: 下载结果
**文件**: `3_download_results.html`

**架构阶段**: `COMPLETED → 导出Excel文件`

**输入**: Session ID（来自阶段2，stage=COMPLETED）
**输出**: Excel文件（物理文件）

**架构实现**:
```
数据状态N → [导出器] → Excel文件
```

**测试内容**:
- 从阶段2获取完成的Session ID
- 检查Session状态和统计信息
- 导出Excel文件（保留格式、颜色、批注）
- 下载的文件可作为新的数据状态0

**API端点**:
- `GET /api/execute/status/{session_id}` - 检查状态
- `GET /api/download/{session_id}` - 下载文件

**返回**: 下载的Excel文件

---

### 🔤 阶段4: CAPS大写转换（链式）
**文件**: `4_caps_transformation.html`

**架构阶段**: `数据状态1 → 数据状态2`（第二次转换）

**输入**: Parent Session ID（来自阶段2，数据状态1）
**输出**: New Session ID（数据状态2）

**架构实现**:
```
数据状态1 → [拆分器(CAPS)] → 任务表2 → [大写转换器] → 数据状态2
```

**测试内容**:
- 从阶段2获取Parent Session ID
- 创建子Session并继承数据状态1（通过 `parent_session_id`）
- 拆分CAPS任务（`rule_set=caps_only`）
- 执行大写转换（`processor=uppercase`）
- 演示无限链式转换能力

**API端点**:
- `POST /api/tasks/split` (with `parent_session_id`) - 创建子Session并拆分
- `POST /api/execute/start` - 执行转换
- `GET /api/tasks/split/status/{session_id}` - 拆分状态
- `GET /api/execute/status/{session_id}` - 执行状态

**返回**: New Session ID（可再次链接到阶段3下载）

**链式示例**:
```
Session1: 状态0 → [翻译] → 状态1
          ↓ (parent_session_id)
Session2: 状态1 → [大写] → 状态2
          ↓ (parent_session_id)
Session3: 状态2 → [其他] → 状态3
          ...
```

---

## 🔄 工作流程

### 基础工作流（翻译）
```
1. 阶段1: 上传Excel，rule_set=translation
   → 获得 Session ID (A)

2. 阶段2: 使用Session ID (A)，processor=llm_qwen
   → Session ID (A) 状态变为COMPLETED

3. 阶段3: 使用Session ID (A)
   → 下载翻译后的Excel文件
```

### 链式工作流（翻译 + 大写）
```
1. 阶段1: 上传Excel，rule_set=translation
   → 获得 Session ID (A)

2. 阶段2: 使用Session ID (A)，processor=llm_qwen
   → Session ID (A) 状态变为COMPLETED（包含数据状态1）

3. 阶段4: parent_session_id=Session ID (A)
   → 创建 Session ID (B)
   → 拆分CAPS任务
   → 执行大写转换
   → Session ID (B) 状态变为COMPLETED（包含数据状态2）

4. 阶段3: 使用Session ID (B)
   → 下载包含 翻译+大写 的Excel文件
```

### 仅CAPS工作流（大写转换）
```
1. 阶段1: 上传Excel，rule_set=caps_only
   → 获得 Session ID (A)

2. 阶段2: 使用Session ID (A)，processor=uppercase
   → Session ID (A) 状态变为COMPLETED

3. 阶段3: 使用Session ID (A)
   → 下载大写转换后的Excel文件
```

---

## 🎯 独立性验证

### ✅ 每个阶段可以单独测试

**阶段1独立测试**:
- 上传文件 → 查看拆分结果 → 检查任务表
- 不需要执行阶段2

**阶段2独立测试**:
- 使用历史Session ID → 执行转换 → 监控进度
- 不需要重新上传文件

**阶段3独立测试**:
- 使用历史Session ID → 下载结果
- 不需要重新执行转换

**阶段4独立测试**:
- 使用历史Parent Session → 创建子Session → 执行CAPS
- 演示链式能力

### ✅ Session ID是唯一连接

```
阶段1 ──Session ID──> 阶段2
            ↓
      (手动复制粘贴)
            ↓
阶段2 ──Session ID──> 阶段3
            ↓
阶段2 ──Session ID──> 阶段4 ──Session ID──> 阶段3
    (parent_session_id)       (new_session_id)
```

### ✅ 状态机严格检查

- 阶段2要求: `stage=SPLIT_COMPLETE`
- 阶段3要求: `stage=COMPLETED`
- 阶段4要求: Parent Session `stage=COMPLETED`

### ✅ 职责清晰分离

| 阶段 | 职责 | 不负责 |
|-----|------|--------|
| 阶段1 | 上传、拆分 | 执行转换 |
| 阶段2 | 执行转换 | 拆分任务、下载 |
| 阶段3 | 下载导出 | 拆分、执行 |
| 阶段4 | 链式转换 | 原始上传 |

---

## 🧪 测试建议

### 测试场景1: 验证拆分器
```bash
1. 打开 1_upload_and_split.html
2. 上传测试Excel文件
3. rule_set=translation
4. 查看API响应中的任务表结构
5. 验证任务类型、字符数统计
```

### 测试场景2: 验证转换器
```bash
1. 从阶段1获取Session ID
2. 打开 2_execute_transformation.html
3. 粘贴Session ID
4. processor=llm_qwen（或自动选择）
5. 监控实时进度
6. 验证成功/失败统计
```

### 测试场景3: 验证导出器
```bash
1. 从阶段2获取完成的Session ID
2. 打开 3_download_results.html
3. 粘贴Session ID
4. 检查统计信息
5. 下载文件并验证格式、内容
```

### 测试场景4: 验证链式能力
```bash
1. 完成阶段1和阶段2（翻译）
2. 打开 4_caps_transformation.html
3. 粘贴Parent Session ID
4. 创建子Session并拆分CAPS任务
5. 执行大写转换
6. 获得New Session ID
7. 使用阶段3下载最终结果
8. 验证包含 翻译+大写 两次转换
```

---

## 🚀 快速开始

### 1. 启动后端服务
```bash
cd /mnt/d/work/trans_excel/translation_system_v2/backend_v2
python main.py
```

默认运行在: `http://localhost:8013`

### 2. 打开导航页
```
浏览器打开: test_pages/index.html
```

### 3. 选择测试场景
- **基础翻译**: 阶段1 → 阶段2 → 阶段3
- **链式转换**: 阶段1 → 阶段2 → 阶段4 → 阶段3
- **仅大写**: 阶段1(caps_only) → 阶段2(uppercase) → 阶段3

### 4. 手动复制Session ID
每个阶段完成后，点击Session ID复制到剪贴板，然后粘贴到下一个阶段。

---

## 📊 架构合规性

### ✅ 数据状态连续性
- `input_state` 和 `output_state` 相同类型（`ExcelDataFrame`）
- 任何输出都可以作为下一个输入
- 支持无限链接（`parent_session_id`）

### ✅ 任务表唯一中间数据
- 任务表（`TaskDataFrameManager`）独立于数据状态
- 描述如何从状态N变成状态N+1
- 可以被保存、恢复、重放

### ✅ 统一转换流程
```
CREATED → INPUT_LOADED → SPLIT_COMPLETE → EXECUTING → COMPLETED
   ↓           ↓              ↓               ↓            ↓
 创建      加载状态N      生成任务表       执行转换    状态N+1就绪
```

### ✅ 拆分器与转换器分离
- 阶段1: 只拆分，不执行
- 阶段2: 只执行，不拆分
- 阶段4: 重新拆分（新规则），再执行

---

## 🔍 API端点对照

| 阶段 | API端点 | 方法 | 作用 |
|-----|---------|------|------|
| 阶段1 | `/api/tasks/split` | POST | 上传文件并拆分任务 |
| 阶段1 | `/api/tasks/split/status/{session_id}` | GET | 查询拆分状态 |
| 阶段2 | `/api/execute/start` | POST | 开始执行转换 |
| 阶段2 | `/api/execute/status/{session_id}` | GET | 查询执行状态 |
| 阶段3 | `/api/download/{session_id}` | GET | 下载结果文件 |
| 阶段4 | `/api/tasks/split` (with parent_session_id) | POST | 创建子Session并拆分 |

---

## 📝 注意事项

### 1. Session ID必须手动传递
- ✅ 这是**设计特性**，不是Bug
- ✅ 确保每个阶段**完全独立**
- ✅ 便于测试特定阶段
- ❌ 不提供自动跳转到下一阶段

### 2. 状态检查严格
- 阶段2要求: `stage=SPLIT_COMPLETE`
- 阶段3要求: `stage=COMPLETED`
- 如果状态不符，会显示错误

### 3. 后端地址可配置
每个页面顶部都有"后端地址"输入框，默认 `http://localhost:8013`

### 4. 实时进度监控
- 阶段1: 拆分进度（百分比）
- 阶段2: 执行进度（任务完成数/总任务数）
- 阶段4: 拆分进度 + 执行进度

### 5. 错误处理
- 显示详细错误信息
- API响应完整展示（JSON格式）
- 便于调试和问题定位

---

## 🎨 UI设计

### 颜色区分
- **阶段1**: 紫色渐变（Purple Gradient）
- **阶段2**: 橙色渐变（Orange Gradient）
- **阶段3**: 粉色渐变（Pink Gradient）
- **阶段4**: 蓝色渐变（Blue Gradient）

### 共同特征
- 清晰的架构原则说明
- 实时状态更新
- 进度条显示
- 响应JSON展示
- Session ID一键复制

---

## 🧩 扩展性

### 添加新阶段
如需添加新的转换阶段（如阶段5、阶段6...），只需:

1. 创建新HTML文件（如 `5_new_transformation.html`）
2. 遵循相同模式:
   ```
   输入: Parent Session ID
   处理: 创建子Session → 拆分任务 → 执行转换
   输出: New Session ID
   ```
3. 更新 `index.html` 添加导航链接

### 添加新Processor
在阶段2或阶段4的Processor选择器中添加新选项即可。

### 添加新Rule Set
在阶段1的规则集选择器中添加新选项，后端需对应实现。

---

## 📚 参考文档

- **架构原则**: `/mnt/d/work/trans_excel/translation_system_v2/.claude/ARCHITECTURE_PRINCIPLES.md`
- **架构设计**: `/mnt/d/work/trans_excel/translation_system_v2/.claude/PIPELINE_ARCHITECTURE.md`
- **简化说明**: `/mnt/d/work/trans_excel/translation_system_v2/.claude/SIMPLIFIED_ARCHITECTURE.md`

---

## ✅ 架构合规确认

这套测试页面**100%符合** `ARCHITECTURE_PRINCIPLES.md` 的要求:

✅ **数据状态连续性**: 通过Session的input_state和output_state实现
✅ **任务表唯一中间数据**: 通过TaskDataFrameManager实现
✅ **统一转换流程**: 通过TransformationStage枚举严格控制
✅ **无限链式支持**: 通过parent_session_id实现（阶段4演示）
✅ **拆分与转换分离**: 阶段1拆分，阶段2/4执行，完全独立

---

**创建时间**: 2025-10-16
**架构版本**: Pipeline Architecture v1.0
**测试理念**: 禁止综合测试，确保每个模块完全独立
