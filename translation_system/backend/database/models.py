"""
数据库模型定义
"""
from sqlalchemy import Column, String, DateTime, Integer, Float, Text, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import uuid

Base = declarative_base()


class Project(Base):
    """项目表"""
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    target_languages = Column(JSON, nullable=False)  # ['pt', 'th', 'ind']
    game_background = Column(Text)
    region_code = Column(String(10), default='na')
    user_id = Column(String(100), nullable=False, index=True)
    status = Column(String(20), default='active', index=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class ProjectVersion(Base):
    """项目版本表"""
    __tablename__ = "project_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), nullable=False, index=True)
    version_name = Column(String(100), nullable=False)
    description = Column(Text)
    status = Column(String(20), default='active')
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class ProjectFile(Base):
    """项目文件表"""
    __tablename__ = "project_files"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), nullable=False, index=True)
    version_id = Column(String(36), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(20), nullable=False, index=True)  # source, terminology, completed, template
    file_size = Column(Integer, default=0)
    upload_time = Column(DateTime, default=func.now())


class TranslationTask(Base):
    """翻译任务表"""
    __tablename__ = "translation_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), nullable=False, index=True)
    version_id = Column(String(36), nullable=False, index=True)
    task_name = Column(String(255), nullable=False)
    input_file_id = Column(String(36), nullable=False)
    output_file_id = Column(String(36), nullable=True)
    config = Column(JSON, nullable=False)  # 翻译配置
    status = Column(String(20), default='pending', index=True)

    # 进度信息
    total_rows = Column(Integer, default=0)
    translated_rows = Column(Integer, default=0)
    current_iteration = Column(Integer, default=0)
    max_iterations = Column(Integer, default=5)

    # Sheet相关信息
    sheet_names = Column(JSON, nullable=True)  # 要处理的Sheet名称列表
    sheet_progress = Column(JSON, nullable=True)  # 每个Sheet的进度
    current_sheet = Column(String(100), nullable=True)  # 当前处理的Sheet
    total_sheets = Column(Integer, default=1)  # 总Sheet数量
    completed_sheets = Column(Integer, default=0)  # 已完成Sheet数量

    # 统计信息
    total_api_calls = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)

    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime, nullable=True)


class Terminology(Base):
    """术语表"""
    __tablename__ = "terminology"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), nullable=False, index=True)
    source = Column(String(500), nullable=False)
    target_translations = Column(JSON, nullable=False)  # {'en': 'Health', 'pt': 'Saúde'}
    category = Column(String(100), index=True)
    priority = Column(Integer, default=1, index=True)
    context = Column(Text)
    case_sensitive = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class TranslationLog(Base):
    """翻译日志表"""
    __tablename__ = "translation_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), nullable=False, index=True)
    iteration = Column(Integer, nullable=False)
    batch_id = Column(Integer, nullable=False)
    request_data = Column(JSON)
    response_data = Column(JSON)
    tokens_used = Column(Integer, default=0)
    duration_ms = Column(Float, default=0.0)
    success = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now(), index=True)