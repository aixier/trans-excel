"""
数据库连接管理
基于SQLAlchemy的异步数据库连接
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

from config.settings import settings


logger = logging.getLogger(__name__)


# 全局引擎实例
async_engine = None
async_session_factory = None


def get_async_engine():
    """获取异步数据库引擎"""
    global async_engine

    if async_engine is None:
        # 构建数据库URL
        database_url = (
            f"mysql+aiomysql://{settings.mysql_user}:{settings.mysql_password}"
            f"@{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_database}"
        )

        # 创建异步引擎，使用连接池优化
        async_engine = create_async_engine(
            database_url,
            # 使用连接池而不是NullPool
            pool_size=5,  # 连接池大小
            max_overflow=10,  # 最大溢出连接数
            pool_timeout=30,  # 连接超时时间
            pool_recycle=3600,  # 连接回收时间（1小时）
            pool_pre_ping=True,  # 检查连接是否有效
            echo=settings.debug_mode,  # 调试模式下打印SQL
            future=True,
            connect_args={
                "charset": "utf8mb4",
                "autocommit": False,
                "connect_timeout": 10  # 连接超时时间
            }
        )

        logger.info("✅ 异步数据库引擎初始化完成")

    return async_engine


def get_async_session_factory():
    """获取异步会话工厂"""
    global async_session_factory

    if async_session_factory is None:
        engine = get_async_engine()
        async_session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=True,
            autocommit=False
        )

        logger.info("✅ 异步会话工厂初始化完成")

    return async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI依赖注入用的数据库会话生成器
    """
    session_factory = get_async_session_factory()

    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    上下文管理器形式的数据库会话
    用于在非FastAPI环境中使用
    """
    session_factory = get_async_session_factory()

    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def test_connection():
    """
    测试数据库连接
    """
    try:
        engine = get_async_engine()

        async with engine.begin() as conn:
            from sqlalchemy import text
            result = await conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()

            if row and row[0] == 1:
                logger.info("✅ 数据库连接测试成功")
                return True
            else:
                logger.error("❌ 数据库连接测试失败：返回值不正确")
                return False

    except Exception as e:
        logger.error(f"❌ 数据库连接测试失败: {str(e)}")
        return False


async def init_database():
    """
    初始化数据库
    创建所有表结构
    """
    try:
        from .models import Base
        engine = get_async_engine()

        async with engine.begin() as conn:
            # 创建所有表
            await conn.run_sync(Base.metadata.create_all)

        logger.info("✅ 数据库表初始化完成")

    except Exception as e:
        logger.error(f"❌ 数据库表初始化失败: {str(e)}")
        raise


async def close_connections():
    """
    关闭所有数据库连接
    """
    global async_engine, async_session_factory

    if async_engine:
        await async_engine.dispose()
        async_engine = None
        async_session_factory = None
        logger.info("✅ 数据库连接已关闭")


# 连接池配置
DATABASE_CONFIG = {
    'pool_size': 10,
    'max_overflow': 20,
    'pool_pre_ping': True,
    'pool_recycle': 300,  # 5分钟回收连接
    'connect_timeout': 60,
    'read_timeout': 60,
    'write_timeout': 60
}