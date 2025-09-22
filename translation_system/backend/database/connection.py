"""
改进的数据库连接管理
解决 Command Out of Sync 错误和其他连接问题
基于 MySQL/aiomysql 最佳实践
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool, QueuePool
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
import logging
import asyncio
from functools import wraps
import pymysql

from config.settings import settings

logger = logging.getLogger(__name__)

# 全局引擎实例
_async_engine: Optional[any] = None
_async_session_factory: Optional[async_sessionmaker] = None


class DatabaseConnectionManager:
    """数据库连接管理器 - 单例模式"""
    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.engine = None
        self.session_factory = None
        self._initialized = False

    async def initialize(self):
        """初始化数据库连接"""
        async with self._lock:
            if self._initialized:
                return

            database_url = (
                f"mysql+aiomysql://{settings.mysql_user}:{settings.mysql_password}"
                f"@{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_database}"
            )

            # 使用更保守的连接池配置来避免 Command Out of Sync
            self.engine = create_async_engine(
                database_url,
                echo=settings.debug_mode,
                future=True,
                # 使用NullPool避免连接复用问题（生产环境可以切换到QueuePool）
                poolclass=NullPool if settings.debug_mode else QueuePool,
                # 连接池配置
                pool_size=20,  # 增加连接池大小支持高并发
                max_overflow=30,  # 增加溢出连接数
                pool_pre_ping=True,  # 每次使用前测试连接
                pool_recycle=300,  # 5分钟回收连接
                pool_timeout=60,  # 增加连接池超时
                # aiomysql 特定配置
                connect_args={
                    "charset": "utf8mb4",
                    "connect_timeout": 60,  # 增加连接超时
                    "autocommit": False,  # 明确关闭自动提交
                    "echo": False,
                    # 重要：确保正确处理结果集
                    "client_flag": pymysql.constants.CLIENT.MULTI_RESULTS,
                }
            )

            # 创建会话工厂
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,  # 避免自动刷新导致的问题
                autocommit=False  # 使用手动提交
            )

            self._initialized = True
            logger.info("✅ 数据库连接管理器初始化成功")

    async def get_session(self) -> AsyncSession:
        """获取数据库会话"""
        if not self._initialized:
            await self.initialize()
        return self.session_factory()

    async def dispose(self):
        """关闭所有连接"""
        if self.engine:
            await self.engine.dispose()
            self.engine = None
            self.session_factory = None
            self._initialized = False
            logger.info("✅ 数据库连接已关闭")


# 全局连接管理器实例
db_manager = DatabaseConnectionManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI依赖注入用的数据库会话生成器
    改进版：完全避免 Command Out of Sync 错误
    """
    session = None
    try:
        session = await db_manager.get_session()

        # 确保会话处于干净状态
        try:
            from sqlalchemy import text
            await session.execute(text("SELECT 1"))
            await session.commit()  # 清理任何挂起的事务
        except Exception:
            await session.rollback()

        yield session

    except Exception as e:
        # 只在真正的异常时记录错误，不记录空异常
        if str(e).strip():
            logger.error(f"数据库会话错误: {e}")
        if session:
            try:
                await session.rollback()
            except Exception as rollback_error:
                logger.debug(f"回滚失败（忽略）: {rollback_error}")
        raise
    finally:
        if session:
            try:
                # 重要：确保所有结果集都被读取
                await session.commit()  # 提交或清理任何未完成的事务
            except Exception:
                pass

            try:
                await session.close()
            except Exception as close_error:
                logger.debug(f"关闭会话失败（忽略）: {close_error}")


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    上下文管理器形式的数据库会话
    用于后台任务和非FastAPI环境
    """
    session = None
    max_retries = 3
    retry_delay = 1

    for attempt in range(max_retries):
        try:
            session = await db_manager.get_session()

            # 测试连接
            from sqlalchemy import text
            await session.execute(text("SELECT 1"))
            await session.commit()

            # 开始新事务
            await session.begin()

            yield session

            # 提交事务
            await session.commit()
            return

        except Exception as e:
            error_msg = str(e).lower()

            # 处理连接错误
            if any(err in error_msg for err in ['lost connection', 'gone away', '2013', '2006', 'command out of sync', '2014']):
                logger.warning(f"数据库连接问题 (尝试 {attempt + 1}/{max_retries}): {e}")

                if session:
                    try:
                        await session.rollback()
                    except Exception:
                        pass
                    try:
                        await session.close()
                    except Exception:
                        pass
                    session = None

                # 如果是最后一次尝试，抛出错误
                if attempt == max_retries - 1:
                    raise

                # 等待后重试
                await asyncio.sleep(retry_delay * (attempt + 1))

                # 重新初始化连接池
                await db_manager.dispose()
                await db_manager.initialize()
            else:
                # 非连接错误，直接抛出
                if session:
                    try:
                        await session.rollback()
                    except Exception:
                        pass
                raise
        finally:
            if session and attempt == max_retries - 1:
                try:
                    await session.close()
                except Exception:
                    pass


def retry_on_db_error(max_retries=3, delay=1.0):
    """
    数据库操作重试装饰器
    专门处理 Command Out of Sync 和连接错误
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None

            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    error_msg = str(e).lower()

                    # 检查是否是可重试的错误
                    if any(err in error_msg for err in [
                        'lost connection',
                        'gone away',
                        '2013',
                        '2006',
                        'command out of sync',
                        '2014',
                        'lock wait timeout'
                    ]):
                        logger.warning(f"数据库操作失败，尝试重试 ({attempt + 1}/{max_retries}): {e}")
                        await asyncio.sleep(delay * (attempt + 1))

                        # 如果有session参数，尝试刷新它
                        if 'session' in kwargs:
                            session = kwargs['session']
                            if session:
                                try:
                                    await session.rollback()
                                    await session.close()
                                except Exception:
                                    pass
                                # 获取新会话
                                kwargs['session'] = await db_manager.get_session()
                    else:
                        # 非可重试错误，直接抛出
                        raise

            raise last_error
        return wrapper
    return decorator


