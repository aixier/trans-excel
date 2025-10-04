# 页面设计：项目创建页

> **页面路径**: `#/create`
> **后端API**: `/api/analyze/*`
> **设计基于**: backend_v2 实际能力

---

## 1. 页面概述

### 1.1 核心功能
基于后端 `analyze_api.py` 的实际能力，此页面负责：
- 上传单个Excel文件（.xlsx/.xls格式）
- 可选填写游戏信息（game_info）
- 获取文件分析结果和Session ID
- 为后续流程建立数据基础

### 1.2 后端API限制
根据代码分析，后端当前：
- ✅ 支持单文件上传
- ✅ 支持.xlsx和.xls格式
- ✅ 支持可选的game_info JSON数据
- ❌ 不支持批量文件上传
- ❌ 不支持断点续传
- ❌ 不支持文件预检查
- ❌ 不支持云端导入

---

## 2. 功能设计

### 2.1 文件上传功能

#### 支持的功能（基于后端实际能力）
```python
# 基于 analyze_api.py 第19-86行
- 文件格式：仅支持 .xlsx 和 .xls
- 上传方式：multipart/form-data
- 文件大小：后端未限制，前端建议限制100MB
- 游戏信息：可选的JSON字符串
```

#### 前端实现
```javascript
// 上传表单数据结构
FormData = {
  file: File,           // Excel文件 (必需)
  game_info: JSON.stringify({  // 游戏信息 (可选)
    game_name: string,
    version: string,
    notes: string
  })
}
```

### 2.2 分析结果展示

#### 后端返回数据（基于实际API）
```python
# analyze_api.py 第73-76行返回结构
{
  "session_id": str,        # 唯一会话标识
  "analysis": {
    "statistics": {
      "sheet_count": int,    # Sheet数量
      "total_cells": int,    # 总单元格数
      "estimated_tasks": int, # 预估任务数
      "task_breakdown": {     # 任务类型分布
        "normal_tasks": int,
        "yellow_tasks": int,
        "blue_tasks": int
      }
    },
    "file_info": {
      "filename": str,
      "file_size": int,
      "sheets": [str]        # Sheet名称列表
    }
  }
}
```

---

## 3. 界面布局

### 3.1 页面结构
```
┌────────────────────────────────────────────────┐
│  [会话剩余: --:--]         页面标题             │
│         「开始新的Excel翻译项目」               │
├────────────────────────────────────────────────┤
│                                                 │
│  ┌───────────────────────────────────────┐     │
│  │                                         │     │
│  │           文件上传区域                  │     │
│  │                                         │     │
│  │      拖拽Excel文件到这里               │     │
│  │           或 [选择文件]                 │     │
│  │                                         │     │
│  │      支持格式：.xlsx, .xls             │     │
│  │                                         │     │
│  └───────────────────────────────────────┘     │
│                                                 │
│  ┌───────────────────────────────────────┐     │
│  │  游戏信息 (可选)                        │     │
│  │                                         │     │
│  │  游戏名称: [________________]          │     │
│  │  版本号:   [________________]          │     │
│  │  备注:     [________________]          │     │
│  │                                         │     │
│  └───────────────────────────────────────┘     │
│                                                 │
│         [上传并分析] (主按钮)                   │
│                                                 │
│  ┌───────────────────────────────────────┐     │
│  │  分析结果 (上传后显示)                  │     │
│  │                                         │     │
│  │  Session ID: xxx-xxx-xxx [复制]        │     │
│  │                                         │     │
│  │  文件统计：                             │     │
│  │  • Sheets: 12个                        │     │
│  │  • 单元格: 1,024个                     │     │
│  │  • 预估任务: 856个                     │     │
│  │                                         │     │
│  │  任务类型：                             │     │
│  │  • 常规翻译: 720个 (84%)               │     │
│  │  • 黄色重翻: 96个 (11%)                │     │
│  │  • 蓝色缩短: 40个 (5%)                 │     │
│  │                                         │     │
│  │         [继续配置 →]                   │     │
│  └───────────────────────────────────────┘     │
│                                                 │
└────────────────────────────────────────────────┘
```

