# 页面设计：翻译执行页

> **页面路径**: `#/execute/:sessionId`
> **后端API**: `/api/execute/*`, `/api/monitor/*`, `/ws/progress`
> **设计基于**: execute_api.py, monitor_api.py, websocket_api.py

---

## 1. 页面概述

### 1.1 核心功能
基于后端实际能力，此页面负责：
- 启动翻译执行（execute_api）
- 实时监控进度（websocket_api）
- 显示详细状态（monitor_api）
- 控制执行流程（暂停/继续/停止）

### 1.2 用户价值
- **实时掌控**: 随时了解翻译进度
- **透明执行**: 查看正在处理的内容
- **灵活控制**: 按需暂停或停止
- **性能监控**: 了解翻译速度和质量

---

## 2. 功能设计

### 2.1 执行控制

#### API能力（基于execute_api.py）
```python
# 启动执行 - POST /api/execute/start
{
  "session_id": str,
  "provider": str,      # 可选：覆盖默认LLM
  "max_workers": int    # 可选：覆盖并发数
}

# 停止执行 - POST /api/execute/stop/{session_id}
# 暂停执行 - POST /api/execute/pause/{session_id}
# 继续执行 - POST /api/execute/resume/{session_id}
```

### 2.2 进度监控

#### WebSocket实时更新
```javascript
// 连接：ws://host/ws/progress/{session_id}
// 接收消息格式
{
  "type": "progress",
  "data": {
    "completed": 156,
    "total": 856,
    "processing": 8,
    "failed": 2,
    "rate": 12.5,        // 任务/秒
    "eta_seconds": 56    // 预计剩余时间
  }
}
```

#### 状态查询（monitor_api）
```python
# GET /api/monitor/status/{session_id}
{
  "status": "running" | "paused" | "completed",
  "progress": {
    "total": 856,
    "completed": 156,
    "processing": 8,
    "pending": 690,
    "failed": 2
  },
  "performance": {
    "elapsed_time": 125,      # 秒
    "average_speed": 1.2,     # 任务/秒
    "success_rate": 98.7      # 百分比
  },
  "recent_completions": [...]
}
```

---

## 3. 界面布局

### 3.1 页面结构

```
┌─────────────────────────────────────────────────┐
│  [会话剩余: 7:15] [🟢 实时连接]                 │
│             翻译执行中心                         │
│      Session: xxx-xxx [文件名.xlsx]             │
├─────────────────────────────────────────────────┤
│                                                   │
│  ┌─────────────────────────────────────────┐    │
│  │          总体进度                        │    │
│  │                                          │    │
│  │  ████████████░░░░░░░░░░░  156/856       │    │
│  │           18.2%                          │    │
│  │                                          │    │
│  │  预计剩余: 5分30秒  速度: 12任务/秒     │    │
│  └─────────────────────────────────────────┘    │
│                                                   │
│  ┌─────────────────────────────────────────┐    │
│  │      控制面板                            │    │
│  │                                          │    │
│  │  [暂停] [停止] [设置]                   │    │
│  │                                          │    │
│  │  并发数: [8 ▼]  LLM: [OpenAI ▼]        │    │
│  └─────────────────────────────────────────┘    │
│                                                   │
│  ┌─────────────────────────────────────────┐    │
│  │     实时状态      │    性能指标          │    │
│  ├───────────────────┼─────────────────────┤    │
│  │                   │                     │    │
│  │ 🟢 完成: 156      │ ⚡ 速度: 12/秒     │    │
│  │ 🔵 处理中: 8      │ ⏱️ 已用: 2:05      │    │
│  │ ⚫ 待处理: 690    │ 📊 成功率: 98.7%   │    │
│  │ 🔴 失败: 2        │ 💰 Token: 125,000  │    │
│  │                   │                     │    │
│  └─────────────────────────────────────────┘    │
│                                                   │
│  ┌─────────────────────────────────────────┐    │
│  │  当前处理任务 (8个并发)                  │    │
│  ├─────────────────────────────────────────┤    │
│  │                                          │    │
│  │  任务#0142  TR → ZH  处理中 3秒        │    │
│  │  "Merhaba dünya" → "..."                │    │
│  │                                          │    │
│  │  任务#0143  TR → EN  处理中 2秒        │    │
│  │  "Günaydın" → "..."                     │    │
│  │                                          │    │
│  │  [展开更多...]                           │    │
│  └─────────────────────────────────────────┘    │
│                                                   │
│  ┌─────────────────────────────────────────┐    │
│  │  最近完成 (最新10个)                     │    │
│  ├─────────────────────────────────────────┤    │
│  │                                          │    │
│  │  ✅ #0141 "Teşekkürler" → "谢谢"       │    │
│  │     置信度: 98%  耗时: 1.2秒           │    │
│  │                                          │    │
│  │  ✅ #0140 "İyi günler" → "Good day"    │    │
│  │     置信度: 95%  耗时: 0.8秒           │    │
│  │                                          │    │
│  │  [查看全部...]                           │    │
│  └─────────────────────────────────────────┘    │
│                                                   │
└─────────────────────────────────────────────────┘
```

