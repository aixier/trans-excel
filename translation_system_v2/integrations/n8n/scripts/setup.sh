#!/bin/bash

# n8n 翻译系统一键部署脚本
# 使用方法: ./setup.sh

set -e

echo "========================================"
echo "  📦 n8n 翻译系统一键部署"
echo "========================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查Docker
echo "🔍 检查 Docker..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker 未安装，请先安装 Docker${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose 未安装，请先安装 Docker Compose${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker 已安装${NC}"
echo ""

# 进入项目目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# 检查 .env 文件
echo "🔍 检查环境配置..."
if [ ! -f "docker/.env" ]; then
    echo -e "${YELLOW}⚠️  未找到 .env 文件，从模板创建...${NC}"
    cp docker/.env.example docker/.env
    echo -e "${YELLOW}📝 请编辑 docker/.env 文件，填写 API 密钥${NC}"
    echo ""
    read -p "是否现在编辑 .env 文件? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ${EDITOR:-vi} docker/.env
    else
        echo -e "${YELLOW}请稍后手动编辑: docker/.env${NC}"
        echo -e "${YELLOW}必须配置以下变量:${NC}"
        echo "  - QWEN_API_KEY"
        echo "  - N8N_ENCRYPTION_KEY"
        echo ""
        read -p "按任意键继续..."
    fi
fi

echo -e "${GREEN}✅ 环境配置就绪${NC}"
echo ""

# 创建数据目录
echo "📁 创建数据目录..."
mkdir -p /data/input
mkdir -p /data/output
mkdir -p /data/glossaries
mkdir -p /data/logs

echo -e "${GREEN}✅ 数据目录创建完成${NC}"
echo ""

# 上传示例术语表到后端
echo "📚 准备术语表..."
if [ -f "examples/glossaries/game_terms.json" ]; then
    cp examples/glossaries/*.json /data/glossaries/ 2>/dev/null || true
    echo -e "${GREEN}✅ 术语表已复制到 /data/glossaries/${NC}"
fi
echo ""

# 启动服务
echo "🚀 启动服务..."
cd docker
docker-compose up -d

echo ""
echo "⏳ 等待服务启动..."
sleep 15

# 检查服务状态
echo ""
echo "🔍 检查服务状态..."

# 检查后端
if curl -s http://localhost:8013/api/database/health > /dev/null; then
    echo -e "${GREEN}✅ 后端API运行正常 (http://localhost:8013)${NC}"
else
    echo -e "${RED}❌ 后端API未响应${NC}"
fi

# 检查n8n
if curl -s http://localhost:5678 > /dev/null; then
    echo -e "${GREEN}✅ n8n运行正常 (http://localhost:5678)${NC}"
else
    echo -e "${RED}❌ n8n未响应${NC}"
fi

echo ""

# 导入工作流
echo "📥 导入工作流..."
cd "$PROJECT_DIR"

# 等待n8n完全启动
sleep 5

# 使用docker exec导入工作流
if [ -f "workflows/08_web_form_translation.json" ]; then
    echo "  - 导入 Web 表单翻译工作流..."
    docker exec translation_n8n n8n import:workflow --input=/workflows/08_web_form_translation.json 2>/dev/null || \
        echo -e "${YELLOW}    ⚠️  自动导入失败，请手动导入${NC}"
fi

echo -e "${GREEN}✅ 工作流导入完成${NC}"
echo ""

# 上传术语表到后端
echo "📚 上传术语表到后端..."
for glossary in examples/glossaries/*.json; do
    if [ -f "$glossary" ]; then
        glossary_name=$(basename "$glossary" .json)
        echo "  - 上传 $glossary_name..."
        curl -s -X POST http://localhost:8013/api/glossaries/upload \
            -F "file=@$glossary" \
            -F "glossary_id=$glossary_name" > /dev/null 2>&1 || true
    fi
done

echo -e "${GREEN}✅ 术语表上传完成${NC}"
echo ""

# 完成
echo "========================================"
echo -e "${GREEN}  ✅ 部署完成！${NC}"
echo "========================================"
echo ""
echo "📌 访问地址:"
echo ""
echo "  🌐 Web表单翻译:"
echo "     http://localhost:5678/form/translate"
echo ""
echo "  🎛️  n8n管理界面:"
echo "     http://localhost:5678"
echo ""
echo "  🔌 后端API:"
echo "     http://localhost:8013"
echo ""
echo "📝 使用步骤:"
echo "  1. 打开浏览器访问: http://localhost:5678/form/translate"
echo "  2. 上传 Excel 文件"
echo "  3. 选择目标语言和术语表"
echo "  4. 点击提交，等待翻译完成"
echo ""
echo "📚 文档:"
echo "  - 快速开始: cat README.md"
echo "  - 工作流目录: cat docs/WORKFLOW_CATALOG.md"
echo "  - 故障排除: docker-compose logs -f"
echo ""
echo "🛑 停止服务:"
echo "  cd docker && docker-compose down"
echo ""
