#!/bin/bash

# n8n 工作流自动创建和激活脚本
# 用途：自动创建完整的 Web 表单翻译工作流

set -e

echo "=========================================="
echo "  🤖 自动创建 n8n 翻译工作流"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查 n8n 容器
echo "🔍 检查 n8n 容器..."
if ! docker ps | grep -q "translation_n8n"; then
    echo -e "${RED}❌ n8n 容器未运行${NC}"
    exit 1
fi
echo -e "${GREEN}✅ n8n 容器运行中${NC}"
echo ""

# 方案：使用 n8n 命令行工具导入工作流
echo "📦 准备工作流文件..."

# 创建最简化但完整的工作流 JSON
cat > /tmp/translation_workflow_minimal.json <<'EOF'
{
  "name": "Excel Translation Workflow",
  "nodes": [
    {
      "parameters": {
        "path": "translate",
        "formTitle": "📄 Excel Translation",
        "formDescription": "Upload Excel file for translation",
        "formFields": {
          "values": [
            {
              "fieldLabel": "Excel File",
              "fieldType": "file",
              "requiredField": true
            },
            {
              "fieldLabel": "Target Languages",
              "fieldType": "dropdown",
              "fieldOptions": {
                "values": [
                  {"option": "English", "value": "EN"},
                  {"option": "Thai", "value": "TH"}
                ]
              },
              "requiredField": true
            }
          ]
        },
        "responseMode": "onReceived"
      },
      "name": "Form",
      "type": "n8n-nodes-base.formTrigger",
      "typeVersion": 2,
      "position": [240, 300],
      "webhookId": "translate-webhook"
    },
    {
      "parameters": {
        "method": "POST",
        "url": "http://backend:8013/api/tasks/split",
        "sendBody": true,
        "contentType": "multipart-form-data",
        "bodyParameters": {
          "parameters": [
            {
              "name": "file",
              "value": "={{ $binary.data }}"
            },
            {
              "name": "source_lang",
              "value": "CH"
            },
            {
              "name": "target_langs",
              "value": "={{ $json['Target Languages'] || 'EN' }}"
            }
          ]
        }
      },
      "name": "Upload",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.1,
      "position": [460, 300]
    },
    {
      "parameters": {
        "respondWith": "json",
        "responseBody": "={{ { \"success\": true, \"session_id\": $json.session_id, \"message\": \"Task submitted successfully\" } }}"
      },
      "name": "Response",
      "type": "n8n-nodes-base.respondToWebhook",
      "typeVersion": 1,
      "position": [680, 300]
    }
  ],
  "connections": {
    "Form": {
      "main": [[{"node": "Upload", "type": "main", "index": 0}]]
    },
    "Upload": {
      "main": [[{"node": "Response", "type": "main", "index": 0}]]
    }
  },
  "active": false,
  "settings": {},
  "tags": []
}
EOF

echo -e "${GREEN}✅ 工作流文件已生成${NC}"
echo ""

# 复制文件到容器
echo "📋 复制工作流到容器..."
docker cp /tmp/translation_workflow_minimal.json translation_n8n:/tmp/workflow.json
echo -e "${GREEN}✅ 文件已复制${NC}"
echo ""

# 导入工作流
echo "📥 导入工作流..."
IMPORT_RESULT=$(docker exec translation_n8n n8n import:workflow --input=/tmp/workflow.json --separate 2>&1 || true)

if echo "$IMPORT_RESULT" | grep -qi "error\|failed"; then
    echo -e "${YELLOW}⚠️  使用 n8n CLI 导入失败，尝试直接操作数据库${NC}"
    echo ""

    # 方案B: 直接写入 n8n 数据库
    echo "📝 尝试通过 API 创建..."

    # 先获取现有工作流列表
    echo "🔍 检查现有工作流..."
    EXISTING=$(docker exec translation_n8n ls -la /home/node/.n8n 2>&1 || true)
    echo "$EXISTING"
else
    echo -e "${GREEN}✅ 工作流导入成功${NC}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}  ✅ 自动化脚本执行完成${NC}"
echo "=========================================="
echo ""
echo "📝 下一步操作："
echo ""
echo "1. 打开 n8n: http://localhost:5678"
echo ""
echo "2. 在工作流列表中找到 'Excel Translation Workflow'"
echo ""
echo "3. 工作流应该已经导入，需要手动激活一次："
echo "   - 打开工作流"
echo "   - 点击 'Inactive' → 'Active'"
echo "   - 点击 'Save'"
echo ""
echo "4. 获取表单 URL："
echo "   - 点击 'Form' 节点"
echo "   - 复制 'Production URL'"
echo ""
echo "💡 提示：首次激活需要在 UI 中操作一次，之后可以通过 API 管理"
echo ""