### 3.2 响应式设计

#### 桌面端 (≥1024px)
- 三栏布局：进度、状态、详情
- 实时任务并排显示
- 详细信息全部展开

#### 平板端 (768px-1023px)
- 双栏布局：主要信息+次要信息
- 标签页切换详细内容

#### 移动端 (<768px)
- 单栏布局，信息垂直堆叠
- 折叠面板显示详情
- 精简控制按钮

---

## 4. 交互设计

### 4.1 实时更新机制

```javascript
// WebSocket连接生命周期
1. 页面加载 → 建立WebSocket连接
2. 接收消息 → 更新UI（无刷新）
3. 连接断开 → 自动重连（指数退避）
4. 页面离开 → 关闭连接
```

### 4.2 状态管理

```
执行状态流转：
┌─────────┐  start   ┌─────────┐  pause   ┌─────────┐
│ Ready   │ -------> │ Running │ -------> │ Paused  │
└─────────┘          └─────────┘          └─────────┘
                          │                     │
                          │ stop            resume│
                          ↓                     ↓
                    ┌─────────┐           ┌─────────┐
                    │ Stopped │           │ Running │
                    └─────────┘           └─────────┘
                          │
                    complete│
                          ↓
                    ┌──────────┐
                    │ Completed│
                    └──────────┘
```

### 4.3 错误处理

| 错误类型 | 用户提示 | 自动恢复 |
|---------|---------|----------|
| WebSocket断开 | "连接中断，重连中..." | 自动重连3次 |
| 任务失败 | "任务#xxx失败：{原因}" | 记录并继续 |
| 批量失败 | "多个任务失败，查看详情" | 显示失败列表 |
| 执行停止 | "执行已停止" | 保存进度 |

---

## 5. 用户体验优化

### 5.1 进度可视化

```
视觉层次：
1. 主进度条 - 最突出，实时动画
2. 百分比 - 大字体，居中显示
3. 预计时间 - 动态更新，智能预测
4. 速度指标 - 趋势图标（↑↓→）
```

### 5.2 性能优化

- **批量更新**: 100ms收集更新，批量渲染
- **虚拟滚动**: 任务列表超过50个时启用
- **防抖处理**: 频繁更新防抖50ms
- **增量渲染**: 仅更新变化的DOM

### 5.3 交互反馈

- **操作确认**: 暂停/停止需二次确认
- **状态过渡**: 平滑动画过渡
- **声音提示**: 完成时可选声音提醒
- **浏览器通知**: 后台运行时推送通知

---

## 6. API集成

### 6.1 启动执行（包含单session限制检查）

```javascript
// 启动翻译执行（后端同时只能执行1个session）
async function startExecution(sessionId, options = {}) {
  // 先检查是否有其他任务正在执行
  const globalStatus = await checkGlobalExecutionStatus();

  if (globalStatus.is_executing && globalStatus.current_session_id !== sessionId) {
    // 有其他任务正在执行，显示冲突提示
    showExecutionConflict(globalStatus.current_session_id);
    return;
  }

  // 正常启动执行
  const response = await fetch('/api/execute/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      provider: options.provider,
      max_workers: options.maxWorkers
    })
  });

  if (response.ok) {
    // 建立WebSocket连接
    connectWebSocket(sessionId);
  } else if (response.status === 400) {
    const error = await response.json();
    if (error.detail.includes('already running')) {
      // 已有任务执行中
      showExecutionConflict(error.current_session_id);
    }
  }
}

// 检查全局执行状态
async function checkGlobalExecutionStatus() {
  // 注意：此API可能需要后端添加
  try {
    const response = await fetch('/api/execute/status');
    return await response.json();
  } catch {
    // 如果API不存在，返回默认值
    return { is_executing: false };
  }
}

// 显示执行冲突提示
function showExecutionConflict(currentSessionId) {
  showDialog({
    type: 'warning',
    title: '无法启动翻译',
    message: '系统当前正在执行其他翻译任务，请等待完成后再试',
    details: `正在执行的会话: ${currentSessionId}`,
    actions: [
      {
        label: '查看当前任务',
        action: () => window.location.hash = `#/execute/${currentSessionId}`
      },
      {
        label: '等待完成',
        action: () => waitForCompletion()
      },
      { label: '取消' }
    ]
  });
}

