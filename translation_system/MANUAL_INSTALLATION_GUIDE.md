# 游戏本地化翻译系统 - 本地安装部署指南

## 📋 环境要求

- **操作系统**: Linux/macOS/Windows (WSL2推荐)
- **Python版本**: Python 3.8 或更高版本
- **MySQL版本**: MySQL 8.0 或更高版本
- **网络要求**: 能够访问阿里云服务 (OSS、DashScope)

## 🛠️ 第一步：系统环境准备

### 1.1 安装Python 3.8+

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.8 python3.8-venv python3.8-dev python3-pip

# CentOS/RHEL
sudo yum install python38 python38-devel python38-pip

# macOS (使用Homebrew)
brew install python@3.8

# 验证Python版本
python3 --version
```

### 1.2 安装MySQL 8.0

```bash
# Ubuntu/Debian
sudo apt install mysql-server mysql-client

# CentOS/RHEL
sudo yum install mysql-server mysql

# macOS
brew install mysql

# 启动MySQL服务
sudo systemctl start mysql      # Linux
brew services start mysql      # macOS
```

### 1.3 安装系统依赖

```bash
# Ubuntu/Debian
sudo apt install build-essential libssl-dev libffi-dev python3-dev

# CentOS/RHEL
sudo yum groupinstall "Development Tools"
sudo yum install openssl-devel libffi-devel python3-devel
```

## 🔧 第二步：项目环境搭建

### 2.1 进入项目目录

```bash
cd /mnt/d/work/trans_excel/translation_system/backend
```

### 2.2 创建虚拟环境

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/macOS
# 或者在Windows WSL2中：
source venv/bin/activate

# 验证虚拟环境
which python
which pip
```

### 2.3 升级pip和安装wheel

```bash
# 升级pip到最新版本
pip install --upgrade pip

# 安装wheel和setuptools
pip install wheel setuptools --upgrade
```

### 2.4 安装项目依赖

```bash
# 安装所有项目依赖
pip install -r requirements.txt

# 验证关键依赖
python -c "import fastapi; print('FastAPI:', fastapi.__version__)"
python -c "import pandas; print('Pandas:', pandas.__version__)"
python -c "import sqlalchemy; print('SQLAlchemy:', sqlalchemy.__version__)"
```

## 🗄️ 第三步：数据库配置

### 3.1 创建MySQL数据库

```bash
# 登录MySQL
mysql -u root -p

# 创建数据库
CREATE DATABASE translation_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 创建用户（可选，推荐）
CREATE USER 'trans_user'@'localhost' IDENTIFIED BY 'your_strong_password';
GRANT ALL PRIVILEGES ON translation_system.* TO 'trans_user'@'localhost';
FLUSH PRIVILEGES;

# 退出MySQL
EXIT;
```

### 3.2 验证数据库连接

```bash
# 测试数据库连接
mysql -u trans_user -p translation_system

# 显示数据库
SHOW DATABASES;
USE translation_system;
EXIT;
```

## ⚙️ 第四步：环境变量配置

### 4.1 创建环境配置文件

```bash
# 在backend目录下创建.env文件
touch .env
```

### 4.2 编辑环境变量配置

```bash
# 使用您喜欢的编辑器编辑.env文件
nano .env
# 或者
vim .env
```

### 4.3 环境变量配置内容

```env
# === 数据库配置 ===
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=trans_user
MYSQL_PASSWORD=your_strong_password
MYSQL_DATABASE=translation_system

# === 阿里云OSS配置 ===
OSS_ACCESS_KEY_ID=LTAI5tSDxxxxxxxxxx
OSS_ACCESS_KEY_SECRET=your_oss_secret_key
OSS_BUCKET_NAME=your-bucket-name
OSS_ENDPOINT=oss-cn-beijing.aliyuncs.com

# === LLM配置 ===
LLM_PROVIDER=dashscope
LLM_API_KEY=sk-your-dashscope-api-key
LLM_MODEL=qwen-plus
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# === Redis配置（可选）===
# 如果没有Redis，系统会使用内存缓存
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# === 应用配置 ===
DEBUG_MODE=true
SERVER_PORT=8000
APP_NAME=游戏本地化智能翻译系统
APP_VERSION=1.0.0

# === 翻译配置 ===
DEFAULT_BATCH_SIZE=3
DEFAULT_MAX_CONCURRENT=10
DEFAULT_MAX_ITERATIONS=5
DEFAULT_TARGET_LANGUAGES=["pt","th","ind"]
DEFAULT_REGION_CODE=na
```

