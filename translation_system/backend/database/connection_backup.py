"""
数据库连接管理
基于SQLAlchemy的异步数据库连接
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import QueuePool
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging
import asyncio
from functools import wraps

from config.settings import settings


logger = logging.getLogger(__name__)


# 全局引擎实例
async_engine = None
async_session_factory = None


def retry_on_disconnect(max_retries=3, delay=1.0):
    """数据库操作重试装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    error_msg = str(e)
                    if any(err in error_msg.lower() for err in ['lost connection', '2013', '2006', 'gone away']):
                        last_error = e
                        logger.warning(f"数据库连接丢失，尝试重连 ({attempt + 1}/{max_retries}): {error_msg}")
                        await asyncio.sleep(delay * (attempt + 1))
                        # 清理旧连接
                        global async_engine, async_session_factory
                        if async_engine:
                            await async_engine.dispose()
                            async_engine = None
                            async_session_factory = None
                    else:
                        raise
            raise last_error
        return wrapper
    return decorator


def get_async_engine():
    """获取异步数据库引擎"""
    global async_engine

    if async_engine is None:
        # 构建数据库URL
        database_url = (
            f"mysql+aiomysql://{settings.mysql_user}:{settings.mysql_password}"
            f"@{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_database}"
        )

        # 创建异步引擎，使用优化的连接池配置
        from sqlalchemy.pool import QueuePool
        async_engine = create_async_engine(
            database_url,
            echo=settings.debug_mode,  # 调试模式下打印SQL
            future=True,
            # 使用QueuePool with 优化配置
            poolclass=QueuePool,
            pool_size=2,  # 进一步减小连接池大小
            max_overflow=3,  # 进一步减小溢出连接数
            pool_pre_ping=True,  # 每次使用前测试连接
            pool_recycle=180,  # 3分钟回收连接
            pool_timeout=20,  # 连接池超时
            connect_args={
                "charset": "utf8mb4",
                "connect_timeout": 10,  # 连接超时
                "server_public_key": None,  # 避免认证问题
                "echo": False,  # 关闭aiomysql的echo
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
            autoflush=False,  # 关闭自动刷新避免并发问题
            autocommit=False  # 使用手动提交模式
        )

        logger.info("✅ 异步会话工厂初始化完成")

    return async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI依赖注入用的数据库会话生成器 - 改进版本
    """
    session_factory = get_async_session_factory()
    session = None

    try:
        session = session_factory()
        yield session
        # 不自动提交，让调用方决定是否提交
    except Exception as e:
        if session:
            try:
                # 简单尝试回滚，捕获所有错误
                await session.rollback()
            except Exception as rollback_error:
                # 忽略回滚错误，避免掩盖原始错误
                logger.debug(f"数据库回滚失败（忽略）: {rollback_error}")
        raise
    finally:
        if session:
            try:
                await session.close()
            except Exception as close_error:
                logger.debug(f"关闭数据库会话失败（忽略）: {close_error}")


async def get_robust_db_session() -> AsyncSession:
    """
    获取健壮的数据库会话 - 用于长时间运行的任务
    """
    session_factory = get_async_session_factory()
    max_retries = 3

    for attempt in range(max_retries):
        try:
            session = session_factory()
            # 测试连接
            from sqlalchemy import text
            await session.execute(text("SELECT 1"))
            return session
        except Exception as e:
            logger.warning(f"创建数据库会话失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(1 * (attempt + 1))


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

        # 使用独立连接避免超时
        async with engine.connect() as conn:
            # 检查表是否已存在
            from sqlalchemy import text
            result = await conn.execute(
                text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = :db"),
                {"db": settings.mysql_database}
            )
            table_count = result.scalar()

            if table_count > 0:
                logger.info(f"✅ 数据库已有 {table_count} 个表，检查并更新表结构")

                # 检查translation_tasks表是否需要添加新列
                try:
                    result = await conn.execute(text("DESCRIBE translation_tasks"))
                    existing_columns = {row[0] for row in result.fetchall()}

                    columns_to_add = []
                    if 'sheet_names' not in existing_columns:
                        columns_to_add.append("ADD COLUMN sheet_names JSON")
                    if 'sheet_progress' not in existing_columns:
                        columns_to_add.append("ADD COLUMN sheet_progress JSON")
                    if 'current_sheet' not in existing_columns:
                        columns_to_add.append("ADD COLUMN current_sheet VARCHAR(100)")
                    if 'total_sheets' not in existing_columns:
                        columns_to_add.append("ADD COLUMN total_sheets INT DEFAULT 1")
                    if 'completed_sheets' not in existing_columns:
                        columns_to_add.append("ADD COLUMN completed_sheets INT DEFAULT 0")

                    if columns_to_add:
                        alter_sql = f"ALTER TABLE translation_tasks {', '.join(columns_to_add)}"
                        logger.info(f"更新表结构: {alter_sql}")
                        await conn.execute(text(alter_sql))
                        await conn.commit()
                        logger.info("✅ 表结构更新成功")
                except Exception as e:
                    logger.warning(f"检查表结构时出现问题: {e}")

                return

            # 创建所有表
            await conn.run_sync(Base.metadata.create_all)
            await conn.commit()

        logger.info("✅ 数据库表初始化完成")

    except Exception as e:
        logger.error(f"❌ 数据库表初始化失败: {str(e)}")
        # 不要抛出异常，允许系统继续启动
        logger.warning("⚠️ 系统将尝试继续启动，表可能已存在")


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