"""
数据库初始化脚本
"""
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import db_manager
from config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_database():
    """初始化数据库"""
    try:
        logger.info("开始初始化数据库...")

        # 初始化数据库连接
        await db_manager.initialize()

        # 创建所有表
        await db_manager.create_tables()

        logger.info("数据库初始化完成!")

    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise
    finally:
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(init_database())