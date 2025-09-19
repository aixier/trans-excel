# 游戏本地化翻译系统 - 前端测试工具

## 快速启动

### 方式一：直接双击打开（推荐）

1. **启动后端服务**
```bash
cd /mnt/d/work/trans_excel/translation_system/backend
SERVER_PORT=8001 python3 minimal_server.py
```

2. **直接打开HTML文件**
   - 在文件管理器中找到 `/mnt/d/work/trans_excel/translation_system/frontend/index.html`
   - 双击直接在浏览器中打开
   - 或者在浏览器中按 Ctrl+O 打开文件

### 方式二：通过HTTP服务器访问

1. **启动后端服务**（同上）

2. **启动前端服务**
```bash
cd /mnt/d/work/trans_excel/translation_system/frontend
python3 -m http.server 3000
```

3. **访问测试界面**
打开浏览器访问: http://localhost:3000

## 功能说明

### 主要功能
- **文件上传**: 支持拖拽或选择Excel文件上传
- **翻译配置**: 选择目标语言、地区代码、批次大小等参数
- **进度监控**: 实时查看翻译进度和处理状态
- **结果下载**: 翻译完成后下载结果文件

### 支持的配置
- **目标语言**: 葡萄牙语(pt)、泰语(th)、印尼语(ind)、西班牙语(es)、法语(fr)、德语(de)
- **地区代码**: 北美(na)、南美(sa)、欧洲(eu)、中东(me)、亚洲(as)
- **批次大小**: 1-20行/批次
- **最大并发**: 1-50个并发任务

## 文件结构
```
frontend/
├── index.html    # 主页面
├── script.js     # JavaScript逻辑
├── style.css     # 样式文件
└── README.md     # 本文档
```

## API端点
- 健康检查: `GET /api/health/status`
- 文件上传: `POST /api/translation/upload`
- 进度查询: `GET /api/translation/status/{task_id}`
- 结果下载: `GET /api/translation/download/{task_id}`

## 注意事项
1. 确保后端服务已启动在8001端口
2. 前端默认使用3000端口
3. 支持的文件格式: .xlsx, .xls
4. 建议文件大小不超过10MB

## 故障排除
- **API连接失败**: 检查后端服务是否正常运行
- **上传失败**: 确认文件格式正确且不超过大小限制
- **进度卡住**: 刷新页面重试或检查后端日志