# 页面设计：结果导出页

> **页面路径**: `#/complete/:sessionId`
> **后端API**: `/api/download/*`, `/api/monitor/summary/*`
> **设计基于**: download_api.py, monitor_api.py

---

## 1. 页面概述

### 1.1 核心功能
基于后端实际能力，此页面负责：
- 展示翻译完成统计
- 预览翻译结果质量
- 下载翻译后的Excel文件
- 提供重新翻译入口

### 1.2 用户价值
- **成果获取**: 快速下载翻译结果
- **质量确认**: 了解翻译质量指标
- **决策支持**: 判断是否需要重新翻译
- **任务闭环**: 完成整个翻译流程

---

## 2. 功能设计

### 2.1 结果下载

#### API能力（基于download_api.py）
```python
# GET /api/download/{session_id}
# 返回：Excel文件流
# 特性：
# - 支持断点续传
# - 自动生成文件名
# - 保留原始格式
```

### 2.2 完成统计

#### API能力（基于monitor_api.py）
```python
# GET /api/monitor/summary/{session_id}
{
  "summary": {
    "total_tasks": 856,
    "completed": 854,
    "failed": 2,
    "success_rate": 99.77,
    "total_time": 305,        # 秒
    "average_confidence": 94.5
  },
  "language_stats": {
    "ZH": {"count": 428, "avg_confidence": 95.2},
    "EN": {"count": 428, "avg_confidence": 93.8}
  },
  "quality_distribution": {
    "high": 750,      # 置信度 > 90%
    "medium": 100,    # 置信度 70-90%
    "low": 4          # 置信度 < 70%
  }
}
```

---

## 3. 界面布局

### 3.1 页面结构

```
┌─────────────────────────────────────────────────┐
│  [会话剩余: 6:45] ⚠️请尽快下载                  │
│              翻译完成                           │
│         您的翻译任务已完成！                     │
├─────────────────────────────────────────────────┤
│                                                   │
│  ┌─────────────────────────────────────────┐    │
│  │         ✅ 翻译成功完成                  │    │
│  │                                          │    │
│  │      文件: translations.xlsx             │    │
│  │      耗时: 5分05秒                       │    │
│  │      完成率: 99.77%                      │    │
│  │                                          │    │
│  │    [📥 下载结果] (主按钮)                │    │
│  │                                          │    │
│  └─────────────────────────────────────────┘    │
│                                                   │
│  ┌─────────────────────────────────────────┐    │
│  │  质量概览                                │    │
│  ├─────────────────────────────────────────┤    │
│  │                                          │    │
│  │  整体置信度:  ████████████░  94.5%       │    │
│  │                                          │    │
│  │  质量分布:                               │    │
│  │  🟢 高质量 (>90%):  750 个 (87.6%)      │    │
│  │  🟡 中等质量:       100 个 (11.7%)      │    │
│  │  🔴 低质量:           4 个 (0.5%)       │    │
│  │  ⚫ 失败:             2 个 (0.2%)       │    │
│  │                                          │    │
│  └─────────────────────────────────────────┘    │
│                                                   │
│  ┌─────────────────────────────────────────┐    │
│  │  语言统计         │   性能指标           │    │
│  ├───────────────────┼─────────────────────┤    │
│  │                   │                     │    │
│  │ 中文翻译:         │ 总任务: 856         │    │
│  │   数量: 428       │ 成功: 854           │    │
│  │   置信度: 95.2%   │ 失败: 2             │    │
│  │                   │                     │    │
│  │ 英文翻译:         │ 总耗时: 5:05        │    │
│  │   数量: 428       │ 平均速度: 2.8/秒    │    │
│  │   置信度: 93.8%   │ Token用量: 156K     │    │
│  │                   │                     │    │
│  └─────────────────────────────────────────┘    │
│                                                   │
│  ┌─────────────────────────────────────────┐    │
│  │  失败任务 (2个)                          │    │
│  ├─────────────────────────────────────────┤    │
│  │                                          │    │
│  │  ❌ Task #234                            │    │
│  │     原文: "Complex technical term..."    │    │
│  │     原因: API超时                        │    │
│  │                                          │    │
│  │  ❌ Task #567                            │    │
│  │     原文: "Very long paragraph..."       │    │
│  │     原因: Token超限                      │    │
│  │                                          │    │
│  └─────────────────────────────────────────┘    │
│                                                   │
│  ┌─────────────────────────────────────────┐    │
│  │  后续操作                                │    │
│  │                                          │    │
│  │  [重新翻译失败任务]  [开始新项目]        │    │
│  │                                          │    │
│  │  [查看详细报告]  [导出日志]              │    │
│  │                                          │    │
│  └─────────────────────────────────────────┘    │
│                                                   │
└─────────────────────────────────────────────────┘
```

### 3.2 响应式设计

#### 桌面端 (≥1024px)
- 居中卡片布局，最大宽度900px
- 统计数据并排显示
- 详细信息完全展开

#### 平板端 (768px-1023px)
- 全宽卡片，留边距
- 统计数据2列布局
- 失败任务折叠显示