async def execute_with_retry(session: AsyncSession, query, params=None, max_retries=3):
    """
    执行数据库查询with重试机制
    确保完整读取结果集，避免 Command Out of Sync
    """
    for attempt in range(max_retries):
        try:
            result = await session.execute(query, params)

            # 重要：确保完整读取结果集
            if result.returns_rows:
                # 对于SELECT查询，获取所有结果
                rows = result.fetchall()
                return rows
            else:
                # 对于非SELECT查询，返回结果对象
                return result

        except Exception as e:
            error_msg = str(e).lower()

            if 'command out of sync' in error_msg or '2014' in error_msg:
                logger.warning(f"Command Out of Sync 错误，尝试清理会话 ({attempt + 1}/{max_retries})")

                # 尝试清理会话
                try:
                    await session.rollback()
                    # 执行一个简单查询来重置连接状态
                    from sqlalchemy import text
                    await session.execute(text("SELECT 1"))
                    await session.commit()
                except Exception:
                    pass

                if attempt == max_retries - 1:
                    raise
            else:
                raise


async def test_connection():
    """测试数据库连接"""
    try:
        async with get_async_session() as session:
            from sqlalchemy import text
            result = await execute_with_retry(session, text("SELECT 1 as test"))

            if result and result[0][0] == 1:
                logger.info("✅ 数据库连接测试成功")
                return True
            else:
                logger.error("❌ 数据库连接测试失败：返回值不正确")
                return False

    except Exception as e:
        logger.error(f"❌ 数据库连接测试失败: {str(e)}")
        return False


async def init_database():
    """初始化数据库表结构"""
    try:
        from .models import Base

        # 确保连接管理器已初始化
        await db_manager.initialize()

        async with get_async_session() as session:
            from sqlalchemy import text

            # 检查表是否存在
            result = await execute_with_retry(
                session,
                text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = :db"),
                {"db": settings.mysql_database}
            )
            table_count = result[0][0] if result else 0

            if table_count > 0:
                logger.info(f"✅ 数据库已有 {table_count} 个表")
            else:
                # 创建所有表
                async with db_manager.engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                logger.info("✅ 数据库表初始化完成")

    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {str(e)}")
        logger.warning("⚠️ 系统将尝试继续启动")


async def close_connections():
    """关闭所有数据库连接"""
    await db_manager.dispose()


# 导出旧接口以保持兼容性
def get_async_engine():
    """获取异步数据库引擎（兼容旧代码）"""
    if not db_manager._initialized:
        asyncio.create_task(db_manager.initialize())
    return db_manager.engine


def get_async_session_factory():
    """获取异步会话工厂（兼容旧代码）"""
    if not db_manager._initialized:
        asyncio.create_task(db_manager.initialize())
    return db_manager.session_factory