"""
翻译服务API路由
基于架构文档的HTTP接口实现，支持文件上传和进度轮询
"""
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from datetime import datetime
from typing import List, Optional
import uuid
import logging

from database.connection import get_db, AsyncSession
from database.models import TranslationTask
from translation_core.translation_engine import TranslationEngine
from project_manager.manager import ProjectManager
from file_service.storage.oss_storage import OSSStorage
from ..models.task import (
    TranslationUploadRequest, TaskResponse, TaskStatusResponse,
    TaskProgressResponse, TaskListResponse, TaskStatus,
    TaskProgress, TranslationMetrics
)


router = APIRouter()
logger = logging.getLogger(__name__)


# 依赖注入
def get_translation_engine():
    """获取翻译引擎实例"""
    return TranslationEngine()


def get_project_manager():
    """获取项目管理器实例"""
    return ProjectManager(OSSStorage())


@router.post("/upload", response_model=TaskResponse)
async def upload_translation_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    target_languages: str = Form(..., description="目标语言列表，逗号分隔，如：pt,th,ind"),
    total_rows: int = Form(190, description="处理总行数"),
    batch_size: int = Form(3, description="批次大小"),
    max_concurrent: int = Form(10, description="最大并发数"),
    region_code: str = Form("na", description="地区代码"),
    game_background: Optional[str] = Form(None, description="游戏背景"),
    db: AsyncSession = Depends(get_db),
    translation_engine: TranslationEngine = Depends(get_translation_engine),
    project_manager: ProjectManager = Depends(get_project_manager)
):
    """
    上传翻译文件并开始翻译任务
    基于Demo的完整工作流程
    """
    try:
        # 验证文件格式
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Only Excel files are supported")

        # 解析目标语言
        target_languages_list = [lang.strip() for lang in target_languages.split(',')]
        if not target_languages_list:
            raise HTTPException(status_code=400, detail="Target languages cannot be empty")

        # 创建翻译任务记录
        task_id = str(uuid.uuid4())
        translation_task = TranslationTask(
            id=task_id,
            file_name=file.filename,
            target_languages=target_languages_list,
            total_rows=total_rows,
            batch_size=batch_size,
            max_concurrent=max_concurrent,
            max_iterations=5,  # 固定为5轮迭代
            region_code=region_code,
            game_background=game_background,
            status='uploading'
        )

        db.add(translation_task)
        await db.commit()

        # 保存上传的文件
        file_content = await file.read()
        file_path = f"temp/{task_id}_{file.filename}"

        # 这里简化处理，实际应该保存到临时目录
        with open(file_path, "wb") as f:
            f.write(file_content)

        logger.info(f"📁 文件上传成功: {file.filename}, 任务ID: {task_id}")

        # 后台启动翻译任务
        background_tasks.add_task(
            start_translation_task,
            db, task_id, file_path, target_languages_list,
            batch_size, max_concurrent, region_code, game_background,
            translation_engine
        )

        return TaskResponse(
            task_id=task_id,
            status=TaskStatus.UPLOADING,
            message="文件上传成功，翻译任务已启动",
            created_at=datetime.utcnow()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


async def start_translation_task(
    db: AsyncSession,
    task_id: str,
    file_path: str,
    target_languages: List[str],
    batch_size: int,
    max_concurrent: int,
    region_code: str,
    game_background: str,
    translation_engine: TranslationEngine
):
    """后台翻译任务执行函数"""
    try:
        logger.info(f"🚀 开始执行翻译任务: {task_id}")

        # 调用翻译引擎处理
        await translation_engine.process_translation_task(
            db=db,
            task_id=task_id,
            file_path=file_path,
            target_languages=target_languages,
            batch_size=batch_size,
            max_concurrent=max_concurrent,
            region_code=region_code,
            game_background=game_background
        )

    except Exception as e:
        logger.error(f"翻译任务执行失败: {task_id}, 错误: {e}")
        # 更新任务状态为失败
        task_query = await db.execute(
            "UPDATE translation_tasks SET status = 'failed', error_message = %s WHERE id = %s",
            (str(e), task_id)
        )
        await db.commit()


@router.get("/tasks/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    project_manager: ProjectManager = Depends(get_project_manager)
):
    """
    获取翻译任务状态
    基于HTTP轮询的进度查询接口
    """
    try:
        # 获取任务详细进度
        task_progress = await project_manager.get_task_progress(db, task_id)

        return TaskStatusResponse(
            task_id=task_progress['task_id'],
            status=TaskStatus(task_progress['status']),
            progress=TaskProgress(
                total_rows=task_progress['progress']['total_rows'],
                translated_rows=task_progress['progress']['translated_rows'],
                current_iteration=task_progress['progress']['current_iteration'],
                max_iterations=task_progress['progress']['max_iterations'],
                completion_percentage=task_progress['progress']['completion_percentage'],
                estimated_time_remaining=task_progress['progress']['estimated_time_remaining']
            ),
            error_message=task_progress['error_message'],
            created_at=task_progress['created_at'],
            updated_at=task_progress['updated_at'],
            download_url=None  # 完成后生成下载链接
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取任务状态失败: {task_id}, 错误: {e}")
        raise HTTPException(status_code=500, detail="Failed to get task status")


@router.get("/tasks/{task_id}/progress", response_model=TaskProgressResponse)
async def get_task_progress(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    project_manager: ProjectManager = Depends(get_project_manager)
):
    """
    获取任务进度详情 - 高频轮询接口
    优化的进度查询，返回最少必要信息
    """
    try:
        task_progress = await project_manager.get_task_progress(db, task_id)

        return TaskProgressResponse(
            task_id=task_progress['task_id'],
            status=TaskStatus(task_progress['status']),
            progress=TaskProgress(
                total_rows=task_progress['progress']['total_rows'],
                translated_rows=task_progress['progress']['translated_rows'],
                current_iteration=task_progress['progress']['current_iteration'],
                max_iterations=task_progress['progress']['max_iterations'],
                completion_percentage=task_progress['progress']['completion_percentage'],
                estimated_time_remaining=task_progress['progress']['estimated_time_remaining']
            ),
            statistics=TranslationMetrics(
                total_api_calls=task_progress['statistics']['total_api_calls'],
                total_tokens_used=task_progress['statistics']['total_tokens_used'],
                total_cost=task_progress['statistics']['total_cost'],
                average_response_time=0.0,  # 可以后续添加
                success_rate=0.95  # 可以后续添加
            ),
            last_updated=task_progress['updated_at']
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取任务进度失败: {task_id}, 错误: {e}")
        raise HTTPException(status_code=500, detail="Failed to get task progress")


@router.get("/tasks", response_model=TaskListResponse)
async def list_translation_tasks(
    status: Optional[TaskStatus] = None,
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """
    列出翻译任务
    支持状态筛选和分页
    """
    try:
        offset = (page - 1) * limit

        # 构建查询
        query = "SELECT * FROM translation_tasks"
        params = []

        if status:
            query += " WHERE status = %s"
            params.append(status.value)

        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        # 执行查询 (这里简化处理，实际应使用SQLAlchemy)
        tasks = []  # 实际应该查询数据库

        # 统计总数
        count_query = "SELECT COUNT(*) FROM translation_tasks"
        count_params = []
        if status:
            count_query += " WHERE status = %s"
            count_params.append(status.value)

        total = 0  # 实际应该查询数据库

        return TaskListResponse(
            tasks=[],  # 实际应该转换为TaskStatusResponse列表
            total=total,
            page=page,
            limit=limit,
            pages=(total + limit - 1) // limit if total > 0 else 0
        )

    except Exception as e:
        logger.error(f"列出翻译任务失败: {e}")
        raise HTTPException(status_code=500, detail="Failed to list tasks")


@router.delete("/tasks/{task_id}")
async def cancel_translation_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    取消翻译任务
    """
    try:
        # 查找任务
        # 这里简化处理，实际应该使用SQLAlchemy查询
        task = None  # await db.get(TranslationTask, task_id)

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # 只能取消未完成的任务
        if task.status in ['completed', 'failed', 'cancelled']:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel task with status: {task.status}"
            )

        # 更新任务状态
        # task.status = 'cancelled'
        # await db.commit()

        logger.info(f"✅ 翻译任务已取消: {task_id}")

        return {"message": "Task cancelled successfully", "task_id": task_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消翻译任务失败: {task_id}, 错误: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel task")


@router.get("/tasks/{task_id}/download")
async def download_translation_result(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    project_manager: ProjectManager = Depends(get_project_manager)
):
    """
    下载翻译结果
    """
    try:
        # 检查任务状态
        task_progress = await project_manager.get_task_progress(db, task_id)

        if task_progress['status'] != 'completed':
            raise HTTPException(
                status_code=400,
                detail="Task is not completed yet"
            )

        # 生成下载链接 (这里应该实际生成OSS临时链接)
        download_url = f"/download/{task_id}"  # 临时处理

        return {
            "download_url": download_url,
            "task_id": task_id,
            "expires_in": 3600  # 1小时过期
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成下载链接失败: {task_id}, 错误: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate download link")