// 等待当前任务完成
async function waitForCompletion() {
  showProgress({
    title: '等待中...',
    message: '当前有任务正在执行，完成后将自动开始您的任务'
  });

  const checkInterval = setInterval(async () => {
    const status = await checkGlobalExecutionStatus();
    if (!status.is_executing) {
      clearInterval(checkInterval);
      // 自动启动
      startExecution(sessionId);
    }
  }, 5000); // 每5秒检查一次
}
```

### 6.2 WebSocket连接（优化断开体验）

```javascript
class WebSocketManager {
  constructor(sessionId) {
    this.sessionId = sessionId;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 3;
    this.isPolling = false;
    this.pollingInterval = null;
  }

  connect() {
    try {
      this.ws = new WebSocket(`ws://${host}/ws/progress/${this.sessionId}`);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        this.stopPolling();
        this.updateConnectionStatus('connected');
      };

      this.ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        this.handleProgressUpdate(message.data);
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.handleDisconnect();
      };

      this.ws.onclose = () => {
        console.log('WebSocket closed');
        this.handleDisconnect();
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      this.handleDisconnect();
    }
  }

  handleDisconnect() {
    this.updateConnectionStatus('disconnected');

    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      // 尝试重连
      this.reconnectAttempts++;
      const delay = Math.pow(2, this.reconnectAttempts) * 1000;

      console.log(`Reconnecting in ${delay}ms... (attempt ${this.reconnectAttempts})`);

      setTimeout(() => this.connect(), delay);
    } else {
      // 超过重连次数，切换到HTTP轮询
      this.switchToPolling();
    }
  }

  switchToPolling() {
    if (this.isPolling) return; // 避免重复启动

    this.isPolling = true;
    this.updateConnectionStatus('polling');

    showToast('已切换到兼容模式，继续获取进度更新', { type: 'info' });

    // 立即执行一次轮询
    this.pollStatus();

    // 设置轮询间隔
    this.pollingInterval = setInterval(() => {
      this.pollStatus();
    }, 2000); // 每2秒轮询

    // 后台继续尝试WebSocket重连
    this.backgroundReconnect();
  }

  async pollStatus() {
    try {
      const response = await fetch(`/api/monitor/status/${this.sessionId}`);
      const data = await response.json();
      this.handleProgressUpdate(data.progress);
    } catch (error) {
      console.error('Polling error:', error);
    }
  }

  backgroundReconnect() {
    // 30秒后尝试重新建立WebSocket
    setTimeout(() => {
      if (this.isPolling) {
        console.log('Attempting WebSocket reconnection...');

        const testWs = new WebSocket(`ws://${host}/ws/progress/${this.sessionId}`);

        testWs.onopen = () => {
          // 重连成功，停止轮询，使用新连接
          this.stopPolling();
          this.ws = testWs;
          this.isPolling = false;
          this.reconnectAttempts = 0;
          this.updateConnectionStatus('connected');

          showToast('已恢复实时连接', { type: 'success' });

          // 设置消息处理
          testWs.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleProgressUpdate(message.data);
          };

          testWs.onerror = () => this.handleDisconnect();
          testWs.onclose = () => this.handleDisconnect();
        };

        testWs.onerror = () => {
          testWs.close();
          // 失败了，继续轮询，稍后再试
          this.backgroundReconnect();
        };
      }
    }, 30000); // 30秒后重试
  }

  stopPolling() {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = null;
    }
    this.isPolling = false;
  }

  handleProgressUpdate(data) {
    // 统一的进度更新处理
    updateProgressUI(data);
  }

  updateConnectionStatus(status) {
    const indicator = document.getElementById('connection-status');
    if (indicator) {
      switch (status) {
        case 'connected':
          indicator.innerHTML = '🟢 实时连接';
          indicator.className = 'status-connected';
          break;
        case 'polling':
          indicator.innerHTML = '🟡 兼容模式';
          indicator.className = 'status-polling';
          break;
        case 'disconnected':
          indicator.innerHTML = '🔴 连接中...';
          indicator.className = 'status-disconnected';
          break;
      }
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
    this.stopPolling();
  }
}

