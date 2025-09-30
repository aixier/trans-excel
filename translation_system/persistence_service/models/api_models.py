"""
API Data Models - Pydantic models for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============================================================================
# Request Models - Task 3.1
# ============================================================================

class SessionData(BaseModel):
    """Session data model for batch requests"""
    session_id: str = Field(..., description="会话ID (UUID)")
    filename: str = Field(..., description="文件名")
    file_path: str = Field(..., description="文件路径")
    status: str = Field(..., description="状态: pending, processing, completed, failed")
    game_info: Optional[Dict[str, Any]] = Field(None, description="游戏信息")
    llm_provider: str = Field(..., description="LLM提供商: openai, qwen, etc.")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    total_tasks: int = Field(0, ge=0, description="总任务数")
    completed_tasks: int = Field(0, ge=0, description="已完成任务数")
    failed_tasks: int = Field(0, ge=0, description="失败任务数")
    processing_tasks: int = Field(0, ge=0, description="处理中任务数")


class TaskData(BaseModel):
    """Task data model for batch requests"""
    task_id: str = Field(..., description="任务ID")
    session_id: str = Field(..., description="会话ID")
    batch_id: str = Field(..., description="批次ID")
    sheet_name: str = Field(..., description="工作表名")
    row_index: int = Field(..., ge=0, description="行索引")
    column_name: str = Field(..., description="列名")
    source_text: str = Field(..., description="源文本")
    target_text: Optional[str] = Field(None, description="翻译结果")
    context: Optional[str] = Field(None, description="上下文")
    status: str = Field(..., description="状态: pending, processing, completed, failed")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="置信度 (0-1)")
    error_message: Optional[str] = Field(None, description="错误信息")
    retry_count: int = Field(0, ge=0, description="重试次数")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    duration_ms: Optional[int] = Field(None, ge=0, description="耗时 (毫秒)")


class SessionBatchRequest(BaseModel):
    """Batch session request"""
    sessions: List[SessionData] = Field(..., description="会话列表")


class TaskBatchRequest(BaseModel):
    """Batch task request"""
    tasks: List[TaskData] = Field(..., description="任务列表")


# ============================================================================
# Response Models - Task 3.2
# ============================================================================

class BatchResponse(BaseModel):
    """Batch operation response"""
    status: str = Field(..., description="状态: accepted, rejected")
    count: int = Field(..., ge=0, description="接受的数量")
    timestamp: datetime = Field(..., description="时间戳")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FlushResponse(BaseModel):
    """Flush operation response"""
    status: str = Field(..., description="刷新状态: flushed, empty, error")
    sessions_written: int = Field(..., ge=0, description="写入的会话数")
    tasks_written: int = Field(..., ge=0, description="写入的任务数")
    duration_ms: int = Field(..., ge=0, description="耗时 (毫秒)")


class QueryResponse(BaseModel):
    """Query response with pagination"""
    total: int = Field(..., ge=0, description="总数")
    page: int = Field(..., ge=1, description="页码")
    page_size: int = Field(..., ge=1, description="每页大小")
    total_pages: int = Field(..., ge=0, description="总页数")
    items: List[Dict[str, Any]] = Field(..., description="数据项")


class SessionDetailResponse(BaseModel):
    """Single session detail response"""
    session_id: str
    filename: str
    file_path: str
    status: str
    game_info: Optional[Dict[str, Any]] = None
    llm_provider: str
    metadata: Optional[Dict[str, Any]] = None
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    processing_tasks: int
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TaskDetailResponse(BaseModel):
    """Single task detail response"""
    task_id: str
    session_id: str
    batch_id: str
    sheet_name: str
    row_index: int
    column_name: str
    source_text: str
    target_text: Optional[str] = None
    context: Optional[str] = None
    status: str
    confidence: Optional[float] = None
    error_message: Optional[str] = None
    retry_count: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RecoveryResponse(BaseModel):
    """Recovery response"""
    session_id: str
    session: Dict[str, Any]
    tasks_count: int
    tasks: List[Dict[str, Any]]
    restored_at: str


class DeleteResponse(BaseModel):
    """Delete operation response"""
    status: str = Field(..., description="状态: deleted")
    session_id: str = Field(..., description="被删除的会话ID")
    timestamp: datetime = Field(..., description="时间戳")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CleanupResponse(BaseModel):
    """Cleanup operation response"""
    deleted_sessions: int = Field(..., ge=0, description="删除的会话数")
    deleted_tasks: int = Field(..., ge=0, description="删除的任务数")
    dry_run: bool = Field(..., description="是否为试运行")
    timestamp: datetime = Field(..., description="时间戳")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StatsResponse(BaseModel):
    """Statistics response"""
    sessions: Dict[str, Any] = Field(..., description="会话统计")
    tasks: Dict[str, Any] = Field(..., description="任务统计")
    storage: Dict[str, Any] = Field(..., description="存储统计")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="健康状态: healthy, unhealthy")
    version: str = Field(..., description="服务版本")
    database: str = Field(..., description="数据库状态: healthy, unhealthy")
    buffer: Dict[str, Any] = Field(..., description="缓冲区统计")


class ErrorResponse(BaseModel):
    """Error response"""
    detail: str = Field(..., description="错误详情")
    error_code: str = Field(..., description="错误代码")
    timestamp: datetime = Field(..., description="时间戳")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ============================================================================
# Internal Models - Task 3.3
# ============================================================================

class Pagination(BaseModel):
    """Pagination parameters"""
    page: int = Field(1, ge=1, description="页码 (从1开始)")
    page_size: int = Field(20, ge=1, le=100, description="每页大小 (1-100)")
    sort_by: str = Field("created_at", description="排序字段")
    order: str = Field("desc", description="排序方向: asc, desc")


class SessionFilters(BaseModel):
    """Session query filters"""
    status: Optional[str] = Field(None, description="状态过滤")
    from_date: Optional[datetime] = Field(None, description="开始日期")
    to_date: Optional[datetime] = Field(None, description="结束日期")
    llm_provider: Optional[str] = Field(None, description="LLM提供商过滤")


class TaskFilters(BaseModel):
    """Task query filters"""
    session_id: Optional[str] = Field(None, description="会话ID过滤")
    status: Optional[str] = Field(None, description="状态过滤")
    sheet_name: Optional[str] = Field(None, description="工作表名过滤")
    from_date: Optional[datetime] = Field(None, description="开始日期")
    to_date: Optional[datetime] = Field(None, description="结束日期")


class QueryResult(BaseModel):
    """Internal query result"""
    total: int = Field(..., ge=0, description="总数")
    items: List[Dict[str, Any]] = Field(..., description="数据项")