# Backend V2 API验证清单

## API端点完整列表

### 1. 文件上传模块
| API端点 | 方法 | 功能描述 | 请求参数 | 响应格式 | 验证状态 |
|---------|------|----------|----------|----------|----------|
| `/api/upload` | POST | 上传Excel文件 | FormData(file) | `{session_id, filename, status}` | ⬜ |
| `/api/upload/validate` | POST | 验证文件格式 | FormData(file) | `{valid, message, details}` | ⬜ |

### 2. 会话管理模块
| API端点 | 方法 | 功能描述 | 请求参数 | 响应格式 | 验证状态 |
|---------|------|----------|----------|----------|----------|
| `/api/sessions` | GET | 获取所有会话 | - | `[{session_id, filename, status, created_at}]` | ⬜ |
| `/api/sessions/{session_id}` | GET | 获取会话详情 | session_id | `{session_id, filename, status, metadata}` | ⬜ |
| `/api/sessions/{session_id}` | DELETE | 删除会话 | session_id | `{success, message}` | ⬜ |
| `/api/sessions/{session_id}/status` | GET | 获取会话状态 | session_id | `{status, progress, updated_at}` | ⬜ |

### 3. 文件分析模块
| API端点 | 方法 | 功能描述 | 请求参数 | 响应格式 | 验证状态 |
|---------|------|----------|----------|----------|----------|
| `/api/analyze/{session_id}` | POST | 分析Excel文件 | `{colors: [], detect_language: bool}` | `{sheets, total_cells, colored_cells, languages}` | ⬜ |
| `/api/analyze/{session_id}/preview` | GET | 获取预览数据 | `{sheet?, rows?}` | `{sheets: [{name, data, colors}]}` | ⬜ |
| `/api/analyze/{session_id}/statistics` | GET | 获取统计信息 | - | `{by_sheet, by_color, by_language}` | ⬜ |

### 4. 任务拆分模块
| API端点 | 方法 | 功能描述 | 请求参数 | 响应格式 | 验证状态 |
|---------|------|----------|----------|----------|----------|
| `/api/split/{session_id}` | POST | 执行任务拆分 | `{colors, source_lang, target_lang, strategy}` | `{task_count, groups, batches}` | ⬜ |
| `/api/split/{session_id}/tasks` | GET | 获取任务列表 | `{page?, limit?, status?}` | `{tasks: [], total, page}` | ⬜ |
| `/api/split/{session_id}/groups` | GET | 获取任务分组 | - | `{groups: [{id, count, status}]}` | ⬜ |

### 5. LLM配置模块
| API端点 | 方法 | 功能描述 | 请求参数 | 响应格式 | 验证状态 |
|---------|------|----------|----------|----------|----------|
| `/api/llm/providers` | GET | 获取可用提供商 | - | `[{name, models, status}]` | ⬜ |
| `/api/llm/config` | GET | 获取当前配置 | - | `{provider, model, parameters}` | ⬜ |
| `/api/llm/config` | POST | 更新LLM配置 | `{provider, model, api_key?, parameters}` | `{success, config}` | ⬜ |
| `/api/llm/test` | POST | 测试LLM连接 | `{provider, api_key}` | `{success, response_time, message}` | ⬜ |

### 6. 翻译执行模块
| API端点 | 方法 | 功能描述 | 请求参数 | 响应格式 | 验证状态 |
|---------|------|----------|----------|----------|----------|
| `/api/execute/{session_id}` | POST | 开始翻译执行 | `{batch_size?, max_workers?, use_batch_optimization?}` | `{execution_id, status}` | ⬜ |
| `/api/execute/{session_id}/pause` | POST | 暂停执行 | - | `{success, status}` | ⬜ |
| `/api/execute/{session_id}/resume` | POST | 恢复执行 | - | `{success, status}` | ⬜ |
| `/api/execute/{session_id}/cancel` | POST | 取消执行 | - | `{success, status}` | ⬜ |
| `/api/execute/{session_id}/status` | GET | 获取执行状态 | - | `{status, progress, errors}` | ⬜ |

### 7. 进度监控模块
| API端点 | 方法 | 功能描述 | 请求参数 | 响应格式 | 验证状态 |
|---------|------|----------|----------|----------|----------|
| `/api/progress/{session_id}` | GET | 获取当前进度 | - | `{total, completed, failed, rate, eta}` | ⬜ |
| `/api/progress/{session_id}/details` | GET | 获取详细进度 | - | `{by_batch, by_status, timeline}` | ⬜ |
| `/ws/progress/{session_id}` | WS | WebSocket实时进度 | - | `{type, data, timestamp}` | ⬜ |

### 8. 结果管理模块
| API端点 | 方法 | 功能描述 | 请求参数 | 响应格式 | 验证状态 |
|---------|------|----------|----------|----------|----------|
| `/api/results/{session_id}` | GET | 获取翻译结果 | `{page?, limit?, status?}` | `{results: [], total}` | ⬜ |
| `/api/results/{session_id}/{task_id}` | GET | 获取单个结果 | task_id | `{task_id, source, result, confidence}` | ⬜ |
| `/api/results/{session_id}/{task_id}` | PUT | 更新翻译结果 | `{result, is_final}` | `{success, task}` | ⬜ |
| `/api/results/{session_id}/statistics` | GET | 获取结果统计 | - | `{total, completed, quality_distribution}` | ⬜ |

### 9. 导出下载模块
| API端点 | 方法 | 功能描述 | 请求参数 | 响应格式 | 验证状态 |
|---------|------|----------|----------|----------|----------|
| `/api/export/{session_id}` | POST | 生成导出文件 | `{format?, include_metadata?}` | `{export_id, status}` | ⬜ |
| `/api/download/{session_id}` | GET | 下载Excel文件 | - | File (application/vnd.ms-excel) | ⬜ |
| `/api/download/{session_id}/status` | GET | 获取下载状态 | - | `{ready, file_size, created_at}` | ⬜ |

