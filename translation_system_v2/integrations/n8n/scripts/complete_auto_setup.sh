#!/bin/bash

# 完全自动化的 n8n 工作流设置脚本
# 包括导入、激活、获取 URL

set -e

echo "=========================================="
echo "  🚀 完全自动化 n8n 设置"
echo "=========================================="
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# 1. 检查 n8n
echo "🔍 步骤1: 检查 n8n 服务..."
if ! curl -s http://localhost:5678/healthz > /dev/null; then
    echo -e "${RED}❌ n8n 未响应${NC}"
    exit 1
fi
echo -e "${GREEN}✅ n8n 运行正常${NC}"
echo ""

# 2. 检查后端
echo "🔍 步骤2: 检查后端服务..."
if ! curl -s http://localhost:8013/health > /dev/null; then
    echo -e "${RED}❌ 后端未响应${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 后端运行正常${NC}"
echo ""

# 3. 创建并导入工作流
echo "📦 步骤3: 创建工作流..."

# 创建简化但功能完整的工作流
cat > /tmp/auto_workflow.json <<'WORKFLOW_EOF'
{
  "name": "Auto Excel Translation",
  "nodes": [
    {
      "parameters": {
        "path": "translate",
        "formTitle": "📄 Excel File Translation System",
        "formDescription": "Upload your Excel file for automatic translation",
        "formFields": {
          "values": [
            {
              "fieldLabel": "Excel File",
              "fieldType": "file",
              "requiredField": true
            },
            {
              "fieldLabel": "Target Language",
              "fieldType": "dropdown",
              "fieldOptions": {
                "values": [
                  {"option": "English (EN)", "value": "EN"},
                  {"option": "Thai (TH)", "value": "TH"},
                  {"option": "Portuguese (PT)", "value": "PT"},
                  {"option": "Vietnamese (VN)", "value": "VN"}
                ]
              },
              "requiredField": true
            },
            {
              "fieldLabel": "Glossary (Optional)",
              "fieldType": "dropdown",
              "fieldOptions": {
                "values": [
                  {"option": "None", "value": ""},
                  {"option": "Game Terms", "value": "game_terms"},
                  {"option": "Business Terms", "value": "business_terms"}
                ]
              }
            }
          ]
        },
        "responseMode": "onReceived",
        "formSubmittedText": "✅ Translation task submitted!\n\nYour file is being processed...\n\nYou will receive the session ID below."
      },
      "name": "Translation Form",
      "type": "n8n-nodes-base.formTrigger",
      "typeVersion": 2,
      "position": [250, 350],
      "webhookId": "auto-translate"
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
              "value": "={{ $json['Target Language'] }}"
            },
            {
              "name": "rule_set",
              "value": "translation"
            }
          ]
        },
        "options": {
          "timeout": 60000
        }
      },
      "name": "Submit to Backend",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.1,
      "position": [500, 350]
    },
    {
      "parameters": {
        "respondWith": "json",
        "responseBody": "={{ {\n  \"success\": true,\n  \"session_id\": $json.session_id,\n  \"message\": \"Translation task submitted successfully!\",\n  \"status_url\": \"http://localhost:8013/api/tasks/split/status/\" + $json.session_id,\n  \"download_url\": \"http://localhost:8013/api/download/\" + $json.session_id\n} }}",
        "options": {}
      },
      "name": "Return Result",
      "type": "n8n-nodes-base.respondToWebhook",
      "typeVersion": 1,
      "position": [750, 350]
    }
  ],
  "connections": {
    "Translation Form": {
      "main": [[{"node": "Submit to Backend", "type": "main", "index": 0}]]
    },
    "Submit to Backend": {
      "main": [[{"node": "Return Result", "type": "main", "index": 0}]]
    }
  },
  "active": false,
  "settings": {
    "executionOrder": "v1"
  },
  "tags": []
}
WORKFLOW_EOF

docker cp /tmp/auto_workflow.json translation_n8n:/tmp/workflow_auto.json
echo -e "${GREEN}✅ 工作流文件已准备${NC}"
echo ""

# 4. 导入工作流
echo "📥 步骤4: 导入工作流到 n8n..."
docker exec translation_n8n n8n import:workflow --input=/tmp/workflow_auto.json --separate 2>&1 | grep -v "^$" || true
echo -e "${GREEN}✅ 工作流已导入${NC}"
echo ""

# 5. 等待 n8n 处理
echo "⏳ 等待 n8n 处理..."
sleep 3
echo ""

# 6. 显示下一步
echo "=========================================="
echo -e "${GREEN}  ✅ 自动导入完成！${NC}"
echo "=========================================="
echo ""
echo -e "${YELLOW}⚠️  重要：首次激活需要一次手动操作${NC}"
echo ""
echo "📋 请按以下步骤操作："
echo ""
echo -e "${BLUE}1. 打开 n8n:${NC}"
echo "   http://localhost:5678"
echo ""
echo -e "${BLUE}2. 在工作流列表找到 'Auto Excel Translation'${NC}"
echo "   (如果看不到，点击筛选器取消归档)"
echo ""
echo -e "${BLUE}3. 激活工作流:${NC}"
echo "   - 打开工作流"
echo "   - 点击右上角 'Inactive' 改为 'Active'"
echo "   - ⚠️  点击 'Save' 保存！"
echo ""
echo -e "${BLUE}4. 获取表单 URL:${NC}"
echo "   - 点击 'Translation Form' 节点"
echo "   - 右侧面板会显示 'Production URL'"
echo "   - 复制这个 URL"
echo ""
echo -e "${BLUE}5. 访问表单:${NC}"
echo "   - 在浏览器中打开获取到的 URL"
echo "   - 上传 Excel 文件测试"
echo ""
echo "=========================================="
echo ""
echo "💡 提示："
echo "   - 工作流只需激活一次"
echo "   - 激活后会自动生成唯一的表单 URL"
echo "   - URL 类似: http://localhost:5678/form/xxxx-xxxx-xxxx"
echo ""
echo "🔧 故障排除："
echo "   - 如果激活失败，检查后端是否运行"
echo "   - 如果找不到工作流，检查是否被归档"
echo "   - 查看日志: docker logs translation_n8n"
echo ""
