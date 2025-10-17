# 🚀 快速开始：3步使用 Web 表单翻译

**目标**: 3分钟部署，立即使用浏览器界面翻译 Excel 文件

---

## 步骤1: 一键部署（1分钟）

```bash
# 进入n8n目录
cd /mnt/d/work/trans_excel/translation_system_v2/integrations/n8n

# 一键部署
./scripts/setup.sh
```

**脚本会自动完成**:
- ✅ 检查Docker环境
- ✅ 创建必要的目录
- ✅ 启动后端和n8n服务
- ✅ 导入Web表单工作流
- ✅ 上传示例术语表

**等待时间**: 约1-2分钟

---

## 步骤2: 打开 Web 表单（5秒）

```
打开浏览器访问: http://localhost:5678/form/translate
```

你会看到:

```
┌──────────────────────────────────────────────┐
│  📄 Excel 文件翻译系统                       │
│  上传 Excel 文件，自动翻译为多种语言         │
├──────────────────────────────────────────────┤
│                                              │
│  Excel 文件 *                                │
│  [选择文件]                                  │
│                                              │
│  目标语言 *                                  │
│  ☑ 英文 (EN)                                │
│  ☐ 泰文 (TH)                                │
│  ☐ 葡萄牙文 (PT)                            │
│  ☐ 越南文 (VN)                              │
│                                              │
│  术语表                                      │
│  [下拉选择] 游戏术语 (game_terms)           │
│                                              │
│  翻译引擎                                    │
│  [下拉选择] 通义千问 (推荐)                 │
│                                              │
│  [提交]                                      │
└──────────────────────────────────────────────┘
```

---

## 步骤3: 上传并翻译（1分钟）

1. **选择文件**: 点击"选择文件"，上传你的 Excel 文件
2. **选择语言**: 勾选一个或多个目标语言
3. **选择术语表**（可选）: 如果需要术语一致性
4. **点击提交**: 等待翻译完成

**提交后**:

```
┌──────────────────────────────────────────────┐
│  ✅ 翻译任务已提交！                         │
│                                              │
│  正在处理您的文件，请稍等片刻...             │
│                                              │
│  您可以关闭此页面，稍后通过 Session ID      │
│  查询结果。                                  │
│                                              │
│  Session ID: abc-123-def-456                 │
└──────────────────────────────────────────────┘
```

---

## 步骤4: 获取结果

### 方式1: API下载（推荐）

```bash
# 使用返回的 Session ID
curl http://localhost:8013/api/download/abc-123-def-456 -o result.xlsx
```

### 方式2: 查看 n8n 执行历史

1. 访问 http://localhost:5678
2. 点击左侧 "Executions"
3. 找到最新的执行
4. 查看 "Download Result" 节点

---

## 🎉 完成！

你已经成功使用 Web 表单翻译了 Excel 文件！

---

## 📚 下一步

### 了解更多功能

- 📖 [Web 表单使用指南](./WEB_FORM_GUIDE.md) - 详细的功能说明
- 📖 [工作流目录](./docs/WORKFLOW_CATALOG.md) - 其他自动化工作流
- 📖 [实现方案](./docs/IMPLEMENTATION_PLAN.md) - 技术细节

### 自定义配置

- **添加新术语表**:
  ```bash
  curl -X POST http://localhost:8013/api/glossaries/upload \
    -F "file=@my_terms.json" \
    -F "glossary_id=my_terms"
  ```

- **修改表单字段**:
  1. 访问 http://localhost:5678
  2. 打开工作流 "Web Form Translation"
  3. 编辑 "Translation Form" 节点

### 高级用法

- **批量处理**: 使用命令行脚本批量翻译
- **定时任务**: 配置定时自动翻译
- **Webhook集成**: 与其他系统集成

---

## ❓ 常见问题

### Q: 表单提交后没反应？

**检查服务状态**:
```bash
# 检查后端
curl http://localhost:8013/api/database/health

# 查看日志
cd docker && docker-compose logs -f
```

### Q: 如何查看翻译进度？

**访问 n8n 执行页面**:
```
http://localhost:5678 → 点击 "Executions"
```

### Q: 术语表不生效？

**检查术语表列表**:
```bash
curl http://localhost:8013/api/glossaries/list
```

---

## 🆘 需要帮助？

- 📖 查看 [Web 表单使用指南](./WEB_FORM_GUIDE.md)
- 📖 查看 [故障排除](./docs/TROUBLESHOOTING.md)
- 📝 查看日志: `docker-compose logs -f`

---

## 🛑 停止服务

```bash
cd docker
docker-compose down
```

---

**开始翻译**: http://localhost:5678/form/translate 🎉
