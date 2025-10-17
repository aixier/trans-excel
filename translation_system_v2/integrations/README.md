# Translation System - 集成层

本目录包含翻译系统与各种第三方工具、平台的集成方案。

---

## 🎯 集成层定位

```
translation_system_v2/
├── backend_v2/         ← API服务核心（RESTful API）
├── frontend_v2/        ← 浏览器界面（人工操作）
└── integrations/       ← 集成层（自动化/扩展）
    └── n8n/           ← 工作流自动化
```

**职责划分**：
- **backend_v2**: 提供RESTful API服务，处理业务逻辑
- **frontend_v2**: 提供浏览器UI，适合人工单次操作
- **integrations**: 连接外部工具，实现自动化和批量处理

---

## 📦 可用集成

### 🔄 n8n - 工作流自动化

**路径**: [`./n8n/`](./n8n/)

**适用场景**:
- ✅ 定时批量翻译（每天凌晨处理文件夹）
- ✅ 复杂多步骤流程（翻译 → 审核 → 通知）
- ✅ 条件分支处理（根据文件大小选择不同策略）
- ✅ 与其他服务联动（翻译完成后发送邮件/Slack通知）
- ✅ 文件夹监控（新文件自动触发翻译）

**技术栈**: n8n Workflow Automation

**难度**: ⭐⭐ (中等)

**状态**: ✅ 已实现

**快速开始**: [n8n/README.md](./n8n/README.md)

---

### 🌐 浏览器前端 (frontend_v2)

**路径**: [`../frontend_v2/`](../frontend_v2/)

**适用场景**:
- ✅ 手动单文件翻译
- ✅ 实时监控翻译进度
- ✅ 术语表管理
- ✅ 结果预览和下载

**技术栈**: 原生 HTML/CSS/JavaScript

**难度**: ⭐ (简单)

**状态**: ✅ 已实现

---

### 🔌 直接API调用

**适用场景**:
- ✅ 集成到现有系统
- ✅ 编程语言调用（Python/JavaScript/curl）
- ✅ 自定义业务逻辑

**技术栈**: HTTP Client

**难度**: ⭐⭐⭐ (较难)

**状态**: ✅ API已就绪

**文档**: [backend_v2/API_REFERENCE.md](../backend_v2/API_REFERENCE.md)

---

## 🧭 选择指南

根据你的使用场景选择合适的集成方式：

| 使用场景 | 推荐方案 | 理由 |
|---------|---------|------|
| **手动单次翻译** | 浏览器前端 | 可视化界面，简单直观 |
| **定时批量翻译** | n8n工作流 | 自动化执行，无需人工干预 |
| **复杂多步骤流程** | n8n工作流 | 支持条件分支、循环、错误处理 |
| **与现有系统集成** | 直接API调用 | 灵活性最高，可嵌入任何系统 |
| **文件夹监控** | n8n工作流 | 支持Trigger和Polling |
| **消息通知联动** | n8n工作流 | 可连接Slack/Email/Webhook |

---

## 🔗 集成示例对比

### 示例：翻译一个Excel文件

#### 方案1: 浏览器前端
```
1. 打开 http://localhost:8080
2. 点击"上传文件"
3. 选择目标语言
4. 点击"开始翻译"
5. 等待完成，下载结果
```
**优势**: 可视化，适合学习和测试
**劣势**: 需要人工操作，无法自动化

---

#### 方案2: n8n工作流
```
1. 导入预设工作流
2. 配置文件路径和参数
3. 设置定时触发（如每天2AM）
4. 自动执行，结果保存到指定位置
```
**优势**: 全自动，支持复杂逻辑
**劣势**: 需要学习n8n基础

---

