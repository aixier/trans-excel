"""
翻译工作台专用API路由
专业翻译工作流：上传 → 分析 → 配置 → 翻译 → 跟踪
"""
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from datetime import datetime
from typing import List, Optional
import uuid
import logging
import pandas as pd
import os

from database.connection import get_db, AsyncSession
from database.models import TranslationTask
from translation_core.translation_engine import TranslationEngine
from project_manager.manager import ProjectManager
from file_service.storage.oss_storage import OSSStorage
from ..models.task import TaskResponse, TaskStatus
from pydantic import BaseModel

router = APIRouter(tags=["workspace"])
logger = logging.getLogger(__name__)


class FileUploadResponse(BaseModel):
    """文件上传响应"""
    file_id: str
    file_name: str
    file_size: int
    analysis: dict
    status: str
    created_at: datetime


class StartTranslationRequest(BaseModel):
    """开始翻译请求"""
    target_languages: List[str]
    project_id: Optional[str] = None  # 项目ID，用于术语管理
    sheet_names: Optional[List[str]] = None
    batch_size: int = 10
    max_concurrent: int = 20
    region_code: str = "auto"
    game_background: Optional[str] = None
    selected_ranges: Optional[List[str]] = None


# 依赖注入
def get_translation_engine():
    """获取翻译引擎实例"""
    return TranslationEngine()


def get_project_manager():
    """获取项目管理器实例"""
    return ProjectManager(OSSStorage())


@router.post("/files/upload", response_model=FileUploadResponse)
async def upload_file_only(
    file: UploadFile = File(...),
    project_id: Optional[str] = Form("default"),
    db: AsyncSession = Depends(get_db)
):
    """
    仅上传文件到服务器，进行智能分析但不开始翻译
    翻译工作台专用接口
    """
    try:
        # 验证文件格式
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Only Excel files are supported")

        # 生成文件ID
        file_id = str(uuid.uuid4())
        file_path = f"uploads/{file_id}_{file.filename}"

        # 创建uploads目录
        os.makedirs("uploads", exist_ok=True)

        # 保存文件
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        # 分析文件结构
        from excel_analysis.header_analyzer import HeaderAnalyzer
        header_analyzer = HeaderAnalyzer()

        xl_file = pd.ExcelFile(file_path)
        analysis_result = {
            "total_sheets": len(xl_file.sheet_names),
            "sheets": []
        }

        for sheet_name in xl_file.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            df.columns = [col.strip(':').strip() for col in df.columns]

            # 使用HeaderAnalyzer进行智能分析
            sheet_info = header_analyzer.analyze_sheet(df, sheet_name)

            sheet_analysis = {
                "name": sheet_name,
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "translatable_rows": sheet_info.translatable_rows,
                "is_terminology": sheet_info.is_terminology,
                "columns": [
                    {
                        "index": col.index,
                        "name": col.name,
                        "type": col.column_type.value,
                        "language": col.language,
                        "sample_data": col.sample_data[:3]
                    }
                    for col in sheet_info.columns
                ],
                "language_columns": [
                    col.name for col in sheet_info.columns
                    if col.language is not None
                ],
                "source_columns": [
                    col.name for col in sheet_info.columns
                    if col.language in ['ch', 'en']
                ],
                "target_columns": [
                    col.name for col in sheet_info.columns
                    if col.language not in ['ch', 'en'] and col.language is not None
                ]
            }
            analysis_result["sheets"].append(sheet_analysis)

        # 创建文件记录到数据库 (使用SQL直接插入)
        from sqlalchemy import text
        insert_query = text("""
            INSERT INTO file_records (
                file_id, original_name, stored_name, file_path, file_size,
                mime_type, storage_type, status, created_at, updated_at
            ) VALUES (
                :file_id, :original_name, :stored_name, :file_path, :file_size,
                :mime_type, :storage_type, :status, NOW(), NOW()
            )
        """)

        await db.execute(insert_query, {
            "file_id": file_id,
            "original_name": file.filename,
            "stored_name": f"{file_id}_{file.filename}",
            "file_path": file_path,
            "file_size": len(content),
            "mime_type": file.content_type or 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            "storage_type": 'local',
            "status": 'completed'
        })
        await db.commit()

        logger.info(f"📁 文件上传并分析完成: {file.filename}, 文件ID: {file_id}")

        return FileUploadResponse(
            file_id=file_id,
            file_name=file.filename,
            file_size=len(content),
            analysis=analysis_result,
            status="uploaded",
            created_at=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/files/{file_id}/start-translation", response_model=TaskResponse)
async def start_translation_from_file(
    file_id: str,
    request: StartTranslationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    translation_engine: TranslationEngine = Depends(get_translation_engine)
):
    """
    基于已上传的文件开始翻译任务
    支持全文翻译或选中范围翻译
    """
    try:
        # 查找文件记录
        from sqlalchemy import text

        result = await db.execute(
            text("SELECT * FROM file_records WHERE file_id = :file_id"),
            {"file_id": file_id}
        )
        file_record = result.fetchone()

        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")

        # 创建翻译任务
        task_id = str(uuid.uuid4())

        config = {
            'target_languages': request.target_languages,
            'sheet_names': request.sheet_names,
            'batch_size': request.batch_size,
            'max_concurrent': request.max_concurrent,
            'region_code': request.region_code,
            'game_background': request.game_background,
            'file_name': file_record.file_name,
            'selected_ranges': request.selected_ranges
        }

        # 估算翻译任务量（简化处理）
        total_tasks = 100  # 临时估算值，实际应该分析文件

        translation_task = TranslationTask(
            id=task_id,
            project_id=request.project_id or 'default',  # 使用请求中的project_id
            version_id='workspace-version',
            task_name=f"Workspace: {file_record.original_name}",
            input_file_id=file_id,
            config=config,
            total_rows=total_tasks,
            status='pending'
        )

        db.add(translation_task)
        await db.commit()

        # 后台启动翻译（使用已保存的文件，传递project_id）
        background_tasks.add_task(
            start_translation_task,
            task_id, file_record.file_path, request.target_languages,
            request.batch_size, request.max_concurrent, request.region_code,
            request.game_background, translation_engine, request.sheet_names, True,
            request.project_id  # 传递project_id
        )

        logger.info(f"🚀 翻译工作台任务启动: {task_id}, 基于文件: {file_id}")

        return TaskResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            message="翻译任务已创建并开始执行",
            created_at=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"启动翻译任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start translation: {str(e)}")


