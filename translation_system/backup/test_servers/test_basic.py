#!/usr/bin/env python3
"""
基础功能测试脚本
在完整依赖安装之前测试核心功能
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试核心模块导入"""
    print("🔍 测试模块导入...")

    try:
        # 测试FastAPI
        import fastapi
        print(f"✅ FastAPI {fastapi.__version__} - 导入成功")

        # 测试Uvicorn
        import uvicorn
        print(f"✅ Uvicorn - 导入成功")

        # 测试环境变量加载
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ python-dotenv - 导入成功")

        return True

    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_config():
    """测试配置加载"""
    print("\n⚙️ 测试配置加载...")

    try:
        from config.settings import settings
        print(f"✅ 配置类导入成功")
        print(f"   - App Name: {settings.app_name}")
        print(f"   - Debug Mode: {settings.debug_mode}")
        print(f"   - Server Port: {settings.server_port}")
        return True

    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False

def test_basic_api():
    """测试基础API创建"""
    print("\n🌐 测试基础API创建...")

    try:
        from fastapi import FastAPI

        # 创建简单的FastAPI应用
        app = FastAPI(title="Translation System Test")

        @app.get("/")
        async def root():
            return {"message": "Translation System is running!"}

        @app.get("/health")
        async def health():
            return {"status": "healthy", "service": "translation-system"}

        print("✅ FastAPI应用创建成功")
        print("   - 根路径: /")
        print("   - 健康检查: /health")

        return app

    except Exception as e:
        print(f"❌ API创建失败: {e}")
        return None

def test_directory_structure():
    """测试目录结构"""
    print("\n📁 测试目录结构...")

    required_dirs = [
        "api_gateway",
        "config",
        "translation_core",
        "excel_analysis",
        "database",
        "file_service",
        "project_manager"
    ]

    all_exist = True
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists():
            print(f"✅ {dir_name}/ - 存在")
        else:
            print(f"❌ {dir_name}/ - 不存在")
            all_exist = False

    return all_exist

def run_basic_server():
    """运行基础测试服务器"""
    print("\n🚀 启动基础测试服务器...")

    app = test_basic_api()
    if app is None:
        return False

    try:
        import uvicorn

        print("启动服务器在 http://localhost:8000")
        print("按 Ctrl+C 停止服务器")
        print("-" * 50)

        # 启动服务器
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )

        return True

    except KeyboardInterrupt:
        print("\n⏹️ 服务器已停止")
        return True
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🎮 游戏本地化翻译系统 - 基础功能测试")
    print("=" * 60)

    # 运行所有测试
    tests = [
        ("模块导入", test_imports),
        ("目录结构", test_directory_structure),
        ("配置加载", test_config),
        ("API创建", lambda: test_basic_api() is not None)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        if test_func():
            passed += 1

    print(f"\n📊 测试结果: {passed}/{total} 通过")

    if passed == total:
        print("✅ 所有基础测试通过！")

        # 询问是否启动测试服务器
        try:
            choice = input("\n是否启动测试服务器? (y/N): ").lower().strip()
            if choice in ['y', 'yes']:
                run_basic_server()
        except KeyboardInterrupt:
            print("\n👋 测试结束")
    else:
        print("❌ 部分测试失败，请检查系统配置")
        return False

    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 测试被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 测试执行出错: {e}")
        sys.exit(1)