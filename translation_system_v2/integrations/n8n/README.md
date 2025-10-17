# n8n 翻译系统集成

## ⚠️ 重要说明

- ✅ **本项目只负责 n8n 工作流部分**
- ✅ **Backend_v2 是独立项目**，请参考其自己的文档启动
- ✅ **前提**: Backend_v2 必须已运行在 `localhost:8013`

---

## 🎯 快速开始（2步）

### 前提条件

**Backend_v2 已运行**（独立项目）：
```bash
# 验证 backend 是否运行
curl http://localhost:8013/health
```

如果未运行，请参考 `/backend_v2` 项目的文档启动。

---

### 步骤1: 启动 n8n

```bash
cd /mnt/d/work/trans_excel/translation_system_v2/integrations/n8n/docker
docker-compose up -d
```

验证：
```bash
curl http://localhost:5678/healthz
```

### 步骤2: 自动创建工作流 ⭐

```bash
cd /mnt/d/work/trans_excel/translation_system_v2/integrations/n8n/scripts
python3 auto_create_via_api.py --interactive
```

⚠️ **首次使用需要生成 API Key：**
1. 打开 http://localhost:5678
2. 登录后：Settings → n8n API → Create API Key
3. 复制生成的 key
4. 粘贴到脚本提示中

**脚本会输出表单访问地址**，例如：
```
📋 表单访问地址:
   http://localhost:5678/form/abc-def-123-456
```

**访问这个地址即可使用 Web 表单上传和翻译 Excel 文件！**

**遇到 401 错误？** 查看 [快速修复指南](./QUICK_FIX_401.md)

### 表单预览

```
┌─────────────────────────────────────────┐
│  📄 Excel 文件翻译系统                  │
├─────────────────────────────────────────┤
│  Excel 文件: [选择文件]                │
│                                         │
│  目标语言:                              │
│  ☑ 英文 (EN)  ☐ 泰文 (TH)             │
│  ☐ 葡萄牙文 (PT) ☐ 越南文 (VN)        │
│                                         │
│  术语表: [下拉选择] 游戏术语            │
│  翻译引擎: [下拉选择] 通义千问          │
│                                         │
│  [提交]                                 │
└─────────────────────────────────────────┘
```

**优势**:
- ✅ 零配置 - 部署后立即使用
- ✅ 零学习成本 - 表单界面，直观易用
- ✅ 自动化处理 - 提交后自动完成所有步骤

**详细说明**: 查看 [Web 表单使用指南](./WEB_FORM_GUIDE.md)

---

## 🚀 5分钟快速开始（手动配置工作流）

### 前置要求

- ✅ 后端API运行在 `http://localhost:8013`
- ✅ Docker已安装（推荐）或 Node.js ≥ 16
- ✅ 至少2GB可用内存

---

### 步骤1: 启动n8n

#### 方式A: Docker（推荐）

```bash
# 进入docker目录
cd /mnt/d/work/trans_excel/translation_system_v2/integrations/n8n/docker

# 启动n8n
docker-compose up -d

# 查看日志
docker-compose logs -f n8n
```

#### 方式B: npm

```bash
# 全局安装n8n
npm install -g n8n

# 启动n8n
n8n start
```

---

### 步骤2: 访问n8n界面

打开浏览器访问: **http://localhost:5678**

初次访问会要求创建账户:
- 用户名: `admin`
- 密码: `<设置你的密码>`
- Email: `admin@example.com`

---

### 步骤3: 导入第一个工作流

1. 点击右上角 **"Import from File"**
2. 选择文件: `workflows/01_basic_translation.json`
3. 点击 **"Import"**

---

### 步骤4: 配置工作流

1. 双击 **"Read File"** 节点
2. 修改文件路径:
   ```
   /data/input/game.xlsx
   ```
3. 点击 **"Save"**