@router.get("/files/{file_id}")
async def get_file_info(
    file_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取文件信息和分析结果"""
    try:
        from sqlalchemy import text

        result = await db.execute(
            text("SELECT * FROM file_records WHERE file_id = :file_id"),
            {"file_id": file_id}
        )
        file_record = result.fetchone()

        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")

        return {
            "file_id": file_record.file_id,
            "file_name": file_record.original_name,
            "file_size": file_record.file_size,
            "analysis": {},  # 分析结果暂时为空，因为表结构不支持
            "status": file_record.status,
            "created_at": file_record.created_at,
            "updated_at": file_record.updated_at
        }

    except Exception as e:
        logger.error(f"获取文件信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get file info: {str(e)}")


@router.get("/files")
async def list_uploaded_files(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """获取数据库中所有上传的Excel文件列表"""
    try:
        from sqlalchemy import select, desc, text

        # 查询所有Excel文件记录
        query = text("""
            SELECT f.file_id, f.original_name, f.file_size, f.storage_type, f.status, f.created_at,
                   COUNT(t.id) as related_tasks
            FROM file_records f
            LEFT JOIN translation_tasks t ON t.input_file_id = f.file_id
            WHERE f.mime_type LIKE '%excel%' OR f.original_name LIKE '%.xlsx' OR f.original_name LIKE '%.xls'
            GROUP BY f.file_id, f.original_name, f.file_size, f.storage_type, f.status, f.created_at
            ORDER BY f.created_at DESC
            LIMIT :limit OFFSET :offset
        """)

        result = await db.execute(query, {"limit": limit, "offset": offset})
        files = result.fetchall()

        # 获取总数
        count_query = text("""
            SELECT COUNT(DISTINCT f.file_id) as total
            FROM file_records f
            WHERE f.mime_type LIKE '%excel%' OR f.original_name LIKE '%.xlsx' OR f.original_name LIKE '%.xls'
        """)
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        return {
            "files": [
                {
                    "file_id": file.file_id,
                    "file_name": file.original_name,
                    "file_size": file.file_size,
                    "storage_type": file.storage_type,
                    "status": file.status,
                    "created_at": file.created_at,
                    "related_tasks": file.related_tasks
                }
                for file in files
            ],
            "total": total,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"获取文件列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")


@router.delete("/files/{file_id}")
async def delete_uploaded_file(
    file_id: str,
    cascade: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """
    删除已上传的文件（统一删除接口）

    Args:
        file_id: 文件ID
        cascade: 是否级联删除相关的翻译任务（默认True）

    Returns:
        删除统计信息
    """
    try:
        from sqlalchemy import select, text
        import os
        import glob

        # 查找文件记录
        result = await db.execute(
            text("SELECT * FROM file_records WHERE file_id = :file_id"),
            {"file_id": file_id}
        )
        file_record = result.fetchone()

        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")

        deleted_files = []
        deleted_tasks = []

        # 1. 删除相关的翻译任务（如果cascade=True）
        if cascade:
            # 查找相关任务
            tasks_query = text("""
                SELECT id, status FROM translation_tasks
                WHERE input_file_id = :file_id
            """)
            tasks_result = await db.execute(tasks_query, {"file_id": file_id})
            related_tasks = tasks_result.fetchall()

            for task in related_tasks:
                task_id = task.id
                try:
                    # 删除任务相关文件
                    task_files = glob.glob(f"temp/{task_id}_*") + glob.glob(f"downloads/{task_id}_*")
                    for file_path in task_files:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            deleted_files.append(file_path)

                    # 删除任务记录
                    await db.execute(
                        text("DELETE FROM translation_tasks WHERE id = :task_id"),
                        {"task_id": task_id}
                    )
                    deleted_tasks.append(task_id)
                    logger.info(f"删除相关翻译任务: {task_id}")

                except Exception as e:
                    logger.warning(f"删除任务失败 {task_id}: {e}")

        # 2. 删除原始文件
        try:
            if os.path.exists(file_record.file_path):
                os.remove(file_record.file_path)
                deleted_files.append(file_record.file_path)
                logger.info(f"删除原始文件: {file_record.file_path}")
        except Exception as e:
            logger.warning(f"删除原始文件失败: {e}")

        # 3. 删除文件记录
        await db.execute(
            text("DELETE FROM file_records WHERE file_id = :file_id"),
            {"file_id": file_id}
        )

        await db.commit()

        logger.info(f"✅ 文件删除完成: {file_id}, 关联任务: {len(deleted_tasks)}, 文件: {len(deleted_files)}")

        return {
            "message": "File and related data deleted successfully",
            "file_id": file_id,
            "deleted_tasks": len(deleted_tasks),
            "deleted_files": len(deleted_files),
            "cascade": cascade
        }

    except Exception as e:
        logger.error(f"删除文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")


async def start_translation_task(
    task_id: str,
    file_path: str,
    target_languages: List[str],
    batch_size: int,
    max_concurrent: int,
    region_code: str,
    game_background: str,
    translation_engine: TranslationEngine,
    sheet_names: List[str] = None,
    auto_detect: bool = True,
    project_id: Optional[str] = None  # 添加project_id参数
):
    """后台翻译任务执行函数"""
    from database.connection import get_async_session

    try:
        logger.info(f"🚀 开始执行翻译工作台任务: {task_id}, 项目: {project_id or 'default'}")

        async with get_async_session() as db:
            await translation_engine.process_translation_task(
                db=db,
                task_id=task_id,
                file_path=file_path,
                target_languages=target_languages,
                batch_size=batch_size,
                max_concurrent=max_concurrent,
                region_code=region_code,
                game_background=game_background,
                sheet_names=sheet_names,
                auto_detect=auto_detect,
                project_id=project_id  # 传递project_id
            )

    except Exception as e:
        logger.error(f"翻译工作台任务执行失败: {task_id}, 错误: {e}")
        async with get_async_session() as db:
            from sqlalchemy import text
            await db.execute(
                text("UPDATE translation_tasks SET status = 'failed', error_message = :error WHERE id = :task_id"),
                {"error": str(e), "task_id": task_id}
            )
            await db.commit()