#### 移动端 (<768px)
- 全宽布局，最小边距
- 所有信息垂直堆叠
- 精简统计显示

---

## 4. 交互设计

### 4.1 下载交互

```
下载流程：
1. 点击下载按钮
2. 显示"准备中..."
3. 开始下载（浏览器接管）
4. 完成后显示"已下载"
```

### 4.2 质量可视化

```javascript
// 质量分布图表
const qualityChart = {
  type: 'doughnut',
  data: {
    labels: ['高质量', '中等', '低质量', '失败'],
    values: [750, 100, 4, 2],
    colors: ['#4CAF50', '#FFC107', '#FF5722', '#9E9E9E']
  }
};

// 置信度进度条
const confidenceBar = {
  value: 94.5,
  color: getColorByConfidence(94.5), // 动态颜色
  animated: true
};
```

### 4.3 失败处理

```
失败任务处理选项：
┌──────────────────┐
│  失败任务 (2)     │
├──────────────────┤
│ [全部重试]        │ → 批量重新翻译
│ [逐个处理]        │ → 手动编辑
│ [导出清单]        │ → 下载失败列表
│ [忽略]           │ → 接受当前结果
└──────────────────┘
```

---

## 5. 用户体验优化

### 5.1 视觉层次

```
信息优先级：
1. 下载按钮 - 最突出，主色调
2. 完成状态 - 大标题，成功图标
3. 质量指标 - 可视化图表
4. 详细统计 - 表格形式
5. 失败信息 - 可折叠面板
```

### 5.2 加载优化

- **预加载统计**: 执行完成前预取数据
- **渐进显示**: 先显示主要信息，详情异步加载
- **懒加载图表**: 视口可见时才渲染图表

### 5.3 操作引导

```
新用户引导：
1. 高亮下载按钮
2. 提示查看质量报告
3. 说明后续操作选项
```

---

## 6. API集成

### 6.1 获取完成统计

```javascript
async function getCompletionSummary(sessionId) {
  try {
    const response = await fetch(`/api/monitor/summary/${sessionId}`);

    if (!response.ok) {
      throw new Error('Failed to get summary');
    }

    const summary = await response.json();
    updateSummaryUI(summary);

  } catch (error) {
    console.error('Error fetching summary:', error);
    // 显示基础信息
    showBasicCompletion();
  }
}
```

### 6.2 下载文件

```javascript
async function downloadResult(sessionId) {
  // 更新UI状态
  setDownloadStatus('preparing');

  try {
    // 创建隐藏的下载链接
    const link = document.createElement('a');
    link.href = `/api/download/${sessionId}`;
    link.download = `translated_${sessionId}.xlsx`;

    // 触发下载
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    // 更新状态
    setDownloadStatus('completed');

    // 记录下载
    trackDownload(sessionId);

  } catch (error) {
    setDownloadStatus('error');
    showError('下载失败，请重试');
  }
}
```

### 6.3 重新翻译

```javascript
async function retryFailedTasks(sessionId) {
  const confirmation = confirm('确定要重新翻译失败的任务吗？');

  if (confirmation) {
    // 获取失败任务列表
    const failedTasks = await getFailedTasks(sessionId);

    // 创建新的翻译任务
    const newSession = await createRetrySession(sessionId, failedTasks);

    // 跳转到执行页
    window.location.hash = `#/execute/${newSession.id}`;
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

  // 完成统计
  summary: {
    totalTasks: 856,
    completed: 854,
    failed: 2,
    successRate: 99.77,
    totalTime: 305,
    averageConfidence: 94.5
  },

  // 质量数据
  qualityData: {
    distribution: null,
    languageStats: null
  },

  // 下载状态
  downloadStatus: 'ready', // ready|preparing|completed|error
  downloadCount: 0,

  // UI状态
  showFailedTasks: false,
  showDetailedReport: false
}
```

### 7.2 数据缓存

```javascript
// 缓存完成数据
function cacheSummary(sessionId, summary) {
  const cacheKey = `summary_${sessionId}`;

  localStorage.setItem(cacheKey, JSON.stringify({
    data: summary,
    timestamp: Date.now(),
    expires: Date.now() + 3600000 // 1小时
  }));
}

// 获取缓存
function getCachedSummary(sessionId) {
  const cacheKey = `summary_${sessionId}`;
  const cached = localStorage.getItem(cacheKey);

  if (cached) {
    const { data, expires } = JSON.parse(cached);

    if (Date.now() < expires) {
      return data;
    }
  }

  return null;
}
```

### 7.3 会话超时提醒

```javascript
// 完成页的超时管理（强调下载的紧迫性）
class CompletionTimeoutManager {
  constructor(sessionId) {
    const session = JSON.parse(localStorage.getItem('currentSession'));
    this.expiresAt = session.expiresAt;
    this.hasDownloaded = false;
    this.startMonitoring();
  }

