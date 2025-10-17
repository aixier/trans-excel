# Next Steps for Form Workflow (下一步操作)

## Current Status (当前状态)

✅ **Configuration Fixed** - 配置已修复
- Binary data pass-through: ✅ Correct
- HTTP Request file reference: ✅ Correct  
- Form Trigger settings: ✅ Correct
- Workflow is active: ✅ Yes

⚠️ **Pending** - 待处理
- Webhook registration: ❌ Not registered (needs UI save)

## What Was Fixed (修复内容)

### Problem (问题)
```
NodeApiError: source.on is not a function
at Upload & Split Tasks node (HTTP Request)
```

### Root Cause (根本原因)
Incorrect binary data reference in HTTP Request node:
- Old: `{{ Object.values($binary)[0] }}`
- Issue: Not stable for multipart/form-data file uploads

### Solution (解决方案)
Changed to explicit field name reference:
- New: `{{ $binary['Excel 文件'] }}`
- Also ensured: `binary: $input.item.binary` in Process Form Data node

## Action Required (需要操作)

### 1️⃣ Save Workflow in UI (在 UI 中保存工作流)

**Why?** - 为什么？
- API updates don't register webhook routes
- Must save in UI to register the form URL
- This is a n8n architectural limitation

**How?** - 怎么做？
1. Open: http://localhost:5678/workflow/1xQAR3UTNGrk0X6B
2. Click the **Save** button (💾 icon in top right)
3. Wait for "Saved" confirmation

### 2️⃣ Verify Webhook Registration (验证 Webhook)

```bash
cd /mnt/d/work/trans_excel/translation_system_v2/integrations/n8n/scripts
python3 verify_form.py
```

**Expected output** after UI save:
```
5️⃣ Testing webhook accessibility...
   Form URL: http://localhost:5678/form/{webhook-id}
   ✅ Form is accessible!
   🎉 You can test the form at: http://localhost:5678/form/{webhook-id}
```

### 3️⃣ Test the Form (测试表单)

1. Access the form URL from verify_form.py output
2. Upload a test Excel file (should have CH column)
3. Select target language (e.g., EN)
4. Choose glossary (optional)
5. Choose translation engine (default: 通义千问)
6. Click Submit
7. Wait for the translation to complete (may take a few minutes)

**Expected result**:
```json
{
  "success": true,
  "message": "✅ 翻译完成！",
  "session_id": "xxx-xxx-xxx",
  "file_name": "example_translated.xlsx",
  "download_url": "http://localhost:8013/api/download/xxx-xxx-xxx",
  "tips": "文件已保存，可以通过 download_url 下载"
}
```

## Troubleshooting (故障排查)

### If form still shows "Problem loading form"
1. Ensure you saved in UI (not just API update)
2. Try deactivate → save → activate
3. Check n8n logs: `docker logs translation_n8n`

### If you still get "source.on is not a function"
1. Run verify_form.py to check configuration
2. If configuration is correct, open workflow in n8n UI and inspect:
   - Process Form Data node output (binary structure)
   - Upload & Split Tasks node input (binary data)
3. Check n8n version compatibility (should be 1.115.3+)

### If backend is not responding
1. Check backend is running: `docker ps | grep backend`
2. Check backend logs: `docker logs translation_backend`
3. Test backend API: `curl http://localhost:8013/api/tasks/split`

## Documentation (文档)

- [Error Fix Details](./workflows/ERROR_FIX_source_on.md)
- [Workflow Update Log](./workflows/WORKFLOW_UPDATE_LOG.md)
- [Claude Development Guide](./.claude/CLAUDE.md)
- [API Key Setup](./README_API_KEY.md)

## Scripts (脚本)

- `scripts/verify_form.py` - Verify workflow configuration
- `scripts/config.py` - Configuration management
- `scripts/auto_create_via_api.py` - Auto-create workflows

---

**Last Updated**: 2025-01-17 19:30
**Status**: Configuration fixed, awaiting UI save
**Priority**: HIGH - User action required to complete fix
