#!/usr/bin/env python3
"""
翻译系统启动脚本
基于架构文档的完整系统启动器
"""
import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from database.connection import init_database, test_connection
from database.models import Base


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/translation_system.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


async def init_system():
    """系统初始化"""
    logger.info("🚀 翻译系统初始化开始")

    try:
        # 1. 测试数据库连接
        logger.info("📊 测试数据库连接...")
        connection_ok = await test_connection()
        if not connection_ok:
            logger.error("❌ 数据库连接失败，请检查配置")
            return False

        # 2. 初始化数据库表
        logger.info("🗄️ 初始化数据库表...")
        await init_database()

        # 3. 验证必要配置
        logger.info("⚙️ 验证系统配置...")

        # 验证LLM配置
        from pathlib import Path
        import json
        llm_config_path = Path(__file__).parent / "config" / "llm_configs.json"
        if llm_config_path.exists():
            with open(llm_config_path, 'r', encoding='utf-8') as f:
                llm_config = json.load(f)
                active_profile = llm_config.get('active_profile')
                if active_profile and active_profile in llm_config.get('profiles', {}):
                    profile = llm_config['profiles'][active_profile]
                    logger.info(f"✅ LLM配置已加载: {active_profile} ({profile.get('provider')}/{profile.get('model')})")
                else:
                    logger.warning("⚠️ LLM配置文件中没有有效的active_profile")
        else:
            logger.warning("⚠️ LLM配置文件不存在: config/llm_configs.json")

        if not all([settings.oss_access_key_id, settings.oss_access_key_secret]):
            logger.warning("⚠️ OSS存储配置未完整")

        logger.info("✅ 系统初始化完成")
        return True

    except Exception as e:
        logger.error(f"❌ 系统初始化失败: {e}")
        return False


async def start_api_server():
    """启动API服务器"""
    try:
        import uvicorn
        from api_gateway.main import app

        logger.info("🌐 启动API服务器...")

        config = uvicorn.Config(
            app,
            host="0.0.0.0",
            port=settings.server_port,
            reload=settings.debug_mode,
            log_level="info",
            access_log=True
        )

        server = uvicorn.Server(config)
        await server.serve()

    except Exception as e:
        logger.error(f"❌ API服务器启动失败: {e}")
        raise


def create_directories():
    """创建必要的目录"""
    directories = [
        "logs",
        "temp",
        "uploads",
        "downloads"
    ]

    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        logger.info(f"📁 创建目录: {directory}")


async def main():
    """主函数"""
    try:
        # 创建必要目录
        create_directories()

        # 系统初始化
        init_success = await init_system()
        if not init_success:
            logger.error("❌ 系统初始化失败，退出程序")
            sys.exit(1)

        # 显示系统信息
        logger.info("=" * 60)
        logger.info("🎮 游戏本地化翻译系统")
        logger.info(f"📡 服务地址: http://0.0.0.0:{settings.server_port}")
        logger.info(f"📚 API文档: http://0.0.0.0:{settings.server_port}/docs")
        logger.info(f"🔧 调试模式: {settings.debug_mode}")
        logger.info(f"🌍 支持语言: pt, th, ind")
        logger.info(f"🗺️ 支持地区: na, sa, eu, me, as")
        logger.info("=" * 60)

        # 启动API服务器
        await start_api_server()

    except KeyboardInterrupt:
        logger.info("⏹️ 接收到停止信号，正在关闭系统...")
    except Exception as e:
        logger.error(f"❌ 系统运行错误: {e}")
        sys.exit(1)
    finally:
        logger.info("👋 系统已关闭")


if __name__ == "__main__":
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        sys.exit(1)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ 程序被用户终止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)