4. 双击 **"Upload & Split"** 节点
5. 检查API地址:
   ```
   http://localhost:8013/api/tasks/split
   ```
   如果n8n在Docker中，使用:
   ```
   http://host.docker.internal:8013/api/tasks/split
   ```
6. 点击 **"Save"**

---

### 步骤5: 执行工作流

1. 点击 **"Execute Workflow"**
2. 观察每个节点的执行状态
3. 查看结果文件

---

## 📁 目录结构

```
n8n/
├── workflows/              # 工作流JSON文件
│   ├── 01_basic_translation.json
│   ├── 02_translation_with_glossary.json
│   ├── 03_batch_translation.json
│   ├── 04_chain_translation_caps.json
│   ├── 05_scheduled_translation.json
│   ├── 06_webhook_triggered.json
│   └── 07_conditional_processing.json
│
├── docs/                   # 详细文档
│   ├── IMPLEMENTATION_PLAN.md      # 实现方案
│   ├── WORKFLOW_CATALOG.md         # 工作流目录
│   ├── DOCKER_DEPLOYMENT.md        # Docker部署
│   ├── TROUBLESHOOTING.md          # 故障排除
│   └── BEST_PRACTICES.md           # 最佳实践
│
├── examples/               # 示例数据
│   ├── sample_files/       # 示例Excel文件
│   ├── glossaries/         # 示例术语表
│   └── configs/            # 配置模板
│
├── docker/                 # Docker配置
│   ├── docker-compose.yml
│   └── .env.example
│
├── scripts/                # 辅助脚本
│   ├── import_workflows.sh
│   ├── export_workflows.sh
│   └── setup_n8n.sh
│
└── README.md               # 本文件
```

---

## 🔄 可用工作流

