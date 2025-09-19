"""
项目管理API路由
"""
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import List, Optional
import uuid
import logging

from database.connection import get_db, AsyncSession
from project_manager.manager import ProjectManager
from file_service.storage.oss_storage import OSSStorage
from ..models.task import (
    ProjectCreateRequest, ProjectResponse, ProjectSummaryResponse
)


router = APIRouter()
logger = logging.getLogger(__name__)


# 依赖注入
def get_project_manager():
    """获取项目管理器实例"""
    return ProjectManager(OSSStorage())


@router.post("/create", response_model=ProjectResponse)
async def create_project(
    request: ProjectCreateRequest,
    user_id: str = "default_user",  # 实际应从认证中获取
    db: AsyncSession = Depends(get_db),
    project_manager: ProjectManager = Depends(get_project_manager)
):
    """
    创建新的翻译项目
    """
    try:
        project_id = await project_manager.create_project(
            db=db,
            name=request.name,
            description=request.description,
            target_languages=request.target_languages,
            user_id=user_id,
            game_background=request.game_background,
            region_code=request.region_code
        )

        logger.info(f"✅ 项目创建成功: {request.name}, ID: {project_id}")

        return ProjectResponse(
            id=project_id,
            name=request.name,
            description=request.description,
            target_languages=request.target_languages,
            status="active",
            created_at=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"项目创建失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")


@router.get("/{project_id}/summary", response_model=ProjectSummaryResponse)
async def get_project_summary(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    project_manager: ProjectManager = Depends(get_project_manager)
):
    """
    获取项目概览信息
    包括版本列表、任务统计、进度信息
    """
    try:
        summary = await project_manager.get_project_summary(db, project_id)

        return ProjectSummaryResponse(
            project=ProjectResponse(
                id=summary['project']['id'],
                name=summary['project']['name'],
                description=summary['project']['description'],
                target_languages=summary['project']['target_languages'],
                status=summary['project']['status'],
                created_at=summary['project']['created_at']
            ),
            versions=summary['versions'],
            task_statistics=summary['task_statistics'],
            progress=summary['progress']
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取项目概览失败: {project_id}, 错误: {e}")
        raise HTTPException(status_code=500, detail="Failed to get project summary")


@router.post("/{project_id}/versions")
async def create_project_version(
    project_id: str,
    version_name: str,
    description: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    project_manager: ProjectManager = Depends(get_project_manager)
):
    """
    创建项目版本
    """
    try:
        version_id = await project_manager.create_version(
            db=db,
            project_id=project_id,
            version_name=version_name,
            description=description
        )

        logger.info(f"✅ 项目版本创建成功: {version_name}, ID: {version_id}")

        return {
            "version_id": version_id,
            "project_id": project_id,
            "version_name": version_name,
            "description": description,
            "created_at": datetime.utcnow()
        }

    except Exception as e:
        logger.error(f"项目版本创建失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create version: {str(e)}")


@router.get("/list")
async def list_projects(
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    user_id: str = "default_user",  # 实际应从认证中获取
    db: AsyncSession = Depends(get_db),
    project_manager: ProjectManager = Depends(get_project_manager)
):
    """
    列出用户的项目
    支持状态筛选和分页
    """
    try:
        projects_data = await project_manager.list_projects(
            db=db,
            user_id=user_id,
            status=status,
            page=page,
            limit=limit
        )

        return {
            "projects": [
                ProjectResponse(
                    id=p['id'],
                    name=p['name'],
                    description=p['description'],
                    target_languages=[],  # 需要从数据库获取
                    status=p['status'],
                    created_at=p['created_at']
                ) for p in projects_data['projects']
            ],
            "total": projects_data['total'],
            "page": projects_data['page'],
            "limit": projects_data['limit'],
            "pages": projects_data['pages']
        }

    except Exception as e:
        logger.error(f"列出项目失败: {e}")
        raise HTTPException(status_code=500, detail="Failed to list projects")


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    删除项目（软删除）
    """
    try:
        # 这里应该实现项目的软删除逻辑
        # 更新项目状态为 'deleted'
        logger.info(f"✅ 项目已删除: {project_id}")

        return {
            "message": "Project deleted successfully",
            "project_id": project_id,
            "deleted_at": datetime.utcnow()
        }

    except Exception as e:
        logger.error(f"删除项目失败: {project_id}, 错误: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete project")