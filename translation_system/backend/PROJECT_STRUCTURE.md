# Translation System 项目结构（清理后）

## 核心目录结构

```
translation_system/
├── backend/                      # 后端服务
│   ├── api_gateway/              # API网关
│   │   ├── main.py              # FastAPI主应用
│   │   ├── models/              # API数据模型
│   │   └── routers/             # API路由
│   │       ├── health.py        # 健康检查
│   │       ├── project.py       # 项目管理
│   │       └── translation.py   # 翻译服务 ⭐
│   ├── config/                   # 配置管理
│   │   └── settings.py          # 系统配置
│   ├── database/                 # 数据库层
│   │   ├── connection.py        # 连接管理
│   │   └── models.py            # 数据模型
│   ├── excel_analysis/           # Excel分析 ⭐
│   │   ├── header_analyzer.py   # 表头分析
│   │   └── translation_detector.py # 翻译检测
│   ├── file_service/             # 文件服务
│   │   └── storage/             # 存储接口
│   ├── project_manager/          # 项目管理
│   │   └── manager.py           # 项目管理器
│   ├── translation_core/         # 翻译核心 ⭐
│   │   ├── translation_engine.py # 翻译引擎
│   │   ├── localization_engine.py # 本地化
│   │   ├── terminology_manager.py # 术语管理
│   │   └── placeholder_protector.py # 占位符保护
│   ├── start.py                 # 主启动脚本
│   └── Dockerfile               # Docker配置
├── frontend/                     # 前端（Vue项目）
├── backup/                       # 备份的测试文件
│   ├── test_servers/            # 测试服务器
│   └── docs/                    # 重复文档
└── docker-compose.yml           # Docker编排

```

## 核心文件说明

### 1. 启动入口
- **start.py** - 生产环境启动脚本
- **api_gateway/main.py** - FastAPI应用定义

### 2. 翻译流程核心
- **translation_engine.py** - 主翻译逻辑，协调所有组件
- **header_analyzer.py** - 分析Excel表头，识别语言列
- **translation_detector.py** - 检测需要翻译的内容

### 3. API接口
- **routers/translation.py** - 翻译API端点
  - POST /upload - 上传文件
  - GET /tasks/{id}/progress - 查询进度
  - GET /tasks/{id}/download - 下载结果

## 语言支持

系统自动检测并支持以下语言：
- CH (中文), TW (繁体中文)
- EN (英语)
- PT (葡萄牙语), ES (西班牙语)
- TH (泰语), VN (越南语), IND (印尼语)
- TR (土耳其语), AR (阿拉伯语)
- JA (日语), KO (韩语)
- DE (德语), FR (法语), IT (意大利语), RU (俄语)

## Docker运行

```bash
# 构建镜像
docker build -t translation-system:1.1 .

# 运行容器
docker run -d --name trans-system \
  -p 8101:8000 \
  --health-cmd "curl -f http://localhost:8000/api/health/status || exit 1" \
  --health-interval 30s \
  --health-timeout 10s \
  --health-retries 3 \
  translation-system:1.1

# 检查状态
curl http://localhost:8101/api/health/status
```

## 注意事项

1. **已清理的文件**：所有测试和临时文件已移至 `/backup` 目录
2. **核心功能**：系统自动检测Excel中的语言列并翻译
3. **无需指定语言**：上传文件时可不指定target_languages，系统自动检测