  startMonitoring() {
    this.checkInterval = setInterval(() => {
      const remaining = this.expiresAt - Date.now();

      if (remaining <= 0) {
        this.handleExpired();
      } else if (remaining <= 30 * 60 * 1000 && !this.hasDownloaded) {
        // 30分钟内未下载，显示紧急提醒
        this.showUrgentWarning(remaining);
      }

      this.updateDisplay(remaining);
    }, 60000); // 每分钟检查
  }

  showUrgentWarning(remaining) {
    const minutes = Math.floor(remaining / 60000);

    showWarning({
      type: 'urgent',
      title: '⚠️ 数据即将清除',
      message: `您的翻译结果将在 ${minutes} 分钟后永久删除，请立即下载！`,
      persistent: true,
      actions: [
        {
          label: '立即下载',
          primary: true,
          action: () => {
            downloadResult();
            this.hasDownloaded = true;
          }
        }
      ]
    });

    // 添加视觉提醒
    document.body.classList.add('urgent-warning');

    // 闪烁下载按钮
    const downloadBtn = document.getElementById('download-btn');
    if (downloadBtn) {
      downloadBtn.classList.add('pulse-animation');
    }
  }

  updateDisplay(remaining) {
    const hours = Math.floor(remaining / 3600000);
    const minutes = Math.floor((remaining % 3600000) / 60000);

    const display = document.getElementById('session-expiry');
    if (display) {
      if (remaining < 30 * 60 * 1000) {
        display.innerHTML = `⚠️ 会话剩余: ${hours}:${minutes.toString().padStart(2, '0')} 请尽快下载`;
        display.classList.add('critical');
      } else {
        display.textContent = `会话剩余: ${hours}:${minutes.toString().padStart(2, '0')}`;
      }
    }
  }

  handleExpired() {
    clearInterval(this.checkInterval);

    if (!this.hasDownloaded) {
      showError({
        title: '会话已过期',
        message: '您的翻译结果已被清除，因为未在8小时内下载',
        blocking: true,
        action: () => window.location.hash = '#/create'
      });
    }
  }
}

// 页面加载时初始化
const timeoutManager = new CompletionTimeoutManager(sessionId);

// 下载成功后更新状态
function onDownloadComplete() {
  timeoutManager.hasDownloaded = true;

  showSuccess({
    title: '下载成功',
    message: '文件已保存到本地。提示：服务器数据将在会话过期后自动清除。',
    duration: 5000
  });
}
```

---

## 8. 异常场景处理

### 8.1 下载失败

```
处理策略：
1. 自动重试 → 最多3次
2. 提供备用链接 → 直接URL访问
3. 生成新链接 → 重新请求下载
4. 联系支持 → 显示错误代码
```

### 8.2 数据不一致

```
校验机制：
1. 总数校验 → completed + failed = total
2. 时间校验 → 确保时间戳合理
3. 状态校验 → 确保状态为completed
```

### 8.3 会话过期

```
恢复方案：
1. 检测过期 → API返回404
2. 尝试恢复 → 从localStorage查找
3. 提示用户 → 显示历史数据
4. 重新生成 → 基于缓存重建
```

---

## 9. 性能优化

### 9.1 关键指标

- **页面加载**: < 800ms
- **统计获取**: < 500ms
- **下载响应**: < 200ms
- **图表渲染**: < 300ms

### 9.2 优化策略

```javascript
// 1. 预取数据
if (executionProgress > 95) {
  prefetchSummary(sessionId);
}

// 2. 延迟加载
const loadCharts = () => {
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          renderChart(entry.target);
        }
      });
    });
  }
};

// 3. 图片懒加载
const lazyLoadIcons = () => {
  document.querySelectorAll('img[data-src]').forEach(img => {
    img.src = img.dataset.src;
  });
};
```

---

## 10. 测试要点

### 10.1 功能测试

- [ ] 统计数据准确性
- [ ] 下载功能完整性
- [ ] 失败任务处理
- [ ] 重新翻译流程
- [ ] 报告导出功能

### 10.2 边界测试

- [ ] 零失败任务显示
- [ ] 大量失败任务（>100）
- [ ] 超长文件名处理
- [ ] 并发下载请求

### 10.3 兼容性测试

- [ ] 不同浏览器下载行为
- [ ] 移动端下载体验
- [ ] 大文件下载（>50MB）
- [ ] 网络异常恢复

---

## 11. 设计规范

### 11.1 颜色定义

```css
/* 状态颜色 */
--success-color: #4CAF50;
--warning-color: #FFC107;
--error-color: #FF5722;
--info-color: #2196F3;

/* 质量等级 */
--quality-high: #4CAF50;
--quality-medium: #FFC107;
--quality-low: #FF5722;
```

### 11.2 动画效果

```css
/* 进度条动画 */
@keyframes progressFill {
  from { width: 0; }
  to { width: var(--progress); }
}

/* 成功图标动画 */
@keyframes successCheck {
  0% { stroke-dashoffset: 100; }
  100% { stroke-dashoffset: 0; }
}
```

---

**文档版本**: 1.0
**基于后端**: download_api.py, monitor_api.py
**创建日期**: 2025-10-04
**作者**: UX Team