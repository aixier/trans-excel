# n8n API Key 配置说明

## 快速开始

### 1. 生成 API Key

在 n8n UI 中生成（这是唯一方式）：

```
http://localhost:5678 → Settings → n8n API → Create API Key
```

复制生成的 key（只显示一次！）

### 2. 保存 API Key

**方式 A：配置文件（推荐）** ⭐

编辑 `.env.local`：

```bash
cd /mnt/d/work/trans_excel/translation_system_v2/integrations/n8n
echo "N8N_API_KEY=你的_API_Key" > .env.local
```

> 已保存你的 key：`eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

**方式 B：环境变量**

```bash
export N8N_API_KEY="你的_API_Key"
```

**方式 C：命令行参数**

```bash
python3 scripts/auto_create_via_api.py --api-key "你的_API_Key"
```

**方式 D：交互式输入**

```bash
python3 scripts/auto_create_via_api.py --interactive
```

### 3. 验证配置

```bash
cd scripts
python3 config.py
```

应该看到：
```
✅ API Key 已加载
📍 n8n URL: http://localhost:5678
```

### 4. 运行脚本

现在可以直接运行，无需每次输入 API Key：

```bash
cd scripts
python3 auto_create_via_api.py
```

## 在代码中使用

### Python 脚本

```python
from config import get_api_headers
import requests

# 自动从 .env.local 读取
headers = get_api_headers()

# 调用 API
response = requests.get(
    'http://localhost:5678/api/v1/workflows',
    headers=headers
)

workflows = response.json()['data']
```

### 独立脚本

如果不想依赖 config.py：

```python
import os
from pathlib import Path

# 读取 .env.local
env_file = Path(__file__).parent.parent / '.env.local'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if line.startswith('N8N_API_KEY='):
                api_key = line.split('=', 1)[1].strip()
                break

headers = {
    'X-N8N-API-KEY': api_key,
    'Content-Type': 'application/json'
}
```

## 文件结构

```
n8n/
├── .env.local          # API Key 配置（已添加到 .gitignore）
├── .gitignore          # 排除敏感文件
├── scripts/
│   ├── config.py       # 配置读取模块
│   ├── auto_create_via_api.py  # 自动创建脚本
│   └── verify_form.py  # 表单验证脚本
└── README_API_KEY.md   # 本文档
```

## 安全注意事项

### ✅ 推荐做法

- ✅ 使用 `.env.local` 文件保存 key
- ✅ 确保 `.env.local` 在 `.gitignore` 中
- ✅ 定期轮换 API Key
- ✅ 不同环境使用不同的 key

### ❌ 不要做

- ❌ 不要将 key 提交到 Git
- ❌ 不要在代码中硬编码 key
- ❌ 不要在日志中打印完整 key
- ❌ 不要分享你的 API Key

## 故障排查

### 问题 1: "未找到 API Key"

**原因**：
- `.env.local` 文件不存在
- 文件中没有 `N8N_API_KEY=` 行
- 环境变量未设置

**解决**：
```bash
# 检查文件是否存在
ls -la /mnt/d/work/trans_excel/translation_system_v2/integrations/n8n/.env.local

# 检查文件内容
cat /mnt/d/work/trans_excel/translation_system_v2/integrations/n8n/.env.local

# 重新创建
echo "N8N_API_KEY=你的key" > /mnt/d/work/trans_excel/translation_system_v2/integrations/n8n/.env.local
```

### 问题 2: "401 Unauthorized"

**原因**：
- API Key 无效或过期
- API Key 格式错误

**解决**：
1. 在 n8n UI 中重新生成 API Key
2. 更新 `.env.local` 文件
3. 验证 key 格式（应该是长字符串，通常以 `eyJ` 开头）

### 问题 3: ImportError: cannot import name 'get_api_key'

**原因**：
- `config.py` 不在正确位置
- Python 路径问题

**解决**：
```bash
# 确保在 scripts 目录运行
cd /mnt/d/work/trans_excel/translation_system_v2/integrations/n8n/scripts

# 检查 config.py 是否存在
ls -la config.py

# 运行脚本
python3 auto_create_via_api.py
```

## 优先级

脚本按以下顺序查找 API Key：

1. **命令行参数** `--api-key`（最高优先级）
2. **交互式输入** `--interactive`
3. **配置文件** `.env.local`
4. **环境变量** `N8N_API_KEY`

## 示例工作流

### 首次设置

```bash
# 1. 在 n8n UI 生成 API Key
# 访问 http://localhost:5678/settings/api

# 2. 保存到配置文件
cd /mnt/d/work/trans_excel/translation_system_v2/integrations/n8n
echo "N8N_API_KEY=eyJhbG..." > .env.local

# 3. 验证
cd scripts
python3 config.py

# 4. 使用
python3 auto_create_via_api.py
```

### 日常使用

```bash
# 直接运行，自动读取配置
cd /mnt/d/work/trans_excel/translation_system_v2/integrations/n8n/scripts
python3 auto_create_via_api.py
```

### 测试验证

```bash
# 验证配置
python3 config.py

# 验证表单
python3 verify_form.py
```

## 相关文档

- [N8N API Key 设置指南](./scripts/N8N_API_KEY_SETUP.md)
- [Webhook 修复文档](./WEBHOOK_FIXED.md)
- [Claude 开发指南](./.claude/CLAUDE.md)
- [故障排查](./TROUBLESHOOTING.md)

---

**已为你配置好 API Key！**

- ✅ `.env.local` 已创建并保存 key
- ✅ `.gitignore` 已更新，不会提交敏感信息
- ✅ `config.py` 模块可以自动读取
- ✅ 所有脚本都支持从配置文件读取

**现在可以直接运行脚本，无需每次输入 API Key！** 🎉