### 3.2 响应式设计

#### 桌面端 (≥1024px)
- 容器宽度：最大1200px，居中显示
- 上传区域：600px宽，200px高
- 表单输入：单行排列
- 顶部显示会话剩余时间

#### 移动端 (<768px)
- 容器宽度：100% - 32px
- 上传区域：全宽，150px高
- 表单输入：垂直堆叠
- 按钮：全宽显示
- 会话时间显示在顶部固定栏

---

## 4. 交互设计

### 4.1 文件上传交互

#### 状态流转
```
1. 初始状态
   - 显示拖拽提示
   - 上传按钮可用

2. 文件选择后
   - 显示文件名和大小
   - 前端验证格式（.xlsx/.xls）
   - 显示"移除"按钮

3. 上传中
   - 显示上传进度条
   - 禁用所有输入
   - 显示"取消"按钮

4. 分析中
   - 显示"正在分析..."
   - 显示加载动画

5. 完成状态
   - 显示分析结果
   - Session ID自动复制到剪贴板
   - 显示"继续配置"按钮
```

### 4.2 错误处理

#### 基于后端错误响应
```python
# analyze_api.py 定义的错误情况
1. 文件格式错误 (400)
   - "Only Excel files are supported"

2. game_info JSON格式错误 (400)
   - "Invalid game_info JSON"

3. 处理错误 (500)
   - "Error processing file: {error_message}"
```

#### 前端错误提示
| 错误类型 | 用户提示 | 恢复建议 |
|---------|---------|---------|
| 格式错误 | "请上传Excel文件(.xlsx或.xls)" | 重新选择文件 |
| 文件过大 | "文件超过100MB限制" | 压缩或拆分文件 |
| 网络错误 | "网络连接失败，请重试" | 检查网络，重新上传 |
| 服务器错误 | "文件处理失败：{具体原因}" | 联系技术支持 |

---

## 5. API集成

### 5.1 上传文件接口

```javascript
// POST /api/analyze/upload
async function uploadFile(file, gameInfo) {
  const formData = new FormData();
  formData.append('file', file);

  if (gameInfo) {
    formData.append('game_info', JSON.stringify(gameInfo));
  }

  const response = await fetch('/api/analyze/upload', {
    method: 'POST',
    body: formData
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }

  return response.json();
}
```

### 5.2 查询分析状态

```javascript
// GET /api/analyze/status/{session_id}
async function getAnalysisStatus(sessionId) {
  const response = await fetch(`/api/analyze/status/${sessionId}`);

  if (response.status === 404) {
    throw new Error('Session not found');
  }

  return response.json();
}
```

---

## 6. 状态管理

### 6.1 页面状态
```javascript
pageState = {
  // 文件相关
  selectedFile: null,
  fileValidated: false,

  // 游戏信息
  gameInfo: {
    game_name: '',
    version: '',
    notes: ''
  },

  // 上传状态
  uploadStatus: 'idle', // idle | uploading | analyzing | completed | error
  uploadProgress: 0,

  // 分析结果
  sessionId: null,
  analysisResult: null,

  // 错误信息
  error: null
}
```

### 6.2 LocalStorage存储
```javascript
// 保存Session信息供后续页面使用（包含创建时间用于超时管理）
localStorage.setItem('currentSession', {
  sessionId: 'xxx-xxx-xxx',
  filename: 'game_texts.xlsx',
  createdAt: Date.now(), // 记录创建时间戳
  expiresAt: Date.now() + 8 * 60 * 60 * 1000, // 8小时后过期
  analysis: {...}
});

// 保存用户偏好
localStorage.setItem('userPreferences', {
  lastGameName: 'MyGame',
  lastVersion: '1.0.0'
});
```

