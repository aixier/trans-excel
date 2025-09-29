# Backend V2 - 翻译系统后端

> **🚀 后端实现：** 这是翻译系统后端的主要实现，采用现代化设计模式。

## 📁 项目结构

```
backend_v2/
├── api/                    # API路由层
├── config/                 # 配置管理
├── database/              # 数据库相关
├── docs/                  # 📚 文档目录
├── models/                # 数据模型
├── services/              # 🚀 核心服务层
│   ├── executor/          # 翻译执行引擎
│   ├── llm/              # LLM集成服务
│   └── export/           # 导出服务
├── tests/                 # 测试文件
└── utils/                 # 工具类
```

## 📚 文档导航

### 核心设计文档
- [🎯 **提示词设计文档**](docs/prompt_design.md) - 提示词模板和智能选择策略
- [⚙️ **LLM配置文档**](docs/LLM_SETTINGS_AND_PROMPT_CONFIG.md) - LLM设置和配置指南
- [🏗️ **系统设计方案 V3**](docs/系统设计方案_v3.md) - Backend V2 整体架构设计

### 开发计划文档
- [📋 **渐进式开发计划**](docs/渐进式开发计划.md) - 整体开发路线图
- [1️⃣ **第一阶段任务**](docs/第一阶段任务.md) - 基础架构搭建
- [2️⃣ **第二阶段任务**](docs/第二阶段任务.md) - 核心功能实现
- [3️⃣ **第三阶段任务**](docs/第三阶段任务.md) - 高级功能开发

### 技术细节文档
- [📊 **任务分组策略说明**](docs/任务分组策略说明.md) - 翻译任务分组逻辑
- [🔧 **任务拆分核心参数说明**](docs/任务拆分核心参数说明.md) - 任务拆分算法

## 🚀 快速开始

### 1. 环境准备
```bash
cd backend_v2
pip install -r requirements.txt
```

### 2. 配置设置
```bash
# 复制配置模板
cp config/config.yaml.example config/config.yaml
# 根据 docs/LLM_SETTINGS_AND_PROMPT_CONFIG.md 进行配置
```

### 3. 启动服务
```bash
python main.py
```

## 🎯 核心特性

### ✅ 已实现功能
- 🏗️ **Worker Pool 架构** - 高性能并发执行
- 🧩 **模块化LLM集成** - 支持多种LLM提供商
- 📝 **智能提示词模板** - 动态源语言选择
- 🔄 **批量处理优化** - 高效的批量翻译
- 📊 **任务管理系统** - 完整的任务生命周期管理

### 🚧 开发中功能
- 🎨 **区域文化配置** - 多地区本地化支持
- 📋 **批注约束系统** - Excel批注作为翻译约束
- 🏷️ **术语管理集成** - 项目级术语表管理

## 📖 开发指南

### 核心文件说明
- **`services/llm/prompt_template.py`** - 提示词模板核心实现
- **`services/executor/worker_pool.py`** - 并发执行引擎
- **`services/llm/qwen_provider.py`** - Qwen LLM集成
- **`api/execute_api.py`** - 翻译执行API

### 开发规范
1. 遵循模块化设计原则
2. 保持代码简洁性，避免过度设计
3. 优先性能和可扩展性
4. 完善的错误处理和日志记录

## 🔗 相关链接

- [整体项目文档](../README.md) - 项目总体说明

---

> **📝 注意**: 这是翻译系统后端的主要实现，采用现代化架构设计。