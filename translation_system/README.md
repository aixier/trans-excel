# 游戏本地化翻译系统

基于微服务架构的游戏本地化翻译系统，支持Excel文件的自动翻译、项目版本管理、区域化本地化等企业级功能。

## ✨ 系统特性

- 🎮 **游戏专用**: 针对游戏本地化场景优化，支持占位符保护、术语管理
- 🌍 **多地区支持**: 支持5个地区的文化本地化 (北美、南美、欧洲、中东、亚洲)
- 🚀 **高性能**: 异步批量处理，支持并发翻译，可自定义批次大小和并发数
- 🔄 **迭代优化**: 支持最多5轮迭代翻译，自动优化翻译质量
- 📊 **智能分析**: 自动检测Excel表头结构，识别需要翻译的内容
- 🛡️ **占位符保护**: 自动保护游戏中的变量占位符、HTML标签、Unity富文本等
- 💾 **版本管理**: 支持项目版本管理，文件历史追踪
- 📈 **进度跟踪**: 实时进度监控，API调用统计，成本控制

## 🏗️ 系统架构

```
translation_system/
├── backend/                    # 后端服务
│   ├── api_gateway/           # API网关层
│   │   ├── main.py           # FastAPI主应用
│   │   ├── models/           # API数据模型
│   │   └── routers/          # API路由
│   ├── translation_core/      # 翻译核心
│   │   ├── translation_engine.py      # 翻译引擎
│   │   ├── placeholder_protector.py   # 占位符保护
│   │   ├── localization_engine.py     # 本地化引擎
│   │   └── terminology_manager.py     # 术语管理
│   ├── excel_analysis/        # Excel分析
│   │   ├── header_analyzer.py         # 表头分析器
│   │   └── translation_detector.py    # 翻译检测器
│   ├── database/              # 数据库层
│   │   ├── models.py         # 数据模型
│   │   └── connection.py     # 数据库连接
│   ├── file_service/          # 文件服务
│   │   └── storage/          # 云存储抽象
│   ├── project_manager/       # 项目管理
│   └── config/               # 配置管理
└── frontend/                  # 前端界面 (待开发)
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- MySQL 8.0+
- 阿里云OSS存储
- LLM API (DashScope/OpenAI)

### 安装步骤

1. **克隆项目**
```bash
cd translation_system/backend
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库、OSS、LLM等信息
```

4. **启动系统**
```bash
python start.py
```

5. **访问API文档**
```
http://localhost:8000/docs
```

## 📖 API使用说明

### 1. 上传翻译文件

```http
POST /api/translation/upload
Content-Type: multipart/form-data

file: Excel文件
target_languages: "pt,th,ind"
batch_size: 3
max_concurrent: 10
region_code: "na"
game_background: "RPG游戏"
```

### 2. 查询翻译进度

```http
GET /api/translation/tasks/{task_id}/progress
```

返回示例:
```json
{
  "task_id": "xxx-xxx-xxx",
  "status": "translating",
  "progress": {
    "total_rows": 190,
    "translated_rows": 95,
    "current_iteration": 2,
    "completion_percentage": 50.0
  },
  "statistics": {
    "total_api_calls": 32,
    "total_tokens_used": 15000,
    "total_cost": 0.75
  }
}
```

### 3. 下载翻译结果

```http
GET /api/translation/tasks/{task_id}/download
```

## 🔧 配置说明

### 数据库配置
```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=translation_system
```

### LLM配置
```env
LLM_PROVIDER=dashscope
LLM_API_KEY=your_dashscope_key
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-max
```

### OSS配置
```env
OSS_ACCESS_KEY_ID=your_access_key
OSS_ACCESS_KEY_SECRET=your_secret_key
OSS_ENDPOINT=https://oss-cn-hangzhou.aliyuncs.com
OSS_BUCKET_NAME=your_bucket
```

## 🎯 支持的语言和地区

### 目标语言
- **pt**: 葡萄牙语 (巴西)
- **th**: 泰语
- **ind**: 印尼语

### 地区代码
- **na**: 北美 (North America)
- **sa**: 南美 (South America)
- **eu**: 欧洲 (Europe)
- **me**: 中东 (Middle East)
- **as**: 亚洲 (Asia)

## 🛡️ 占位符保护

系统自动保护以下类型的占位符:

- **变量占位符**: `%s`, `%d`, `{num}`, `{0}`, `{name}`
- **HTML标签**: `<color>`, `<b>`, `<i>`, `<size>`
- **Unity富文本**: `<color=#FF0000>`, `<size=20>`
- **特殊符号**: `\\n`, `\\t`, `&lt;`, `&gt;`

## 📊 翻译流程

1. **文件上传**: Excel文件上传到系统
2. **智能分析**: 自动分析表头结构，检测可翻译内容
3. **批次创建**: 根据配置创建翻译批次
4. **并发翻译**: 使用信号量控制并发翻译
5. **质量检查**: 多轮迭代优化翻译质量
6. **结果保存**: 生成带时间戳的完成文件

## 🔍 监控和日志

- **健康检查**: `/api/health/status`
- **系统信息**: `/api/info`
- **日志文件**: `logs/translation_system.log`

## 🚧 开发状态

### 已完成 ✅
- [x] 项目结构搭建
- [x] 配置管理系统
- [x] 数据库模型设计
- [x] Excel分析引擎
- [x] 翻译核心引擎
- [x] 占位符保护系统
- [x] 本地化引擎
- [x] 术语管理系统
- [x] API网关开发
- [x] 文件存储服务
- [x] 项目管理系统

### 待开发 🚧
- [ ] 单元测试
- [ ] 集成测试
- [ ] 性能优化
- [ ] 前端界面
- [ ] Docker化部署
- [ ] 监控告警

## 📝 更新日志

### v1.0.0 (2025-09-18)
- ✨ 系统架构完整实现
- ✨ 基于Demo的翻译引擎
- ✨ 多地区本地化支持
- ✨ API网关和路由
- ✨ 异步数据库支持

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持

如有问题或建议，请通过以下方式联系:

- 🐛 Bug报告: GitHub Issues
- 💡 功能建议: GitHub Issues
- 📧 邮件支持: support@example.com

---

**Made with ❤️ for Game Localization**