// 使用示例
const wsManager = new WebSocketManager(sessionId);
wsManager.connect();
```

### 6.3 状态轮询（备用）

```javascript
// WebSocket失败时的备用方案
async function pollStatus(sessionId) {
  const response = await fetch(`/api/monitor/status/${sessionId}`);
  const status = await response.json();
  updateUI(status);

  if (status.status !== 'completed') {
    setTimeout(() => pollStatus(sessionId), 2000);
  }
}
```

---

## 7. 状态管理

### 7.1 页面状态

```javascript
pageState = {
  // 会话信息
  sessionId: 'xxx-xxx',
  fileName: 'translations.xlsx',

  // 执行状态
  executionStatus: 'running', // ready|running|paused|stopped|completed

  // 进度数据
  progress: {
    total: 856,
    completed: 0,
    processing: 0,
    failed: 0,
    pending: 856
  },

  // 性能指标
  performance: {
    startTime: Date.now(),
    elapsedTime: 0,
    averageSpeed: 0,
    currentSpeed: 0,
    estimatedTime: 0
  },

  // WebSocket
  wsConnection: null,
  wsStatus: 'disconnected', // connecting|connected|disconnected

  // UI状态
  showDetails: false,
  selectedTab: 'current', // current|completed|failed
}
```

### 7.2 数据持久化

```javascript
// 保存执行状态到localStorage
function saveExecutionState() {
  localStorage.setItem(`execution_${sessionId}`, JSON.stringify({
    status: pageState.executionStatus,
    progress: pageState.progress,
    startTime: pageState.performance.startTime,
    lastUpdate: Date.now()
  }));
}

// 恢复执行状态
function restoreExecutionState() {
  const saved = localStorage.getItem(`execution_${sessionId}`);
  if (saved) {
    const state = JSON.parse(saved);
    // 恢复状态并继续监控
  }
}
```

---

## 8. 异常场景处理

### 8.1 网络中断

```
处理流程：
1. 检测断开 → 显示重连提示
2. 自动重连 → 指数退避（1s, 2s, 4s...）
3. 重连成功 → 恢复进度更新
4. 重连失败 → 切换到轮询模式
```

### 8.2 执行异常

```
异常类型：
- LLM服务异常 → 自动重试3次
- 配额超限 → 暂停并提示
- 任务超时 → 标记失败，继续其他
- 批量失败 → 触发告警阈值
```

### 8.3 页面刷新

```
恢复机制：
1. 检查localStorage → 找到未完成执行
2. 提示用户 → "发现未完成的翻译任务"
3. 用户确认 → 恢复监控或放弃
4. 继续执行 → 重建WebSocket连接
```

---

## 9. 性能指标

### 9.1 关键指标

- **首屏加载**: < 1秒
- **WebSocket延迟**: < 100ms
- **UI更新频率**: 10 FPS
- **内存占用**: < 50MB

### 9.2 优化策略

- 使用requestAnimationFrame优化动画
- 实施虚拟滚动处理大量任务
- 采用Web Worker处理数据计算
- 延迟加载非关键组件

---

## 10. 测试要点

### 10.1 功能测试
- [ ] 执行控制（启动/暂停/继续/停止）
- [ ] WebSocket实时更新
- [ ] 进度计算准确性
- [ ] 错误恢复机制

### 10.2 性能测试
- [ ] 大量任务（>1000）渲染性能
- [ ] 长时间运行内存泄漏
- [ ] 网络异常恢复时间

### 10.3 兼容性测试
- [ ] 不同浏览器WebSocket支持
- [ ] 移动端触控交互
- [ ] 后台运行状态保持

---

**文档版本**: 1.0
**基于后端**: execute_api.py, monitor_api.py, websocket_api.py
**创建日期**: 2025-10-04
**作者**: UX Team