| 工作流 | 难度 | 适用场景 | 状态 |
|-------|------|---------|------|
| [**Web表单翻译**](./WEB_FORM_GUIDE.md) ⭐ **推荐** | ⭐ | 浏览器界面翻译 | ✅ **已实现** |
| [基础翻译](./docs/WORKFLOW_CATALOG.md#工作流1-基础翻译) | ⭐ | 单文件手动翻译 | 🟡 设计完成 |
| [术语表翻译](./docs/WORKFLOW_CATALOG.md#工作流2-术语表翻译) | ⭐⭐ | 术语一致性翻译 | 🟡 设计完成 |
| [批量处理](./docs/WORKFLOW_CATALOG.md#工作流3-批量处理) | ⭐⭐⭐ | 批量翻译多文件 | 🟡 设计完成 |
| [链式处理](./docs/WORKFLOW_CATALOG.md#工作流4-链式处理) | ⭐⭐⭐ | 翻译+大写转换 | 🟡 设计完成 |
| [定时任务](./docs/WORKFLOW_CATALOG.md#工作流5-定时任务) | ⭐⭐⭐⭐ | 每日自动翻译 | 🟡 设计完成 |
| [Webhook触发](./docs/WORKFLOW_CATALOG.md#工作流6-webhook触发) | ⭐⭐⭐⭐ | 外部系统集成 | 🟡 设计完成 |
| [条件分支](./docs/WORKFLOW_CATALOG.md#工作流7-条件分支) | ⭐⭐⭐⭐ | 智能策略选择 | 🟡 设计完成 |

**状态说明**:
- ✅ **已实现** - JSON文件已创建，可直接使用
- 🟡 设计完成 - 方案文档已完成，JSON待实现

详细说明请查看: [工作流目录](./docs/WORKFLOW_CATALOG.md)

---

## 💡 使用场景示例

### 场景1: 每天凌晨自动翻译

**需求**: 每天凌晨2点自动翻译 `/data/input` 文件夹中的新文件

**方案**: 使用 **05_scheduled_translation.json**

**配置**:
```json
{
  "cronExpression": "0 2 * * *",
  "inputFolder": "/data/input",
  "outputFolder": "/data/output"
}
```

**效果**: 无需人工干预，每天自动处理

---

### 场景2: 外部系统触发翻译

**需求**: 游戏管理后台提交翻译任务，n8n自动处理并回调结果

**方案**: 使用 **06_webhook_triggered.json**

**集成代码**:
```javascript
// 游戏后台提交翻译
fetch('https://n8n.example.com/webhook/translate', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    file_url: 'https://storage.example.com/game.xlsx',
    target_langs: ['EN', 'TH'],
    callback_url: 'https://api.game.com/translation/callback'
  })
});

// 接收翻译完成回调
app.post('/translation/callback', (req, res) => {
  const {session_id, result_url} = req.body;
  console.log(`Translation completed: ${result_url}`);
});
```

---

### 场景3: 术语一致性翻译

**需求**: 翻译游戏文本时，确保"攻击力"始终翻译为"ATK"

**方案**: 使用 **02_translation_with_glossary.json**

**配置**:
1. 准备术语表 `game_terms.json`:
   ```json
   {
     "攻击力": "ATK",
     "生命值": "HP",
     "防御力": "DEF"
   }
   ```
2. 导入工作流
3. 配置术语表路径
4. 执行翻译

**效果**: 所有术语翻译一致，提升翻译质量

---

## 🔧 配置说明

### API地址配置

**本地开发**:
```
http://localhost:8013
```

**Docker环境**:
```
http://host.docker.internal:8013  # Docker Desktop (Mac/Windows)
http://172.17.0.1:8013            # Docker on Linux
```

**远程服务器**:
```
http://<your-server-ip>:8013
```

---

### 文件路径映射

如果n8n在Docker中运行，需要配置卷挂载:

```yaml
# docker-compose.yml
volumes:
  - /mnt/d/work/trans_excel:/data
```

工作流中的路径:
```
/data/input/game.xlsx
/data/output/result.xlsx
/data/glossaries/terms.json
```

实际路径:
```
/mnt/d/work/trans_excel/input/game.xlsx
/mnt/d/work/trans_excel/output/result.xlsx
/mnt/d/work/trans_excel/glossaries/terms.json
```

---

## 📊 监控和日志

### 查看工作流执行历史

1. 在n8n界面点击 **"Executions"**
2. 查看所有执行记录
3. 点击任意执行查看详细日志

---

### 查看节点输出

1. 执行工作流后，点击任意节点
2. 查看 **"Input"** 和 **"Output"** 标签
3. 检查数据是否符合预期

---

### Docker日志

```bash
# 查看n8n日志
docker-compose logs -f n8n

# 查看后端日志
docker-compose logs -f backend
```

---

## 🐛 常见问题

### Q1: n8n无法连接后端API

**问题**: `Error: connect ECONNREFUSED 127.0.0.1:8013`

**解决**:
1. 确认后端运行: `curl http://localhost:8013/api/database/health`
2. 如果n8n在Docker中，使用: `http://host.docker.internal:8013`
3. 检查防火墙设置

---

### Q2: 文件读取失败

**问题**: `Error: ENOENT: no such file or directory`

**解决**:
1. 检查文件路径是否正确
2. 确认Docker卷挂载配置
3. 检查文件权限

---

### Q3: 轮询超时

**问题**: `Maximum number of retries reached`

**解决**:
1. 增加 `maxRetries` 值
2. 检查后端是否正常处理
3. 查看后端日志排查错误

---

### Q4: Webhook无法访问

**问题**: `Webhook URL not accessible`

**解决**:
1. 确认n8n可从外部访问
2. 配置反向代理（Nginx）
3. 设置HTTPS证书（生产环境）

### Q5: 401 Unauthorized 错误

**问题**: `❌ 创建工作流失败: 401 {"message":"unauthorized"}`

**解决**:
必须通过 n8n UI 生成 API Key，环境变量中的 key 无效。

**快速修复**:
1. 打开 http://localhost:5678
2. Settings → n8n API → Create API Key
3. 复制生成的 key
4. 运行: `python3 auto_create_via_api.py --interactive`

详细步骤请查看:
- [快速修复指南](./QUICK_FIX_401.md)
- [API Key 设置指南](./scripts/N8N_API_KEY_SETUP.md)
- [完整故障排查](./TROUBLESHOOTING.md)

---

## 🔐 安全建议

### 1. 启用认证

```yaml
# docker-compose.yml
environment:
  - N8N_BASIC_AUTH_ACTIVE=true
  - N8N_BASIC_AUTH_USER=admin
  - N8N_BASIC_AUTH_PASSWORD=<strong-password>
```

---

### 2. 使用HTTPS

生产环境务必启用HTTPS:

```yaml
environment:
  - N8N_PROTOCOL=https
  - N8N_SSL_KEY=/certs/privkey.pem
  - N8N_SSL_CERT=/certs/fullchain.pem
```

---

### 3. 限制文件权限

```bash
# 设置只读权限
chmod 444 workflows/*.json

# 设置数据目录权限
chmod 750 /data/input
chmod 750 /data/output
```

---

## 📖 文档索引

### 快速开始
- [本README](./README.md) - 5分钟快速上手

### 详细文档
- [实现方案](./docs/IMPLEMENTATION_PLAN.md) - 完整实施步骤和技术细节
- [工作流目录](./docs/WORKFLOW_CATALOG.md) - 所有工作流的详细说明
- [Docker部署](./docs/DOCKER_DEPLOYMENT.md) - 生产环境部署指南
- [故障排除](./docs/TROUBLESHOOTING.md) - 常见问题和解决方案
- [最佳实践](./docs/BEST_PRACTICES.md) - 性能优化和安全建议

### 后端文档
- [API参考](../../backend_v2/API_REFERENCE.md) - 后端API完整文档
- [后端数据流](../../backend_v2/BACKEND_DATA_FLOW.md) - 系统架构说明

### 集成层文档
- [集成总览](../README.md) - 所有集成方案对比

---

## 🚀 下一步

### 初学者

1. ✅ 完成5分钟快速开始
2. ✅ 导入并测试 **01_basic_translation.json**
3. ✅ 尝试修改工作流参数
4. ✅ 阅读 [工作流目录](./docs/WORKFLOW_CATALOG.md)

---

### 进阶用户

1. ✅ 创建自定义工作流
2. ✅ 配置定时任务
3. ✅ 集成Webhook
4. ✅ 阅读 [实现方案](./docs/IMPLEMENTATION_PLAN.md)

---

### 生产部署

1. ✅ 配置Docker Compose
2. ✅ 启用HTTPS和认证
3. ✅ 设置监控和告警
4. ✅ 阅读 [Docker部署](./docs/DOCKER_DEPLOYMENT.md)

---

## 🆘 获取帮助

### 文档
- [n8n官方文档](https://docs.n8n.io/)
- [翻译系统后端文档](../../backend_v2/README.md)

### 社区
- [n8n社区论坛](https://community.n8n.io/)
- [n8n GitHub](https://github.com/n8n-io/n8n)

### 问题反馈
- 后端问题: 查看 `backend_v2/README.md`
- n8n集成问题: 查看 `docs/TROUBLESHOOTING.md`

---

## 📝 更新日志

**v1.1.0** (2025-10-17) - Web 表单功能上线
- ✅ **实现 Web 表单翻译工作流** - 浏览器界面上传翻译
- ✅ 创建示例术语表（游戏/商业/技术）
- ✅ 创建一键部署脚本 (setup.sh)
- ✅ 编写 Web 表单使用指南
- ✅ 完整的开箱即用方案

**v1.0.0** (2025-10-17) - 初始版本
- ✅ 创建n8n集成目录结构
- ✅ 设计7个核心工作流
- ✅ 编写完整实现方案文档
- ✅ 创建快速开始指南

---

**开始你的n8n自动化翻译之旅！** 🎉

如有问题，请查看 [故障排除指南](./docs/TROUBLESHOOTING.md) 或联系技术支持。
