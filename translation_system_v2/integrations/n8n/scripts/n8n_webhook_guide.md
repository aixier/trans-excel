# n8n Form Webhook 激活指南

## 问题
通过 API 创建的工作流虽然已激活，但 Form Trigger 的 webhook 未生成，导致无法访问表单。

## 解决步骤（只需30秒）

### 1. 打开 n8n 工作流页面
```
http://localhost:5678/home/workflows
```

### 2. 找到并打开工作流
点击以下任一工作流：
- **Excel翻译表单_自动创建** （简化版，推荐）
- **Web Form Translation (网页表单翻译)** （完整版）

### 3. 保存工作流
- 点击右上角的 **"Save"** 按钮（💾 图标）
- 或使用快捷键：`Ctrl+S` (Windows/Linux) 或 `Cmd+S` (Mac)
- 等待保存完成（约2秒）

### 4. 查看生成的 Webhook URL

保存后，webhook 会自动生成：

**方式A：在节点中查看**
1. 点击第一个节点 "翻译表单" 或 "Translation Form"
2. 在节点设置面板中，找到 **"Test URL"** 或 **"Production URL"**
3. 复制该 URL（格式：`http://localhost:5678/form/xxxxx`）

**方式B：在工作流设置中查看**
1. 点击右上角的 "⋮" 菜单
2. 选择 "Settings"
3. 找到 "Webhook" 部分查看 URL

### 5. 测试表单
在浏览器打开刚才复制的 URL，应该能看到翻译表单。

## 验证脚本

保存工作流后，运行以下命令验证 webhook 是否生成：

```bash
cd /mnt/d/work/trans_excel/translation_system_v2/integrations/n8n/scripts
python3 << 'PYEOF'
import requests
import json

API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5YWI2NGQ4Yi01NmFjLTQxOWQtOWNmZS03MjgzYThhMGY1MGUiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzYwNjg1ODU2LCJleHAiOjE3NjMyMjI0MDB9.4KZSwDix7zGmSQ-H4fOn9hxnxJWZ4vVltbQY_i22waE"

headers = {'X-N8N-API-KEY': API_KEY}
response = requests.get('http://localhost:5678/api/v1/workflows', headers=headers)
workflows = response.json().get('data', [])

print("\n" + "="*60)
print("n8n 表单 Webhook 状态")
print("="*60 + "\n")

for w in workflows:
    if 'Excel翻译' in w['name'] or 'Translation' in w['name']:
        print(f"工作流: {w['name']}")
        print(f"  状态: {'✅ 已激活' if w['active'] else '❌ 未激活'}")

        # 查找 Form Trigger
        form_nodes = [n for n in w.get('nodes', [])
                     if n.get('type') == 'n8n-nodes-base.formTrigger']

        if form_nodes:
            node = form_nodes[0]
            webhook_id = node.get('webhookId', '')

            if webhook_id:
                form_url = f"http://localhost:5678/form/{webhook_id}"
                print(f"  Webhook: ✅ 已生成")
                print(f"  表单URL: {form_url}")
            else:
                print(f"  Webhook: ❌ 未生成")
                print(f"  操作: 请在 UI 中保存工作流")
        print()

print("="*60)
PYEOF
```

## 常见问题

### Q1: 保存后还是没有 webhook？
**A**: 刷新页面，再次查看节点。如果仍然没有，尝试：
1. 停用工作流
2. 再次激活
3. 保存

### Q2: 表单 URL 显示错误？
**A**: 确保工作流处于**已激活**状态（右上角开关为绿色）。

### Q3: 可以同时使用两个工作流吗？
**A**: 可以！两个工作流可以共存，有不同的 webhook URL。

### Q4: 需要修改工作流吗？
**A**: 不需要！只需保存即可，n8n 会自动生成 webhook。

## 下一步

生成 webhook 后：
1. 在浏览器访问表单 URL
2. 上传 Excel 文件测试
3. 查看翻译结果

## 技术说明

n8n Form Trigger 的 webhook 生成机制：
- **API 创建/激活**: 只设置 `active = true`，不生成 webhook
- **UI 保存**: 触发完整的工作流验证和 webhook 注册流程
- **必须操作**: 至少在 UI 中保存一次

这是 n8n 的架构设计，无法通过纯 API 绕过。
