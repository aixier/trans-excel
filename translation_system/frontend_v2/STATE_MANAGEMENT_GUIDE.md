# 翻译系统状态管理指南

**版本**: 2.0
**日期**: 2025-10-07
**原则**: 模块化设计 · 状态准确 · 可独立测试

---

## 目录

- [1. 核心问题与解决方案](#1-核心问题与解决方案)
- [2. 状态设计规范](#2-状态设计规范)
- [3. 状态流转详解](#3-状态流转详解)
- [4. API接口规范](#4-api接口规范)
- [5. 前端集成指南](#5-前端集成指南)
- [6. 实施检查清单](#6-实施检查清单)
- [7. 测试指南](#7-测试指南)

---

## 1. 核心问题与解决方案

### 1.1 竞态条件问题

**问题描述**：
```
Timeline:
T0   POST /api/tasks/split → 返回 {"status": "processing"}
T1   GET /api/tasks/split/status → {"status": "completed"}
T2   POST /api/execute/start → 404 Session not found
T42  session_manager.set_task_manager() 实际完成
```

**根本原因**：
- `status: "completed"` 表示**计算完成**，但不表示**数据持久化完成**
- 保存操作耗时0-42秒（需优化但不在本次范围）
- 前端误判可进入下一阶段

**解决方案**（模块化，不大改）：
1. 添加 `saving` 状态表示保存中
2. 添加 `ready_for_next_stage` 标志明确就绪度
3. 后端验证前置条件
4. 前端严格检查就绪标志

---

## 2. 状态设计规范

### 2.1 设计原则

```
✅ 状态必须反映系统实际就绪度
✅ 每个模块独立维护自己的状态
✅ 状态转换必须原子性
✅ 使用标志位明确就绪条件
✅ 可独立测试每个状态模块
```

### 2.2 会话全局状态

```python
# backend_v2/models/session_state.py (新建)
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime

class SessionStage(Enum):
    """会话全局阶段 - 粗粒度状态"""
    CREATED = "created"              # 会话已创建
    ANALYZED = "analyzed"            # 分析完成，可拆分
    SPLIT_COMPLETE = "split_complete"  # 拆分完成，可执行
    EXECUTING = "executing"          # 执行中
    COMPLETED = "completed"          # 全部完成，可下载
    FAILED = "failed"                # 失败

    def can_split(self) -> bool:
        """是否可以开始拆分"""
        return self == SessionStage.ANALYZED

    def can_execute(self) -> bool:
        """是否可以开始执行"""
        return self == SessionStage.SPLIT_COMPLETE

    def can_download(self) -> bool:
        """是否可以下载"""
        return self == SessionStage.COMPLETED


class SessionStatus:
    """会话状态容器 - 单一数据源"""
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.stage = SessionStage.CREATED
        self.updated_at = datetime.now()

    def update_stage(self, stage: SessionStage):
        """更新阶段"""
        self.stage = stage
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """序列化"""
        return {
            "session_id": self.session_id,
            "stage": self.stage.value,
            "updated_at": self.updated_at.isoformat()
        }
```

### 2.3 拆分阶段状态（独立模块）

```python
# backend_v2/services/split_state.py (新建)
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime

class SplitStatus(Enum):
    """拆分状态"""
    NOT_STARTED = "not_started"
    PROCESSING = "processing"    # 计算中
    SAVING = "saving"            # 保存中（关键新增）
    COMPLETED = "completed"      # 完成
    FAILED = "failed"

class SplitStage(Enum):
    """拆分内部阶段"""
    ANALYZING = "analyzing"      # 分析表格
    ALLOCATING = "allocating"    # 分配批次
    CREATING_DF = "creating_df"  # 创建DataFrame
    SAVING = "saving"            # 保存数据
    VERIFYING = "verifying"      # 验证完整性
    DONE = "done"

class SplitProgress:
    """拆分进度管理 - 独立可测试"""
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.status = SplitStatus.NOT_STARTED
        self.stage = SplitStage.ANALYZING
        self.progress: float = 0.0  # 0-100
        self.message: str = ""
        self.ready_for_next_stage: bool = False  # 关键标志
        self.metadata: Dict[str, Any] = {}
        self.error: Optional[str] = None
        self.updated_at = datetime.now()

    def update(self,
               status: Optional[SplitStatus] = None,
               stage: Optional[SplitStage] = None,
               progress: Optional[float] = None,
               message: Optional[str] = None):
        """更新进度"""
        if status:
            self.status = status
        if stage:
            self.stage = stage
        if progress is not None:
            self.progress = progress
        if message:
            self.message = message
        self.updated_at = datetime.now()

    def mark_saving(self):
        """标记为保存中 - 关键方法"""
        self.status = SplitStatus.SAVING
        self.stage = SplitStage.SAVING
        self.ready_for_next_stage = False
        self.updated_at = datetime.now()

    def mark_completed(self, metadata: Dict[str, Any]):
        """标记为完成 - 只有这里设置ready标志"""
        self.status = SplitStatus.COMPLETED
        self.stage = SplitStage.DONE
        self.progress = 100.0
        self.ready_for_next_stage = True  # 只有这里为True
        self.metadata = metadata
        self.updated_at = datetime.now()

    def mark_failed(self, error: str):
        """标记为失败"""
        self.status = SplitStatus.FAILED
        self.error = error
        self.ready_for_next_stage = False
        self.updated_at = datetime.now()

    def is_ready(self) -> bool:
        """是否就绪 - 供外部验证"""
        return (
            self.status == SplitStatus.COMPLETED and
            self.ready_for_next_stage is True
        )

    def to_dict(self) -> Dict[str, Any]:
        """序列化 - API返回格式"""
        data = {
            "session_id": self.session_id,
            "status": self.status.value,
            "stage": self.stage.value,
            "progress": self.progress,
            "message": self.message,
            "ready_for_next_stage": self.ready_for_next_stage,
            "updated_at": self.updated_at.isoformat()
        }
        if self.error:
            data["error"] = self.error
        if self.metadata:
            data["metadata"] = self.metadata
        return data
```

### 2.4 执行阶段状态（独立模块）

```python
# backend_v2/services/execution_state.py (新建)
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime

class ExecutionStatus(Enum):
    """执行状态"""
    IDLE = "idle"
    INITIALIZING = "initializing"  # 初始化中
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    COMPLETED = "completed"
    FAILED = "failed"

class ExecutionProgress:
    """执行进度管理 - 独立可测试"""
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.status = ExecutionStatus.IDLE
        self.ready_for_monitoring: bool = False  # 监控就绪标志
        self.ready_for_download: bool = False    # 下载就绪标志
        self.statistics: Dict[str, Any] = {
            "total": 0,
            "completed": 0,
            "failed": 0,
            "processing": 0
        }
        self.error: Optional[str] = None
        self.updated_at = datetime.now()

    def mark_initializing(self):
        """标记为初始化中"""
        self.status = ExecutionStatus.INITIALIZING
        self.ready_for_monitoring = False
        self.updated_at = datetime.now()

    def mark_running(self):
        """标记为运行中 - 监控就绪"""
        self.status = ExecutionStatus.RUNNING
        self.ready_for_monitoring = True  # 可以开始监控
        self.updated_at = datetime.now()

    def mark_completed(self):
        """标记为完成 - 下载就绪"""
        self.status = ExecutionStatus.COMPLETED
        self.ready_for_download = True  # 可以下载
        self.updated_at = datetime.now()

    def update_statistics(self, stats: Dict[str, Any]):
        """更新统计信息"""
        self.statistics.update(stats)
        self.updated_at = datetime.now()

    def is_ready_for_monitoring(self) -> bool:
        """是否可以监控"""
        return self.ready_for_monitoring

    def is_ready_for_download(self) -> bool:
        """是否可以下载"""
        return self.ready_for_download

    def to_dict(self) -> Dict[str, Any]:
        """序列化"""
        return {
            "session_id": self.session_id,
            "status": self.status.value,
            "ready_for_monitoring": self.ready_for_monitoring,
            "ready_for_download": self.ready_for_download,
            "statistics": self.statistics,
            "updated_at": self.updated_at.isoformat()
        }
```

### 2.5 集成到SessionData

```python
# backend_v2/utils/session_manager.py (修改)
from models.session_state import SessionStage, SessionStatus
from services.split_state import SplitProgress
from services.execution_state import ExecutionProgress

class SessionData:
    """会话数据容器"""
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()

        # 数据
        self.excel_df: Optional[ExcelDataFrame] = None
        self.task_manager: Optional[TaskDataFrameManager] = None
        self.game_info: Optional[GameInfo] = None
        self.analysis: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}

        # 状态管理（模块化）
        self.session_status = SessionStatus(session_id)
        self.split_progress: Optional[SplitProgress] = None
        self.execution_progress: Optional[ExecutionProgress] = None

    def init_split_progress(self) -> SplitProgress:
        """初始化拆分进度"""
        if not self.split_progress:
            self.split_progress = SplitProgress(self.session_id)
        return self.split_progress

    def init_execution_progress(self) -> ExecutionProgress:
        """初始化执行进度"""
        if not self.execution_progress:
            self.execution_progress = ExecutionProgress(self.session_id)
        return self.execution_progress
```

---

## 3. 状态流转详解

### 3.1 整体流程图

```
┌──────────┐  上传Excel   ┌──────────┐  配置拆分   ┌──────────────┐
│ CREATED  │ ──────────> │ ANALYZED │ ─────────> │ SPLIT_COMPLETE│
└──────────┘             └──────────┘            └───────┬────────┘
                                                         │
                                                         │ 开始执行
                                                         ▼
┌───────────┐  完成翻译  ┌────────────┐              ┌──────────┐
│ COMPLETED │ <───────── │ EXECUTING  │              │          │
└───────────┘            └────────────┘              └──────────┘
```

### 3.2 阶段1：上传分析（同步，无竞态）

```python
# backend_v2/api/analyze_api.py
@router.post("/upload")
async def upload_excel(file: UploadFile):
    """同步执行，返回即完成"""
    # 1. 加载Excel
    excel_df = loader.load_excel(file)

    # 2. 创建会话
    session_id = session_manager.create_session()
    session = session_manager.get_session(session_id)

    # 3. 保存数据
    session_manager.set_excel_df(session_id, excel_df)

    # 4. 分析
    analysis = analyzer.analyze(excel_df, game_info)
    session_manager.set_analysis(session_id, analysis)

    # 5. 更新状态
    session.session_status.update_stage(SessionStage.ANALYZED)

    return {
        "session_id": session_id,
        "stage": session.session_status.stage.value,
        "analysis": analysis
    }
```

### 3.3 阶段2：任务拆分（异步，需准确状态）

```python
# backend_v2/api/task_api.py
from services.split_state import SplitProgress

# 存储拆分进度（保持现有设计）
splitting_progress: Dict[str, SplitProgress] = {}

@router.post("/split")
async def split_tasks(request: SplitRequest, background_tasks: BackgroundTasks):
    """启动拆分任务"""
    session_id = request.session_id

    # 验证前置条件
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    if not session.session_status.stage.can_split():
        raise HTTPException(400, f"Cannot split in stage: {session.session_status.stage.value}")

    # 初始化进度
    split_progress = SplitProgress(session_id)
    split_progress.update(
        status=SplitStatus.PROCESSING,
        stage=SplitStage.ANALYZING,
        progress=0,
        message="开始拆分任务..."
    )
    splitting_progress[session_id] = split_progress

    # 启动后台任务
    background_tasks.add_task(_perform_split_async, request)

    return split_progress.to_dict()


async def _perform_split_async(request: SplitRequest):
    """后台拆分任务 - 准确的状态管理"""
    session_id = request.session_id
    split_progress = splitting_progress[session_id]

    try:
        # 阶段1: 分析表格 (0-70%)
        for idx, sheet in enumerate(sheets):
            progress = 10 + (idx / len(sheets)) * 60
            split_progress.update(
                stage=SplitStage.ANALYZING,
                progress=progress,
                message=f"处理表格 {sheet} ({idx+1}/{len(sheets)})"
            )
            tasks = process_sheet(sheet)
            await asyncio.sleep(0.01)

        # 阶段2: 分配批次 (70-85%)
        split_progress.update(
            stage=SplitStage.ALLOCATING,
            progress=85,
            message=f"分配批次 (共{len(tasks)}个任务)"
        )
        tasks = allocate_batches(tasks)

        # 阶段3: 创建DataFrame (85-90%)
        split_progress.update(
            stage=SplitStage.CREATING_DF,
            progress=90,
            message="创建任务数据表..."
        )
        task_manager.add_tasks_batch(tasks)

        # ✨ 关键：阶段4: 保存数据 (90-95%)
        split_progress.mark_saving()  # 明确标记为saving状态
        split_progress.update(progress=95, message="保存任务管理器...")

        success = session_manager.set_task_manager(session_id, task_manager)
        if not success:
            raise Exception("Failed to save task_manager")

        # 阶段5: 验证 (95-98%)
        split_progress.update(
            stage=SplitStage.VERIFYING,
            progress=98,
            message="验证数据完整性..."
        )
        verify = session_manager.get_task_manager(session_id)
        if not verify:
            raise Exception("Verification failed")

        # 阶段6: 完成 (100%)
        stats = task_manager.get_statistics()
        split_progress.mark_completed({
            "task_count": stats['total'],
            "batch_count": len(batches)
        })

        # 更新会话全局状态
        session = session_manager.get_session(session_id)
        session.session_status.update_stage(SessionStage.SPLIT_COMPLETE)

    except Exception as e:
        split_progress.mark_failed(str(e))


@router.get("/split/status/{session_id}")
async def get_split_status(session_id: str):
    """获取拆分状态"""
    # 检查进度
    if session_id in splitting_progress:
        return splitting_progress[session_id].to_dict()

    # 检查是否已完成（从旧会话恢复）
    task_manager = session_manager.get_task_manager(session_id)
    if task_manager:
        return {
            "session_id": session_id,
            "status": "completed",
            "ready_for_next_stage": True
        }

    raise HTTPException(404, "Split progress not found")
```

### 3.4 阶段3：执行翻译

```python
# backend_v2/api/execute_api.py
from services.execution_state import ExecutionProgress

@router.post("/start")
async def start_execution(request: ExecuteRequest):
    """启动执行 - 严格验证前置条件"""
    session_id = request.session_id

    # 验证1: 会话存在
    task_manager = session_manager.get_task_manager(session_id)
    if not task_manager:
        raise HTTPException(404, "Session not found")

    # 验证2: 拆分已完成且就绪
    split_progress = splitting_progress.get(session_id)
    if not split_progress or not split_progress.is_ready():
        raise HTTPException(400, "Session not ready: split not complete")

    # 验证3: 会话状态正确
    session = session_manager.get_session(session_id)
    if not session.session_status.stage.can_execute():
        raise HTTPException(400, f"Cannot execute in stage: {session.session_status.stage.value}")

    # 初始化执行进度
    exec_progress = session.init_execution_progress()
    exec_progress.mark_initializing()

    try:
        # 创建LLM provider
        llm_provider = LLMFactory.create_from_config_file(config, provider_name)

        # 启动执行（等待初始化完成）
        result = await worker_pool.start_execution(session_id, llm_provider)
        if result['status'] == 'error':
            raise HTTPException(400, result['message'])

        # 启动进度监控（等待初始化）
        await progress_tracker.start_progress_monitoring(session_id)
        await progress_tracker.wait_for_initialization(session_id, timeout=5.0)

        # 标记为运行中
        exec_progress.mark_running()
        session.session_status.update_stage(SessionStage.EXECUTING)

        return {
            **result,
            **exec_progress.to_dict()
        }

    except Exception as e:
        exec_progress.status = ExecutionStatus.FAILED
        raise HTTPException(500, str(e))
```

---

## 4. API接口规范

### 4.1 统一响应格式

所有API返回格式：

```typescript
interface ApiResponse {
    session_id: string;
    status: string;              // 模块状态
    stage?: string;              // 内部阶段（可选）
    progress?: number;           // 0-100
    message?: string;            // 用户消息
    ready_for_next_stage?: boolean;  // 就绪标志
    metadata?: any;              // 扩展数据
    error?: string;              // 错误信息
}
```

### 4.2 关键端点

#### POST /api/tasks/split
```json
// 立即返回
{
    "session_id": "abc123",
    "status": "processing",
    "stage": "analyzing",
    "progress": 0,
    "message": "开始拆分任务...",
    "ready_for_next_stage": false
}
```

#### GET /api/tasks/split/status/{session_id}
```json
// 保存中
{
    "session_id": "abc123",
    "status": "saving",      // ✨ 关键状态
    "stage": "saving",
    "progress": 95,
    "message": "保存任务管理器...",
    "ready_for_next_stage": false  // ✨ 不可进入下一阶段
}

// 完成
{
    "session_id": "abc123",
    "status": "completed",
    "stage": "done",
    "progress": 100,
    "message": "拆分完成",
    "ready_for_next_stage": true,  // ✨ 可进入下一阶段
    "metadata": {
        "task_count": 1250,
        "batch_count": 125
    }
}
```

#### POST /api/execute/start
```json
// 成功
{
    "session_id": "abc123",
    "status": "running",
    "ready_for_monitoring": true,  // ✨ 可立即监控
    "statistics": {
        "total": 1250,
        "completed": 0
    }
}

// 失败 (400)
{
    "detail": "Session not ready: split not complete"
}
```

---

## 5. 前端集成指南

### 5.1 拆分进度轮询

```javascript
// frontend_v2/js/pages/config.js
class ConfigPage {
    async pollSplitStatus() {
        try {
            const status = await API.getSplitStatus(this.sessionId);

            // 更新进度显示
            this.updateProgress(status.progress, status.message);

            // ✨ 严格检查就绪条件
            if (status.status === 'completed' && status.ready_for_next_stage === true) {
                // 可选：额外验证
                const verify = await API.getTaskStatus(this.sessionId);
                if (verify.has_tasks) {
                    this.onSplitComplete(status);
                    return;
                }
            }

            // 处理保存状态
            if (status.status === 'saving') {
                this.showSavingIndicator(status.message);
            }

            // 继续轮询
            if (['processing', 'saving'].includes(status.status)) {
                setTimeout(() => this.pollSplitStatus(), 2000);
            }

        } catch (error) {
            this.handleError(error);
        }
    }

    showSavingIndicator(message) {
        // 显示"正在保存"提示
        console.log('保存中:', message);
        // 可以添加特殊的UI指示器
    }
}
```

### 5.2 执行监控

```javascript
// frontend_v2/js/pages/execute.js
class ExecutePage {
    async startExecution() {
        try {
            const result = await API.startExecution(this.sessionId, this.options);

            // ✨ 检查监控就绪标志
            if (result.ready_for_monitoring) {
                // 立即开始轮询（无需延迟）
                this.startPolling();
            } else {
                // 延迟轮询
                setTimeout(() => this.startPolling(), 2000);
            }

        } catch (error) {
            if (error.message.includes('not ready')) {
                UIHelper.showToast('任务尚未准备好，请稍候', 'warning');
                window.location.hash = '#/config';
            } else {
                this.handleError(error);
            }
        }
    }

    async pollExecutionStatus() {
        try {
            const status = await API.getExecutionProgress(this.sessionId);

            this.updateProgress(status);

            if (status.ready_for_download) {
                this.onExecutionComplete();
                return;
            }

            // 继续轮询
            this.pollingTimer = setTimeout(() => {
                this.pollExecutionStatus();
            }, 2000);

        } catch (error) {
            // 不再容忍404（后端保证不返回404）
            this.handleError(error);
            this.stopPolling();
        }
    }
}
```

---

## 6. 实施检查清单

### 第一阶段：核心修复（1-2天）

**后端**：
- [ ] 创建 `backend_v2/models/session_state.py`
- [ ] 创建 `backend_v2/services/split_state.py`
- [ ] 创建 `backend_v2/services/execution_state.py`
- [ ] 修改 `SessionData` 集成状态模块
- [ ] 修改 `task_api.py` 使用 `SplitProgress`
- [ ] 添加 `mark_saving()` 调用在保存前
- [ ] 修改 `execute_api.py` 严格验证前置条件
- [ ] 添加 `is_ready()` 检查

**前端**：
- [ ] 修改 `config.js` 检查 `ready_for_next_stage`
- [ ] 添加 `saving` 状态处理
- [ ] 修改 `execute.js` 处理400错误
- [ ] 检查 `ready_for_monitoring` 标志
- [ ] 移除404容忍逻辑

**测试**：
- [ ] 测试拆分完成立即点击执行
- [ ] 测试保存状态显示
- [ ] 测试就绪标志验证
- [ ] 测试错误处理

### 第二阶段：优化改进（2-3天）

- [ ] 添加状态转换日志
- [ ] 性能监控（保存时间）
- [ ] 单元测试状态模块
- [ ] 集成测试完整流程
- [ ] 文档更新

---

## 7. 测试指南

### 7.1 状态模块单元测试

```python
# tests/test_split_state.py
import pytest
from services.split_state import SplitProgress, SplitStatus, SplitStage

def test_split_progress_initialization():
    """测试初始化"""
    progress = SplitProgress("test_session")
    assert progress.status == SplitStatus.NOT_STARTED
    assert progress.ready_for_next_stage is False

def test_mark_saving():
    """测试保存状态"""
    progress = SplitProgress("test_session")
    progress.mark_saving()

    assert progress.status == SplitStatus.SAVING
    assert progress.stage == SplitStage.SAVING
    assert progress.ready_for_next_stage is False

def test_mark_completed():
    """测试完成状态"""
    progress = SplitProgress("test_session")
    progress.mark_completed({"task_count": 100})

    assert progress.status == SplitStatus.COMPLETED
    assert progress.ready_for_next_stage is True
    assert progress.is_ready() is True

def test_is_ready_validation():
    """测试就绪验证"""
    progress = SplitProgress("test_session")

    # 初始状态：不就绪
    assert progress.is_ready() is False

    # 保存中：不就绪
    progress.mark_saving()
    assert progress.is_ready() is False

    # 完成：就绪
    progress.mark_completed({})
    assert progress.is_ready() is True
```

### 7.2 集成测试

```python
# tests/test_integration.py
import pytest
from fastapi.testclient import TestClient

def test_split_execute_workflow(client: TestClient):
    """测试完整工作流"""
    # 1. 上传
    response = client.post("/api/analyze/upload", files={"file": excel_file})
    session_id = response.json()["session_id"]

    # 2. 启动拆分
    response = client.post("/api/tasks/split", json={
        "session_id": session_id,
        "target_langs": ["PT"]
    })
    assert response.json()["ready_for_next_stage"] is False

    # 3. 轮询直到完成
    while True:
        response = client.get(f"/api/tasks/split/status/{session_id}")
        status = response.json()

        if status["status"] == "completed":
            assert status["ready_for_next_stage"] is True
            break

        time.sleep(1)

    # 4. 启动执行（应该成功）
    response = client.post("/api/execute/start", json={
        "session_id": session_id
    })
    assert response.status_code == 200
    assert response.json()["ready_for_monitoring"] is True
```

### 7.3 竞态测试

```python
def test_race_condition_prevention(client: TestClient):
    """测试竞态条件防护"""
    # 1. 启动拆分
    response = client.post("/api/tasks/split", json={
        "session_id": session_id,
        "target_langs": ["PT"]
    })

    # 2. 立即尝试执行（应该失败）
    response = client.post("/api/execute/start", json={
        "session_id": session_id
    })
    assert response.status_code == 400
    assert "not ready" in response.json()["detail"]

    # 3. 等待完成后执行（应该成功）
    # ... wait for completion
    response = client.post("/api/execute/start", json={
        "session_id": session_id
    })
    assert response.status_code == 200
```

---

## 8. 总结

### 关键改进

1. **模块化状态管理**
   - `SessionStatus`: 会话全局状态
   - `SplitProgress`: 拆分阶段状态（独立可测试）
   - `ExecutionProgress`: 执行阶段状态（独立可测试）

2. **准确的状态表示**
   - 添加 `saving` 状态
   - 明确 `ready_for_next_stage` 标志
   - 严格验证前置条件

3. **可测试性**
   - 每个状态模块独立
   - 提供单元测试
   - 提供集成测试

4. **避免耦合**
   - 状态模块不依赖具体实现
   - 通过标志位通信
   - 清晰的接口定义

### 实施原则

- ✅ 渐进式改进，不大改
- ✅ 模块化设计，低耦合
- ✅ 状态准确，无歧义
- ✅ 可独立测试
- ✅ 保持现有架构

---

**文档版本**: 2.0
**下一步**: 按检查清单逐步实施