### 6.3 会话超时管理
```javascript
// 会话生命周期管理（8小时限制）
class SessionManager {
  constructor() {
    this.SESSION_TIMEOUT = 8 * 60 * 60 * 1000; // 8小时
    this.WARNING_THRESHOLD = 30 * 60 * 1000; // 30分钟警告
  }

  createSession(sessionId, filename) {
    const now = Date.now();
    const session = {
      sessionId,
      filename,
      createdAt: now,
      expiresAt: now + this.SESSION_TIMEOUT,
      stage: 'created'
    };

    localStorage.setItem('currentSession', JSON.stringify(session));
    this.startTimeoutMonitoring(session);
    return session;
  }

  startTimeoutMonitoring(session) {
    // 计算剩余时间
    const checkTimeout = () => {
      const remaining = session.expiresAt - Date.now();

      if (remaining <= 0) {
        this.handleExpired();
      } else if (remaining <= this.WARNING_THRESHOLD) {
        this.showExpiryWarning(remaining);
      }

      // 更新UI显示
      this.updateExpiryDisplay(remaining);
    };

    // 每分钟检查一次
    setInterval(checkTimeout, 60000);
  }

  showExpiryWarning(remaining) {
    const minutes = Math.floor(remaining / 60000);

    showWarning({
      title: '会话即将过期',
      message: `您的翻译会话将在 ${minutes} 分钟后过期，请尽快完成操作`,
      actions: [
        { label: '继续配置', action: () => navigate('#/config') },
        { label: '知道了' }
      ]
    });
  }

  updateExpiryDisplay(remaining) {
    const hours = Math.floor(remaining / 3600000);
    const minutes = Math.floor((remaining % 3600000) / 60000);

    const display = document.getElementById('session-expiry');
    if (display) {
      display.textContent = `剩余: ${hours}小时${minutes}分钟`;

      // 根据剩余时间改变颜色
      if (remaining < this.WARNING_THRESHOLD) {
        display.classList.add('warning');
      }
    }
  }
}
```

---

## 7. 性能优化

### 7.1 文件上传优化
- 前端文件大小验证（避免上传超大文件）
- 显示上传进度和速度
- 失败自动重试（最多3次）

### 7.2 用户体验优化
- Session ID自动复制到剪贴板
- 记住上次填写的游戏信息
- 分析结果缓存，避免重复请求

---

## 8. 安全考虑

### 8.1 文件验证
```javascript
// 前端验证
function validateFile(file) {
  // 格式检查
  const validExtensions = ['.xlsx', '.xls'];
  const extension = file.name.substring(file.name.lastIndexOf('.'));
  if (!validExtensions.includes(extension.toLowerCase())) {
    throw new Error('Invalid file format');
  }

  // 大小检查
  const maxSize = 100 * 1024 * 1024; // 100MB
  if (file.size > maxSize) {
    throw new Error('File too large');
  }

  return true;
}
```

### 8.2 数据安全
- 游戏信息仅在客户端JSON序列化
- Session ID使用安全的随机生成
- 敏感信息不在URL中传递

---

## 9. 测试要点

### 9.1 功能测试
- [ ] 正常文件上传流程
- [ ] 各种Excel格式兼容性（.xlsx/.xls）
- [ ] 游戏信息可选填写
- [ ] Session ID正确生成和显示
- [ ] 分析结果正确展示

### 9.2 异常测试
- [ ] 非Excel文件拒绝上传
- [ ] 大文件上传处理
- [ ] 网络中断恢复
- [ ] 错误信息正确显示
- [ ] Session过期处理

### 9.3 兼容性测试
- [ ] Chrome/Firefox/Safari/Edge
- [ ] 移动端浏览器
- [ ] 不同分辨率适配

---

## 10. 实现注意事项

### 10.1 必须实现的功能
基于后端实际API：
1. 单文件上传（.xlsx/.xls）
2. 可选game_info填写
3. 显示分析结果
4. Session ID管理

### 10.2 不要实现的功能
后端不支持：
1. ❌ 批量文件上传
2. ❌ 断点续传
3. ❌ 文件预检查API
4. ❌ 云端文件导入
5. ❌ 历史文件列表API

### 10.3 可以前端优化的功能
1. ✅ 前端文件格式验证
2. ✅ 前端文件大小限制
3. ✅ LocalStorage缓存Session
4. ✅ 用户偏好记忆
5. ✅ 上传进度显示（基于XHR）

---

**文档版本**: 1.0
**基于后端**: backend_v2
**创建日期**: 2025-10-04
**作者**: Frontend Team