# n8n 工作流版本对比

## 📋 可用的工作流文件

### 1. `08_web_form_translation_simple.json` ⭐ **推荐新手使用**

**简化版 - 只提交任务**

**节点数量**: 3个
- 翻译表单 (Form Trigger)
- 提交翻译任务 (HTTP Request)
- 返回结果 (Respond to Webhook)

**特点**:
- ✅ 简单直观，易于理解
- ✅ 快速上手，适合学习
- ✅ 只负责提交任务，返回 session_id
- ⚠️ 需要用户手动查询状态和下载结果

**适用场景**:
- 学习 n8n 工作流
- 快速测试翻译功能
- 与前端应用集成（前端负责轮询）
- 需要自定义后续处理逻辑

**使用步骤**:
1. 导入工作流
2. 激活工作流
3. 访问表单 URL
4. 上传文件，获取 session_id
5. 手动访问 status_url 查询进度
6. 完成后访问 download_url 下载

---

### 2. `08_web_form_translation.json` 🚀 **完整自动化**

**完整版 - 自动轮询和下载**

**节点数量**: 13个
- 翻译表单 (Form Trigger)
- 处理表单数据 (Code)
- 上传并拆分任务 (HTTP Request)
- 轮询拆分状态 (HTTP Request + If + Wait)
- 执行翻译 (HTTP Request)
- 轮询执行状态 (HTTP Request + If + Wait)
- 下载结果 (HTTP Request)
- 保存文件 (Write Binary File)
- 返回成功/失败 (Respond to Webhook x2)

**特点**:
- ✅ 完全自动化，无需手动操作
- ✅ 自动轮询任务状态
- ✅ 自动下载并保存结果文件
- ✅ 错误处理和重试机制
- ⚠️ 复杂，不易理解和修改
- ⚠️ 工作流执行时间长（等待翻译完成）

**适用场景**:
- 生产环境使用
- 需要完全自动化的场景
- 不想手动查询状态
- 需要立即获得翻译结果

**使用步骤**:
1. 导入工作流
2. 激活工作流
3. 访问表单 URL
4. 上传文件，等待几分钟
5. 自动返回下载链接

---

## 🆚 详细对比

| 特性 | 简化版 | 完整版 |
|------|--------|--------|
| **节点数量** | 3 | 13 |
| **复杂度** | ⭐ 简单 | ⭐⭐⭐⭐⭐ 复杂 |
| **执行时间** | <1秒 | 几分钟（等待翻译） |
| **自动轮询** | ❌ | ✅ |
| **自动下载** | ❌ | ✅ |
| **错误处理** | ❌ | ✅ |
| **学习成本** | 低 | 高 |
| **适合新手** | ✅ | ❌ |
| **适合生产** | 需配合前端 | ✅ |

---

## 🎯 如何选择？

### 选择简化版（08_web_form_translation_simple.json）当你：

1. **刚开始学习 n8n** - 简单的流程便于理解
2. **需要快速测试** - 快速验证功能是否正常
3. **有前端应用** - 前端可以自己实现轮询逻辑
4. **需要自定义** - 简单结构易于修改和扩展
5. **对响应时间敏感** - 不想等待翻译完成

### 选择完整版（08_web_form_translation.json）当你：

1. **需要开箱即用** - 不想写额外代码
2. **生产环境部署** - 需要稳定可靠的自动化
3. **终端用户使用** - 用户希望一次操作完成所有步骤
4. **不需要修改** - 功能满足需求，不需要定制
5. **可以等待** - 可以接受几分钟的处理时间

---

## 📝 导入方式

### 方式1：通过 n8n UI 导入

```bash
1. 访问 http://localhost:5678
2. 点击右上角 "Import from File"
3. 选择对应的 JSON 文件
4. 点击 "Import"
5. 激活工作流
```

### 方式2：通过 API 自动创建（仅简化版）

```bash
cd integrations/n8n/scripts
python3 auto_create_via_api.py --interactive
```

这个脚本会自动创建并激活简化版工作流。

---

## 🔄 从简化版迁移到完整版

如果你先使用简化版，后来需要完整的自动化功能：

1. **保留简化版工作流** - 可以共存
2. **导入完整版** - 作为新的工作流
3. **更新前端代码** - 指向新的表单 URL
4. **测试完整流程** - 确保一切正常
5. **停用简化版** - 可选，不影响完整版

---

## 🛠️ 自定义建议

### 基于简化版自定义

简化版易于扩展，你可以添加：

1. **邮件通知** - 翻译完成后发送邮件
2. **数据库记录** - 保存翻译历史
3. **Slack 通知** - 团队协作
4. **文件上传到云存储** - S3、OSS 等

### 基于完整版自定义

完整版已经很复杂，建议只修改：

1. **轮询间隔** - Wait 节点的时间
2. **超时设置** - HTTP Request 的 timeout
3. **文件保存路径** - Write Binary File 的参数
4. **返回信息格式** - Respond to Webhook 的内容

---

## 📚 相关文档

- [快速修复 401 错误](../QUICK_FIX_401.md)
- [API Key 设置指南](../scripts/N8N_API_KEY_SETUP.md)
- [故障排查指南](../TROUBLESHOOTING.md)
- [主 README](../README.md)

---

## 💡 技术提示

### 简化版的 HTTP Request 配置

```yaml
URL: http://backend:8013/api/tasks/split
Method: POST
Content-Type: multipart-form-data
Body:
  - file: {{ $binary.data }}
  - source_lang: CH
  - target_langs: {{ $json['目标语言'] }}
  - glossary_name: {{ $json['术语库（可选）'] || 'default' }}
Timeout: 300000ms (5分钟)
```

### 完整版的轮询逻辑

```
Poll Split Status → Check Split Complete
    ↓ Yes                   ↓ No
Execute Translation      Wait 2s → Poll Again

Poll Execution Status → Check Execution Complete
    ↓ Yes                      ↓ No
Download Result             Wait 5s → Poll Again
```

---

## ❓ 常见问题

### Q1: 简化版提交后看不到结果？

**A**: 这是正常的。简化版只负责提交任务，需要手动访问返回的 `status_url` 查询进度。

### Q2: 完整版一直在等待？

**A**: 完整版会自动轮询直到翻译完成。如果超过10分钟，检查后端日志。

### Q3: 可以同时使用两个版本吗？

**A**: 可以！它们是独立的工作流，可以共存。建议使用不同的路径：
- 简化版: `/trans-simple`
- 完整版: `/trans-full`

### Q4: 哪个性能更好？

**A**: 
- **简化版**：响应快（<1秒），但需要额外的状态查询请求
- **完整版**：整体时间长（几分钟），但用户体验更好（一次性完成）

### Q5: 如何修改表单路径？

编辑 Form Trigger 节点的 `path` 参数：
```json
"parameters": {
  "path": "your-custom-path"
}
```

保存后，表单 URL 变为：`http://localhost:5678/form/{webhook_id}`

---

**选择适合你的版本，开始翻译之旅！** 🚀
