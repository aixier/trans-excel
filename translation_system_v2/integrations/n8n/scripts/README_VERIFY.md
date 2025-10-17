# Form Verification Script (表单验证脚本)

## Quick Start

```bash
cd /mnt/d/work/trans_excel/translation_system_v2/integrations/n8n/scripts
python3 verify_form.py
```

## What It Checks (检查项目)

1. **Workflow Status** (工作流状态)
   - Whether workflow exists
   - Whether workflow is active

2. **Form Trigger Configuration** (表单触发器配置)
   - Response mode (should be "lastNode")
   - Path setting
   - Webhook ID (empty = needs UI save)

3. **Process Form Data Node** (表单数据处理节点)
   - Binary pass-through: `binary: $input.item.binary`

4. **Upload & Split Tasks Node** (上传和拆分任务节点)
   - File parameter: `{{ $binary['Excel 文件'] }}`

5. **Webhook Accessibility** (Webhook 可访问性)
   - Tests if the form URL is accessible
   - Checks if webhook is registered

## Output Examples (输出示例)

### Before UI Save (保存前)

```
============================================================
Form Workflow Verification (表单工作流验证)
============================================================

1️⃣  Fetching workflow...
✅ Workflow found: Web Form Translation (网页表单翻译)
   Active: True

2️⃣  Checking Form Trigger configuration...
   Name: Translation Form
   Path: translation
   Response Mode: lastNode
   Webhook ID: (empty - need UI save)

3️⃣  Checking Process Form Data node...
   ✅ Binary pass-through: Correct

4️⃣  Checking Upload & Split Tasks node...
   File parameter: ={{ $binary['Excel 文件'] }}
   ✅ Binary reference: Correct (specific field name)

5️⃣  Testing webhook accessibility...
   ⚠️  No webhook ID - workflow needs to be saved in UI
   📝 Action: Open http://localhost:5678/workflow/1xQAR3UTNGrk0X6B and click Save

============================================================
Summary (总结)
============================================================
⚠️  Some configuration issues detected
Please review the checks above
```

### After UI Save (保存后)

```
5️⃣  Testing webhook accessibility...
   Form URL: http://localhost:5678/form/abc123xyz
   ✅ Form is accessible!
   🎉 You can test the form at: http://localhost:5678/form/abc123xyz

============================================================
Summary (总结)
============================================================
✅ Configuration looks good!

Next steps:
1. If webhook is not registered:
   - Open: http://localhost:5678/workflow/1xQAR3UTNGrk0X6B
   - Click the Save button (💾)
   - Run this script again to verify

2. Test the form:
   - Access: http://localhost:5678/form/abc123xyz
   - Upload an Excel file
   - Select target language (EN)
   - Submit and wait for result
```

## When to Run (何时运行)

- ✅ After updating workflow via API
- ✅ Before testing form submission
- ✅ After saving workflow in UI
- ✅ When troubleshooting form issues

## Troubleshooting (故障排查)

### Error: "API Key not found"
```bash
# Check if .env.local exists
cat /mnt/d/work/trans_excel/translation_system_v2/integrations/n8n/.env.local

# If missing, create it
echo "N8N_API_KEY=your-api-key" > /mnt/d/work/trans_excel/translation_system_v2/integrations/n8n/.env.local
```

### Error: "Connection refused"
```bash
# Check if n8n is running
docker ps | grep n8n

# Check n8n logs
docker logs translation_n8n
```

### Configuration shows as incorrect
1. Check the workflow in n8n UI
2. Compare with the workflow JSON file
3. Re-apply fix via API:
```bash
python3 << 'PYTHON_EOF'
import requests
import json
from config import get_api_headers

headers = get_api_headers()
workflow_id = "1xQAR3UTNGrk0X6B"

# Deactivate, update, activate
requests.post(f'http://localhost:5678/api/v1/workflows/{workflow_id}/deactivate', headers=headers)

with open('../workflows/08_web_form_translation.json') as f:
    workflow = json.load(f)

update_data = {
    'name': workflow['name'],
    'nodes': workflow['nodes'],
    'connections': workflow['connections'],
    'settings': workflow['settings']
}

requests.put(f'http://localhost:5678/api/v1/workflows/{workflow_id}', headers=headers, json=update_data)
requests.post(f'http://localhost:5678/api/v1/workflows/{workflow_id}/activate', headers=headers)

print("Workflow re-applied")
PYTHON_EOF
```

## Related Scripts (相关脚本)

- `config.py` - Configuration management
- `auto_create_via_api.py` - Create workflows via API

## Related Docs (相关文档)

- [Next Steps](../NEXT_STEPS.md)
- [Error Fix Details](../workflows/ERROR_FIX_source_on.md)
- [Workflow Update Log](../workflows/WORKFLOW_UPDATE_LOG.md)

---

**Last Updated**: 2025-01-17 19:30