### 10. 监控管理模块
| API端点 | 方法 | 功能描述 | 请求参数 | 响应格式 | 验证状态 |
|---------|------|----------|----------|----------|----------|
| `/api/monitor/system` | GET | 系统监控信息 | - | `{cpu, memory, disk, connections}` | ⬜ |
| `/api/monitor/performance` | GET | 性能指标 | `{period?}` | `{response_times, throughput, error_rate}` | ⬜ |
| `/api/monitor/costs` | GET | 成本统计 | `{start_date?, end_date?}` | `{by_provider, by_model, total}` | ⬜ |
| `/ws/monitor` | WS | 实时监控WebSocket | - | `{type, metrics, timestamp}` | ⬜ |

### 11. 持久化模块
| API端点 | 方法 | 功能描述 | 请求参数 | 响应格式 | 验证状态 |
|---------|------|----------|----------|----------|----------|
| `/api/checkpoint/{session_id}` | GET | 获取检查点列表 | - | `[{checkpoint_id, created_at, progress}]` | ⬜ |
| `/api/checkpoint/{session_id}` | POST | 创建检查点 | `{type: 'manual'}` | `{checkpoint_id, success}` | ⬜ |
| `/api/checkpoint/{session_id}/restore` | POST | 恢复检查点 | `{checkpoint_id}` | `{success, restored_state}` | ⬜ |

### 12. 历史记录模块
| API端点 | 方法 | 功能描述 | 请求参数 | 响应格式 | 验证状态 |
|---------|------|----------|----------|----------|----------|
| `/api/history` | GET | 获取历史记录 | `{page?, limit?, start_date?, end_date?}` | `{records: [], total}` | ⬜ |
| `/api/history/{session_id}` | GET | 获取会话历史 | session_id | `{session, tasks, timeline}` | ⬜ |
| `/api/history/search` | POST | 搜索历史 | `{query, filters}` | `{results: [], count}` | ⬜ |

## 验证步骤模板

### 基础验证流程
```javascript
// 1. 健康检查
GET /api/health
期望: { status: "healthy", version: "2.0.0" }

// 2. API可用性测试
OPTIONS /api/*
期望: 返回允许的方法和CORS头

// 3. 错误处理测试
GET /api/invalid_endpoint
期望: { error: "Not Found", status: 404 }
```

### 功能验证流程
```javascript
// 完整翻译流程测试
async function testTranslationFlow() {
  // 1. 上传文件
  const uploadResponse = await uploadFile(testFile);
  const sessionId = uploadResponse.session_id;

  // 2. 分析文件
  const analyzeResponse = await analyzeFile(sessionId);

  // 3. 拆分任务
  const splitResponse = await splitTasks(sessionId, {
    colors: ['yellow', 'blue'],
    source_lang: 'CH',
    target_lang: 'PT'
  });

  // 4. 执行翻译
  const executeResponse = await executeTranslation(sessionId);

  // 5. 监控进度
  const ws = connectWebSocket(`/ws/progress/${sessionId}`);
  ws.on('progress_update', (data) => {
    console.log('Progress:', data);
  });

  // 6. 获取结果
  const results = await getResults(sessionId);

  // 7. 下载文件
  const file = await downloadFile(sessionId);

  return { success: true, sessionId };
}
```

## 性能基准测试

### 响应时间要求
| API类别 | 目标响应时间 | 最大响应时间 |
|---------|-------------|-------------|
| 查询类API | < 200ms | < 500ms |
| 上传API | < 1s/MB | < 2s/MB |
| 执行API | < 500ms | < 1s |
| 下载API | < 1s | < 3s |
| WebSocket | < 50ms | < 100ms |

### 并发测试
```javascript
// 并发测试配置
const concurrencyTests = {
  upload: { concurrent: 10, duration: '1m' },
  query: { concurrent: 100, duration: '1m' },
  websocket: { concurrent: 50, duration: '5m' }
};
```

## 错误场景测试

### 必须测试的错误场景
1. **无效session_id**: 404 Not Found
2. **文件过大**: 413 Payload Too Large
3. **无效文件格式**: 400 Bad Request
4. **API限流**: 429 Too Many Requests
5. **服务器错误**: 500 Internal Server Error
6. **超时错误**: 504 Gateway Timeout
7. **认证失败**: 401 Unauthorized
8. **权限不足**: 403 Forbidden

## 安全性测试

### 安全检查项
- [ ] XSS防护测试
- [ ] CSRF防护验证
- [ ] SQL注入测试
- [ ] 文件上传安全
- [ ] API密钥安全
- [ ] 会话安全
- [ ] 数据加密传输

## 兼容性测试

### 浏览器兼容性
- [ ] Chrome 90+
- [ ] Firefox 88+
- [ ] Safari 14+
- [ ] Edge 90+

### 设备兼容性
- [ ] Desktop (1920x1080)
- [ ] Laptop (1366x768)
- [ ] Tablet (768x1024)
- [ ] Mobile (375x667)

## 验证进度跟踪

### 阶段1完成标准
- [ ] 所有上传API测试通过
- [ ] 所有会话API测试通过
- [ ] 错误处理正确
- [ ] 性能达标

### 阶段2完成标准
- [ ] 分析功能正常
- [ ] 任务拆分准确
- [ ] 统计数据正确

### 最终验收标准
- [ ] 所有API端点验证通过
- [ ] 性能测试达标
- [ ] 安全测试通过
- [ ] 兼容性测试通过
- [ ] 端到端流程测试通过