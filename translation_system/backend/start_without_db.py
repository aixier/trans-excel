#!/usr/bin/env python3
"""
无数据库启动脚本 - 用于测试完整系统架构
跳过数据库初始化，直接启动API服务器
"""
import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def init_system_without_db():
    """系统初始化（跳过数据库）"""
    logger.info("🚀 翻译系统初始化开始（无数据库模式）")

    try:
        # 验证基础配置
        logger.info("⚙️ 验证系统配置...")
        logger.info(f"   App Name: {settings.app_name}")
        logger.info(f"   Debug Mode: {settings.debug_mode}")
        logger.info(f"   LLM Provider: {settings.llm_provider}")

        if not settings.llm_api_key or settings.llm_api_key == "sk-demo-api-key":
            logger.warning("⚠️ LLM API密钥未配置，翻译功能将不可用")
        else:
            logger.info("✅ LLM API密钥已配置")

        if not settings.oss_access_key_id or "XXXX" in settings.oss_access_key_id:
            logger.warning("⚠️ OSS存储配置未完整，文件上传功能将不可用")
        else:
            logger.info("✅ OSS存储配置已完整")

        logger.info("✅ 系统初始化完成（无数据库模式）")
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
        logger.info(f"📁 确保目录存在: {directory}")


async def main():
    """主函数"""
    try:
        # 创建必要目录
        create_directories()

        # 系统初始化（跳过数据库）
        init_success = await init_system_without_db()
        if not init_success:
            logger.error("❌ 系统初始化失败，退出程序")
            sys.exit(1)

        # 显示系统信息
        logger.info("=" * 60)
        logger.info("🎮 游戏本地化翻译系统 (无数据库测试模式)")
        logger.info(f"📡 服务地址: http://0.0.0.0:{settings.server_port}")
        logger.info(f"📚 API文档: http://0.0.0.0:{settings.server_port}/docs")
        logger.info(f"🔧 调试模式: {settings.debug_mode}")
        logger.info(f"🌍 支持语言: pt, th, ind")
        logger.info(f"🗺️ 支持地区: na, sa, eu, me, as")
        logger.info("⚠️ 注意: 数据库功能已禁用，仅测试API架构")
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