#### 方案3: 直接API调用
```bash
# 1. 上传并拆分
curl -X POST http://localhost:8013/api/tasks/split \
  -F "file=@game.xlsx" \
  -F "target_langs=EN,TH"
# → 返回 session_id

# 2. 执行翻译
curl -X POST http://localhost:8013/api/execute/start \
  -H "Content-Type: application/json" \
  -d '{"session_id": "xxx", "processor": "llm_qwen"}'

# 3. 下载结果
curl http://localhost:8013/api/download/xxx -o result.xlsx
```
**优势**: 完全控制，可嵌入脚本
**劣势**: 需要编程知识

---

## 🚀 快速开始

### 1. 确保后端运行

```bash
cd /mnt/d/work/trans_excel/translation_system_v2/backend_v2
python3 main.py
```

后端应运行在 `http://localhost:8013`

---

### 2. 选择集成方式

#### 选项A: 浏览器前端
```bash
cd /mnt/d/work/trans_excel/translation_system_v2/frontend_v2
# 打开 test_pages/2_execute_transformation.html
```

#### 选项B: n8n工作流
```bash
cd /mnt/d/work/trans_excel/translation_system_v2/integrations/n8n
# 查看快速开始指南
cat README.md
```

#### 选项C: API调用
```bash
# 查看API文档
cat /mnt/d/work/trans_excel/translation_system_v2/backend_v2/API_REFERENCE.md
```

---

## 📚 文档索引

### 核心文档
- [后端API参考](../backend_v2/API_REFERENCE.md) - 所有API端点详细说明
- [后端数据流](../backend_v2/BACKEND_DATA_FLOW.md) - 系统架构和数据流程
- [前端使用手册](../frontend_v2/USER_MANUAL.md) - 浏览器界面使用指南

### 集成文档
- [n8n集成指南](./n8n/README.md) - n8n工作流快速开始
- [n8n工作流目录](./n8n/docs/WORKFLOW_CATALOG.md) - 所有预设工作流说明
- [n8n部署方案](./n8n/docs/DOCKER_DEPLOYMENT.md) - Docker部署指南

---

## 🔮 未来规划

### 计划中的集成

#### Zapier集成 (未来)
```
integrations/zapier/
├── zaps/
├── docs/
└── README.md
```
**优势**: 可连接5000+应用

---

#### Make.com集成 (未来)
```
integrations/make/
├── scenarios/
├── docs/
└── README.md
```
**优势**: 可视化工作流编辑器

---

#### API客户端库 (未来)
```
integrations/api_clients/
├── python/
│   └── translation_client.py
├── javascript/
│   └── translation-client.js
└── README.md
```
**优势**: 简化编程调用

---

## ❓ 常见问题

### Q1: 我应该选择哪种集成方式？

**A**:
- 如果你是**非技术用户**，只需要偶尔翻译 → 使用**浏览器前端**
- 如果你需要**定时批量处理** → 使用**n8n工作流**
- 如果你要**集成到现有系统** → 使用**直接API调用**

---

### Q2: n8n和浏览器前端可以同时使用吗？

**A**: 可以！它们都是调用同一个后端API，互不影响。

---

### Q3: 我的工作流需要哪些权限？

**A**:
- 文件读写权限（读取Excel，保存结果）
- 网络访问权限（调用后端API）
- 如果使用Docker，需要配置文件挂载

---

### Q4: 集成层会修改后端代码吗？

**A**: **不会**。集成层只是后端API的消费者，不修改后端任何代码。

---

## 📧 支持与反馈

- **后端问题**: 查看 [backend_v2/README.md](../backend_v2/README.md)
- **前端问题**: 查看 [frontend_v2/README.md](../frontend_v2/README.md)
- **n8n集成问题**: 查看 [n8n/docs/TROUBLESHOOTING.md](./n8n/docs/TROUBLESHOOTING.md)

---

## 📝 更新日志

**v1.0.0** (2025-10-17)
- ✅ 创建集成层目录结构
- ✅ n8n工作流集成方案设计完成
- ✅ 文档编写完成
- 🔄 工作流JSON实现中

---

**祝你使用愉快！** 🎉