### 4.4 环境变量说明

| 配置项 | 必需 | 说明 |
|--------|------|------|
| `MYSQL_*` | ✅ | MySQL数据库连接配置 |
| `OSS_*` | ✅ | 阿里云OSS存储配置 |
| `LLM_*` | ✅ | 大语言模型API配置 |
| `REDIS_*` | ❌ | Redis缓存配置（可选） |
| `DEBUG_MODE` | ❌ | 开发调试模式 |
| `SERVER_PORT` | ❌ | API服务器端口 |

## 📁 第五步：目录结构验证

### 5.1 确认目录结构

```bash
# 在backend目录下检查目录结构
ls -la

# 应该看到以下主要目录和文件：
# api_gateway/     - API网关
# translation_core/ - 翻译核心
# excel_analysis/  - Excel分析
# database/        - 数据库层
# config/          - 配置管理
# requirements.txt - 依赖列表
# start.py         - 启动脚本
# .env             - 环境配置
```

### 5.2 创建必要的工作目录

```bash
# 确保工作目录存在
mkdir -p logs temp uploads downloads

# 设置目录权限
chmod 755 logs temp uploads downloads

# 验证目录创建
ls -la logs temp uploads downloads
```

## 🗃️ 第六步：数据库初始化

### 6.1 初始化数据库表结构

```bash
# 激活虚拟环境（如果还没有激活）
source venv/bin/activate

# 运行数据库初始化脚本
python -c "
import asyncio
import sys
sys.path.insert(0, '.')
from database.connection import init_database
asyncio.run(init_database())
print('数据库初始化完成!')
"
```

### 6.2 验证数据库表创建

```bash
# 登录MySQL检查表
mysql -u trans_user -p translation_system

# 查看创建的表
SHOW TABLES;

# 应该看到以下表：
# projects
# project_versions  
# project_files
# translation_tasks
# terminology
# translation_logs

# 查看某个表结构（例如projects表）
DESCRIBE projects;
EXIT;
```

## 🚀 第七步：系统启动

### 7.1 测试系统配置

```bash
# 激活虚拟环境
source venv/bin/activate

# 测试配置和连接
python -c "
import asyncio
import sys
sys.path.insert(0, '.')
from config.settings import settings
from database.connection import test_connection

async def test():
    print('配置测试:')
    print(f'数据库: {settings.mysql_host}:{settings.mysql_port}')
    print(f'数据库名: {settings.mysql_database}')
    print(f'LLM提供商: {settings.llm_provider}')
    print(f'LLM模型: {settings.llm_model}')
    
    print('\\n数据库连接测试:')
    result = await test_connection()
    print(f'连接状态: {\"成功\" if result else \"失败\"}')
    
asyncio.run(test())
"
```

### 7.2 启动完整系统

```bash
# 启动完整的翻译系统
python start.py
```

### 7.3 启动成功验证

当看到以下输出时，表示系统启动成功：

```
============================================================
🎮 游戏本地化翻译系统
📡 服务地址: http://0.0.0.0:8000
📚 API文档: http://0.0.0.0:8000/docs
🔧 调试模式: True
🌍 支持语言: pt, th, ind
🗺️ 支持地区: na, sa, eu, me, as
============================================================
```

## 🌐 第八步：访问验证

### 8.1 访问API文档

```bash
# 在浏览器中打开
http://localhost:8000/docs

# 或者使用curl测试
curl http://localhost:8000/api/health/status
```

### 8.2 健康检查

```bash
# API健康检查
curl -X GET "http://localhost:8000/api/health/status" -H "accept: application/json"

# 系统信息
curl -X GET "http://localhost:8000/api/info" -H "accept: application/json"
```

### 8.3 基础功能测试

```bash
# 测试文件上传接口（需要准备测试Excel文件）
curl -X POST "http://localhost:8000/api/v1/translation/upload" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@text_input.xlsx" \
     -F "target_languages=pt,th" \
     -F "batch_size=3" \
     -F "region_code=na"
```

## 🔧 第九步：常见问题排查

### 9.1 依赖安装问题

