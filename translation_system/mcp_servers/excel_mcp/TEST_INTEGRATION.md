# Excel MCP v2.0 Integration Test Guide

## 快速测试流程

### 前置条件

1. **启动 backend_service** (端口 9000)
```bash
cd /mnt/d/work/trans_excel/translation_system/mcp_servers/backend_service
python3 server.py
```

2. **启动 excel_mcp** (端口 8021)
```bash
cd /mnt/d/work/trans_excel/translation_system/mcp_servers/excel_mcp
python3 server.py --http
```

### 测试场景 1: Web UI 测试

#### 步骤
1. 浏览器访问: `http://localhost:8021/static/index.html`
2. **Step 1**: 上传 Excel 文件或输入测试 URL
   - 使用测试文件: `/mnt/d/work/trans_excel/test1.xlsx`
3. **Step 2**: 等待分析完成，查看统计信息
4. **Step 5**: 配置任务拆分
   - 源语言: EN (或自动检测)
   - 目标语言: 勾选 TR, TH, PT
   - 启用上下文提取
5. **Step 6**: 查看任务结果
   - 点击 "Get Tasks" 查看任务摘要
   - 点击 "Get Batches" 查看批次分布
6. **Step 7**: 导出任务
   - 选择格式: Excel
   - 包含上下文: ✅
   - 点击 "Export Tasks"

#### 预期结果
- ✅ 分析成功，显示表格统计
- ✅ 任务拆分完成，显示任务数/批次数/字符数
- ✅ 显示任务类型分布（normal/yellow/blue）
- ✅ 显示语言批次分布
- ✅ 导出成功，下载 Excel 文件

### 测试场景 2: MCP 工具直接测试

使用 curl 直接调用 MCP 工具:

#### 1. 分析 Excel
```bash
curl -X POST http://localhost:8021/mcp/tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "excel_analyze",
    "arguments": {
      "token": "test_token_123",
      "file_url": "http://example.com/test.xlsx",
      "options": {
        "detect_language": true,
        "detect_formats": true,
        "analyze_colors": true
      }
    }
  }'
```

响应示例:
```json
{
  "session_id": "excel_abc123",
  "status": "queued",
  "message": "Analysis task submitted to queue"
}
```

#### 2. 查询分析状态
```bash
curl -X POST http://localhost:8021/mcp/tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "excel_get_status",
    "arguments": {
      "token": "test_token_123",
      "session_id": "excel_abc123"
    }
  }'
```

#### 3. 拆分任务
```bash
curl -X POST http://localhost:8021/mcp/tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "excel_split_tasks",
    "arguments": {
      "token": "test_token_123",
      "session_id": "excel_abc123",
      "source_lang": null,
      "target_langs": ["TR", "TH", "PT"],
      "extract_context": true
    }
  }'
```

#### 4. 获取任务结果
```bash
curl -X POST http://localhost:8021/mcp/tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "excel_get_tasks",
    "arguments": {
      "token": "test_token_123",
      "session_id": "excel_abc123",
      "preview_limit": 10
    }
  }'
```

#### 5. 获取批次信息
```bash
curl -X POST http://localhost:8021/mcp/tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "excel_get_batches",
    "arguments": {
      "token": "test_token_123",
      "session_id": "excel_abc123"
    }
  }'
```

#### 6. 导出任务
```bash
curl -X POST http://localhost:8021/mcp/tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "excel_export_tasks",
    "arguments": {
      "token": "test_token_123",
      "session_id": "excel_abc123",
      "format": "excel",
      "include_context": true
    }
  }'
```

### 验证点

#### ✅ 功能验证
- [ ] Excel 上传和分析成功
- [ ] 语言检测准确
- [ ] 颜色检测正确（黄色/蓝色单元格）
- [ ] 任务拆分成功
- [ ] 批次分配合理（约50k字符/批次）
- [ ] 上下文提取完整
- [ ] 导出文件正确

#### ✅ 性能验证
- [ ] 大文件（>1000行）处理正常
- [ ] 异步处理不阻塞
- [ ] Session 正确管理
- [ ] 内存使用合理

#### ✅ 错误处理
- [ ] 无效 token 返回错误
- [ ] Session 不存在返回错误
- [ ] 文件格式错误正确处理
- [ ] 网络错误优雅处理

### 调试技巧

#### 查看日志
```bash
# Excel MCP 日志
tail -f /var/log/excel_mcp.log

# 或直接查看控制台输出
```

#### 检查 Session
```python
# 在 Python 控制台
from utils.session_manager import session_manager
session = session_manager.get("excel_abc123")
print(session.to_dict())
```

#### 验证颜色检测
```python
from utils.color_detector import is_yellow_color, is_blue_color

# 测试黄色
print(is_yellow_color("FFFFFF00"))  # True
print(is_yellow_color("FFFF00"))    # True

# 测试蓝色
print(is_blue_color("00B0F0"))      # True
```

### 常见问题

#### Q: Token 验证失败
**A**: 确保 backend_service 正在运行，使用正确的 token: `test_token_123`

#### Q: Session 不存在
**A**: 检查 session_id 是否正确，Session 有效期为8小时

#### Q: 颜色检测不准确
**A**: 查看 `config/color_config.yaml` 配置，调整颜色范围

#### Q: 批次分配不合理
**A**: 检查字符数统计是否正确，调整 `BATCH_SIZE` 常量

### 性能基准

| 文件大小 | 行数 | 分析耗时 | 拆分耗时 | 内存使用 |
|---------|------|---------|---------|---------|
| 1MB     | 500  | ~2s     | ~3s     | ~50MB   |
| 5MB     | 2500 | ~5s     | ~8s     | ~150MB  |
| 10MB    | 5000 | ~10s    | ~15s    | ~300MB  |

### 测试报告模板

```markdown
## Excel MCP v2.0 集成测试报告

**测试日期**: 2025-10-03
**测试环境**: 
- OS: Ubuntu 20.04
- Python: 3.10
- Excel MCP: v2.0.0

### 测试结果

#### 功能测试
- [x] Excel 分析
- [x] 任务拆分
- [x] 批次分配
- [x] 任务导出
- [x] 颜色检测
- [x] 上下文提取

#### 性能测试
- [x] 大文件处理
- [x] 并发请求
- [x] 内存使用

#### 问题记录
1. [已解决] Token 验证失败 - 更新为 test_token_123
2. [已解决] 导入路径错误 - 修正服务导入

### 结论
✅ 所有功能正常，可以发布 v2.0.0
```

---

**准备就绪！开始测试 Excel MCP v2.0！** 🚀
