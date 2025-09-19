#!/usr/bin/env python3
"""
完整配置测试脚本
测试数据库连接和API配置
"""
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_config():
    """测试配置加载"""
    print("🔧 测试配置加载...")

    try:
        from config.settings import settings
        print("✅ 配置模块导入成功")

        print(f"   数据库主机: {settings.mysql_host}")
        print(f"   数据库用户: {settings.mysql_user}")
        print(f"   数据库名: {settings.mysql_database}")
        print(f"   LLM Provider: {settings.llm_provider}")
        print(f"   LLM API Key: {settings.llm_api_key[:10]}..." if settings.llm_api_key else "未配置")
        print(f"   OSS Bucket: {settings.oss_bucket_name}")

        return True
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False

async def test_database_connection():
    """测试数据库连接"""
    print("\n🗄️ 测试数据库连接...")

    try:
        from database.connection import test_connection

        connection_ok = await test_connection()
        if connection_ok:
            print("✅ 数据库连接成功")
        else:
            print("❌ 数据库连接失败")
        return connection_ok
    except Exception as e:
        print(f"❌ 数据库连接测试失败: {e}")
        return False

async def test_llm_config():
    """测试LLM配置"""
    print("\n🤖 测试LLM配置...")

    try:
        from config.settings import settings

        if not settings.llm_api_key or settings.llm_api_key == "sk-demo-api-key":
            print("⚠️ LLM API Key 未正确配置")
            return False

        print(f"✅ LLM配置正常")
        print(f"   Provider: {settings.llm_provider}")
        print(f"   Model: {settings.llm_model}")
        print(f"   Base URL: {settings.llm_base_url}")

        return True
    except Exception as e:
        print(f"❌ LLM配置测试失败: {e}")
        return False

async def test_oss_config():
    """测试OSS配置"""
    print("\n☁️ 测试OSS配置...")

    try:
        from config.settings import settings

        if not settings.oss_access_key_id or "XXXX" in settings.oss_access_key_id:
            print("⚠️ OSS配置不完整")
            return False

        print("✅ OSS配置正常")
        print(f"   Bucket: {settings.oss_bucket_name}")
        print(f"   Endpoint: {settings.oss_endpoint}")

        return True
    except Exception as e:
        print(f"❌ OSS配置测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🎮 游戏本地化翻译系统 - 完整配置测试")
    print("=" * 60)

    tests = [
        ("配置加载", test_config),
        ("数据库连接", test_database_connection),
        ("LLM配置", test_llm_config),
        ("OSS配置", test_oss_config)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            if await test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name}测试出错: {e}")

    print(f"\n📊 测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有配置测试通过！系统可以启动完整服务器")
        return True
    else:
        print("⚠️ 部分配置测试失败，建议先修复配置问题")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n👋 测试被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 测试执行出错: {e}")
        sys.exit(1)