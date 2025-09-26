"""
项目管理器
基于Demo中的进度统计功能扩展
"""
from typing import List, Dict, Optional
import uuid
from datetime import datetime
from database.connection import AsyncSession
from database.models import Project, ProjectVersion, ProjectFile, TranslationTask
from sqlalchemy import select, func
from file_service.storage.oss_storage import OSSStorage
import json
import logging
import asyncio

logger = logging.getLogger(__name__)


class ProjectManager:
    """项目管理器 - 基于Demo中的进度统计功能"""

    def __init__(self, oss_storage: OSSStorage):
        self.storage = oss_storage

    async def create_project(
        self,
        db: AsyncSession,
        name: str,
        description: str,
        target_languages: List[str],
        user_id: str,
        game_background: str = None,
        region_code: str = 'na'
    ) -> str:
        """创建新项目"""
        project_id = str(uuid.uuid4())

        project = Project(
            id=project_id,
            name=name,
            description=description,
            target_languages=target_languages,
            game_background=game_background,
            region_code=region_code,
            user_id=user_id,
            status='active'
        )

        db.add(project)
        await db.commit()

        return project_id

    async def create_version(
        self,
        db: AsyncSession,
        project_id: str,
        version_name: str,
        description: str = None
    ) -> str:
        """创建项目版本"""
        version_id = str(uuid.uuid4())

        version = ProjectVersion(
            id=version_id,
            project_id=project_id,
            version_name=version_name,
            description=description,
            status='active'
        )

        db.add(version)
        await db.commit()

        return version_id

    async def upload_translation_file(
        self,
        db: AsyncSession,
        project_id: str,
        version_id: str,
        file_name: str,
        file_content: bytes,
        file_type: str = 'source'  # source, terminology, completed
    ) -> str:
        """上传翻译文件到项目"""
        # 1. 上传文件到OSS
        file_path = f"projects/{project_id}/versions/{version_id}/{file_type}/{file_name}"
        await self.storage.upload_bytes(file_content, file_path)

        # 2. 记录文件信息
        file_id = str(uuid.uuid4())
        project_file = ProjectFile(
            id=file_id,
            project_id=project_id,
            version_id=version_id,
            file_name=file_name,
            file_path=file_path,
            file_type=file_type,
            file_size=len(file_content)
        )

        db.add(project_file)
        await db.commit()

        return file_id

    async def get_project_summary(self, db: AsyncSession, project_id: str) -> Dict:
        """获取项目概览信息 - 基于Demo中的统计信息"""
        # 项目基本信息
        project_query = select(Project).where(Project.id == project_id)
        result = await db.execute(project_query)
        project = result.scalar_one_or_none()

        if not project:
            raise ValueError("Project not found")

        # 版本信息
        versions_query = select(ProjectVersion).where(
            ProjectVersion.project_id == project_id
        ).order_by(ProjectVersion.created_at.desc())
        versions_result = await db.execute(versions_query)
        versions = versions_result.scalars().all()

        # 翻译任务统计 (与Demo进度统计类似)
        tasks_query = select(
            TranslationTask.status,
            func.count(TranslationTask.id).label('count')
        ).where(
            TranslationTask.project_id == project_id
        ).group_by(TranslationTask.status)

        tasks_result = await db.execute(tasks_query)
        task_stats = {row.status: row.count for row in tasks_result}

        # 翻译进度统计 (类似Demo中的completed_batches/total_batches)
        total_rows_query = select(
            func.sum(TranslationTask.total_rows).label('total_rows'),
            func.sum(TranslationTask.translated_rows).label('translated_rows')
        ).where(TranslationTask.project_id == project_id)

        progress_result = await db.execute(total_rows_query)
        progress_data = progress_result.first()

        total_rows = progress_data.total_rows or 0
        translated_rows = progress_data.translated_rows or 0
        completion_percentage = (translated_rows / total_rows * 100) if total_rows > 0 else 0

        return {
            'project': {
                'id': project.id,
                'name': project.name,
                'description': project.description,
                'target_languages': project.target_languages,
                'game_background': project.game_background,
                'region_code': project.region_code,
                'status': project.status,
                'created_at': project.created_at,
                'updated_at': project.updated_at
            },
            'versions': [
                {
                    'id': v.id,
                    'version_name': v.version_name,
                    'description': v.description,
                    'status': v.status,
                    'created_at': v.created_at
                } for v in versions
            ],
            'task_statistics': task_stats,
            'progress': {
                'total_rows': total_rows,
                'translated_rows': translated_rows,
                'completion_percentage': completion_percentage
            }
        }

    async def get_task_progress(self, db: AsyncSession, task_id: str) -> Dict:
        """获取任务进度详情 - 基于Demo中的进度显示逻辑"""
        # 使用新的数据库会话避免并发问题
        from database.connection import get_async_session

        async with get_async_session() as new_session:
            task_query = select(TranslationTask).where(TranslationTask.id == task_id)
            result = await new_session.execute(task_query)
            task = result.scalar_one_or_none()

        if not task:
            raise ValueError("Task not found")

        # 计算进度百分比 (与Demo逻辑一致)
        completion_percentage = 0
        if task.total_rows > 0:
            completion_percentage = (task.translated_rows / task.total_rows) * 100

        # 估计剩余时间 (基于Demo中的处理速度)
        estimated_time_remaining = None
        if task.status == 'translating' and task.translated_rows > 0:
            elapsed_time = (datetime.utcnow() - task.created_at).total_seconds()
            avg_time_per_row = elapsed_time / task.translated_rows
            remaining_rows = task.total_rows - task.translated_rows
            estimated_time_remaining = int(remaining_rows * avg_time_per_row)

        # 添加Sheet进度信息
        sheet_progress_list = []
        if task.sheet_progress:
            for sheet_name, progress in task.sheet_progress.items():
                sheet_progress_list.append({
                    'name': sheet_name,
                    'total_rows': progress.get('total', 0),
                    'translated_rows': progress.get('translated', 0),
                    'status': progress.get('status', 'pending'),
                    'percentage': (progress.get('translated', 0) / progress.get('total', 1)) * 100
                })

        return {
            'task_id': task.id,
            'status': task.status,
            'progress': {
                'total_rows': task.total_rows,
                'translated_rows': task.translated_rows,
                'current_iteration': task.current_iteration,
                'max_iterations': task.max_iterations,
                'completion_percentage': completion_percentage,
                'estimated_time_remaining': estimated_time_remaining
            },
            'statistics': {
                'total_api_calls': task.total_api_calls,
                'total_tokens_used': task.total_tokens_used,
                'total_cost': task.total_cost
            },
            'sheet_progress': sheet_progress_list,
            'current_sheet': task.current_sheet,
            'total_sheets': task.total_sheets,
            'completed_sheets': task.completed_sheets,
            'error_message': task.error_message,
            'created_at': task.created_at,
            'updated_at': task.updated_at
        }

    async def update_task_progress(
        self,
        db: AsyncSession,  # 这个参数保留以兼容，但不使用
        task_id: str,
        translated_rows: int = None,
        current_iteration: int = None,
        api_calls: int = None,
        tokens_used: int = None,
        cost: float = None,
        status: str = None,
        current_sheet: str = None,
        error_message: str = None,
        sheet_progress: dict = None
    ):
        """更新任务进度 - 直接使用task_repo统一管理缓存"""
        from database.task_repository import get_task_repository
        from datetime import datetime

        task_repo = get_task_repository()

        # 获取任务（从缓存）
        task_data = task_repo._cache.get(task_id)
        if not task_data:
            logger.warning(f"任务 {task_id} 未在缓存中找到")
            return

        # 更新进度数据
        if translated_rows is not None:
            task_data['translated_rows'] = translated_rows
        if current_iteration is not None:
            task_data['current_iteration'] = current_iteration
        if api_calls is not None:
            task_data['total_api_calls'] = task_data.get('total_api_calls', 0) + api_calls
        if tokens_used is not None:
            task_data['total_tokens_used'] = task_data.get('total_tokens_used', 0) + tokens_used
        if cost is not None:
            task_data['total_cost'] = task_data.get('total_cost', 0.0) + cost
        if status is not None:
            task_data['status'] = status
        if current_sheet is not None:
            task_data['current_sheet'] = current_sheet
        if error_message is not None:
            task_data['error_message'] = error_message
        if sheet_progress is not None:
            task_data['sheet_progress'] = sheet_progress

        # 更新时间戳
        task_data['updated_at'] = datetime.utcnow()

        # 计算完成百分比
        total_rows = task_data.get('total_rows', 0)
        if total_rows > 0 and translated_rows is not None:
            task_data['completion_percentage'] = (translated_rows / total_rows) * 100

        # 标记为脏数据（需要持久化）
        task_repo._dirty_tasks.add(task_id)

        logger.debug(f"任务 {task_id} 进度已更新到缓存: {translated_rows}/{total_rows}")

    async def update_task_sheets(
        self,
        db: AsyncSession,
        task_id: str,
        sheet_names: List[str] = None,
        sheet_progress: Dict = None,
        current_sheet: str = None,
        total_sheets: int = None,
        completed_sheets: int = None
    ):
        """更新任务的Sheet信息"""
        task_query = select(TranslationTask).where(TranslationTask.id == task_id)
        result = await db.execute(task_query)
        task = result.scalar_one_or_none()

        if not task:
            raise ValueError("Task not found")

        # 更新Sheet信息
        if sheet_names is not None:
            task.sheet_names = sheet_names
        if sheet_progress is not None:
            task.sheet_progress = sheet_progress
        if current_sheet is not None:
            task.current_sheet = current_sheet
        if total_sheets is not None:
            task.total_sheets = total_sheets
        if completed_sheets is not None:
            task.completed_sheets = completed_sheets

        task.updated_at = datetime.utcnow()
        await db.commit()

    async def list_projects(
        self,
        db: AsyncSession,
        user_id: str,
        status: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict:
        """列出用户项目"""
        offset = (page - 1) * limit

        query = select(Project).where(Project.user_id == user_id)
        if status:
            query = query.where(Project.status == status)

        query = query.order_by(Project.created_at.desc()).offset(offset).limit(limit)

        result = await db.execute(query)
        projects = result.scalars().all()

        # 统计总数
        count_query = select(func.count(Project.id)).where(Project.user_id == user_id)
        if status:
            count_query = count_query.where(Project.status == status)

        count_result = await db.execute(count_query)
        total = count_result.scalar()

        return {
            'projects': [
                {
                    'id': p.id,
                    'name': p.name,
                    'description': p.description,
                    'status': p.status,
                    'created_at': p.created_at,
                    'updated_at': p.updated_at
                } for p in projects
            ],
            'total': total,
            'page': page,
            'limit': limit,
            'pages': (total + limit - 1) // limit
        }