```bash
# 如果遇到编译错误，安装构建工具
sudo apt install build-essential python3-dev  # Ubuntu
sudo yum groupinstall "Development Tools"     # CentOS

# 如果某个包安装失败，单独安装
pip install --no-cache-dir package_name

# 清理pip缓存重新安装
pip cache purge
pip install -r requirements.txt --force-reinstall
```

### 9.2 数据库连接问题

```bash
# 检查MySQL服务状态
sudo systemctl status mysql

# 重启MySQL服务
sudo systemctl restart mysql

# 检查端口是否被占用
netstat -tulpn | grep 3306

# 测试数据库连接
mysql -u trans_user -p -h localhost -P 3306
```

### 9.3 权限问题

```bash
# 修复目录权限
chmod -R 755 logs temp uploads downloads

# 修复Python文件权限
chmod +x start.py

# 检查当前用户权限
whoami
groups
```

### 9.4 端口占用问题

```bash
# 检查8000端口是否被占用
netstat -tulpn | grep 8000
# 或者
lsof -i :8000

# 杀死占用端口的进程
sudo kill -9 PID

# 或者修改配置使用其他端口
export SERVER_PORT=8001
```

## 📝 第十步：开发环境配置（可选）

### 10.1 安装开发工具

```bash
# 安装代码格式化工具
pip install black isort

# 安装代码检查工具  
pip install flake8 mypy

# 安装测试工具
pip install pytest pytest-asyncio pytest-cov
```

### 10.2 配置IDE

```bash
# 为VSCode创建配置
mkdir -p .vscode
cat > .vscode/settings.json << 'EOF'
{
    "python.pythonPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": false,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black"
}
EOF
```

## 🔄 第十一步：服务管理

### 11.1 创建启动脚本

```bash
# 创建启动脚本
cat > start_service.sh << 'EOF'
#!/bin/bash
cd /mnt/d/work/trans_excel/translation_system/backend
source venv/bin/activate
python start.py
EOF

chmod +x start_service.sh
```

### 11.2 后台运行

```bash
# 使用nohup后台运行
nohup ./start_service.sh > logs/service.log 2>&1 &

# 查看进程
ps aux | grep start.py

# 停止服务
pkill -f start.py
```

### 11.3 使用systemd管理（Linux）

```bash
# 创建systemd服务文件
sudo cat > /etc/systemd/system/translation-system.service << 'EOF'
[Unit]
Description=Translation System
After=network.target mysql.service

[Service]
Type=simple
User=your_username
WorkingDirectory=/mnt/d/work/trans_excel/translation_system/backend
Environment=PATH=/mnt/d/work/trans_excel/translation_system/backend/venv/bin
ExecStart=/mnt/d/work/trans_excel/translation_system/backend/venv/bin/python start.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 启用并启动服务
sudo systemctl daemon-reload
sudo systemctl enable translation-system
sudo systemctl start translation-system

# 查看服务状态
sudo systemctl status translation-system
```

## 📋 第十二步：安装验证清单

### 验证清单

- [ ] Python 3.8+ 已安装并可用
- [ ] MySQL 8.0+ 已安装并运行
- [ ] 虚拟环境已创建并激活
- [ ] 所有Python依赖已成功安装
- [ ] MySQL数据库和用户已创建
- [ ] 环境变量(.env)文件已正确配置
- [ ] 必要的工作目录已创建
- [ ] 数据库表结构已初始化
- [ ] 系统配置测试通过
- [ ] API服务器成功启动
- [ ] API文档可正常访问 (http://localhost:8000/docs)
- [ ] 健康检查接口正常响应
- [ ] 可以进行基础的翻译任务测试

### 成功标志

当所有验证项都完成后，您应该能够：

1. 访问 `http://localhost:8000/docs` 看到完整的API文档
2. 使用API上传Excel文件进行翻译
3. 查询翻译任务的进度和状态
4. 下载翻译完成的文件

## 🆘 故障排除联系方式

如果在安装过程中遇到问题，请：

1. 检查系统日志：`tail -f logs/translation_system.log`
2. 查看错误信息并对照常见问题部分
3. 确认所有环境变量配置正确
4. 验证网络连接可以访问阿里云服务

---

**安装完成！🎉**

现在您可以使用这个功能完整的游戏本地化翻译系统了。


