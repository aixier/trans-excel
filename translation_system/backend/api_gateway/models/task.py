"""
API数据模型定义
"""
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import List, Optional, Dict, Any


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"           # 等待处理
    UPLOADING = "uploading"       # 文件上传中
    ANALYZING = "analyzing"       # 文件分析中
    TRANSLATING = "translating"   # 翻译中
    ITERATING = "iterating"       # 迭代翻译中
    COMPLETED = "completed"       # 完成
    FAILED = "failed"             # 失败
    CANCELLED = "cancelled"       # 已取消


class TaskProgress(BaseModel):
    """任务进度模型"""
    total_rows: int = Field(..., description="总行数")
    translated_rows: int = Field(..., description="已翻译行数")
    current_iteration: int = Field(..., description="当前迭代次数")
    max_iterations: int = Field(..., description="最大迭代次数")
    completion_percentage: float = Field(..., description="完成百分比")
    estimated_time_remaining: Optional[int] = Field(None, description="预计剩余时间(秒)")


class TranslationMetrics(BaseModel):
    """翻译统计指标"""
    total_api_calls: int = Field(..., description="API调用总次数")
    total_tokens_used: int = Field(..., description="使用Token总数")
    total_cost: float = Field(..., description="总费用")
    average_response_time: float = Field(..., description="平均响应时间")
    success_rate: float = Field(..., description="成功率")


# 请求模型

class TranslationUploadRequest(BaseModel):
    """翻译上传请求"""
    target_languages: str = Field(..., description="目标语言列表，逗号分隔")
    total_rows: int = Field(190, description="处理总行数")
    batch_size: int = Field(3, description="批次大小")
    max_concurrent: int = Field(10, description="最大并发数")
    region_code: str = Field("na", description="地区代码")
    game_background: Optional[str] = Field(None, description="游戏背景")


class ProjectCreateRequest(BaseModel):
    """项目创建请求"""
    name: str = Field(..., description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    target_languages: List[str] = Field(..., description="目标语言列表")
    game_background: Optional[str] = Field(None, description="游戏背景")
    region_code: str = Field("na", description="地区代码")


# 响应模型

class TaskResponse(BaseModel):
    """任务响应模型"""
    task_id: str = Field(..., description="任务ID")
    status: TaskStatus = Field(..., description="任务状态")
    message: str = Field(..., description="响应消息")
    created_at: datetime = Field(..., description="创建时间")


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str = Field(..., description="任务ID")
    status: TaskStatus = Field(..., description="任务状态")
    progress: TaskProgress = Field(..., description="任务进度")
    error_message: Optional[str] = Field(None, description="错误消息")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    download_url: Optional[str] = Field(None, description="下载链接")


class TaskProgressResponse(BaseModel):
    """任务进度响应 - 用于高频轮询"""
    task_id: str = Field(..., description="任务ID")
    status: TaskStatus = Field(..., description="任务状态")
    progress: TaskProgress = Field(..., description="进度详情")
    statistics: TranslationMetrics = Field(..., description="统计信息")
    last_updated: datetime = Field(..., description="最后更新时间")


class TaskListResponse(BaseModel):
    """任务列表响应"""
    tasks: List[TaskStatusResponse] = Field(..., description="任务列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="页码")
    limit: int = Field(..., description="每页数量")
    pages: int = Field(..., description="总页数")


class ProjectResponse(BaseModel):
    """项目响应模型"""
    id: str = Field(..., description="项目ID")
    name: str = Field(..., description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    target_languages: List[str] = Field(..., description="目标语言")
    status: str = Field(..., description="项目状态")
    created_at: datetime = Field(..., description="创建时间")


class ProjectSummaryResponse(BaseModel):
    """项目概览响应"""
    project: ProjectResponse = Field(..., description="项目信息")
    versions: List[Dict[str, Any]] = Field(..., description="版本列表")
    task_statistics: Dict[str, int] = Field(..., description="任务统计")
    progress: Dict[str, Any] = Field(..., description="总体进度")


# 错误响应模型

class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误消息")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")


class ValidationErrorResponse(BaseModel):
    """验证错误响应"""
    error: str = Field("validation_error", description="错误类型")
    message: str = Field(..., description="错误消息")
    field_errors: List[Dict[str, str]] = Field(..., description="字段错误列表")