#!/usr/bin/env python3
"""Verify excel_mcp installation and dependencies."""

import sys
import os
from pathlib import Path

def check_file(filepath, description):
    """Check if a file exists."""
    if os.path.isfile(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} (MISSING)")
        return False

def check_directory(dirpath, description):
    """Check if a directory exists."""
    if os.path.isdir(dirpath):
        print(f"✅ {description}: {dirpath}")
        return True
    else:
        print(f"❌ {description}: {dirpath} (MISSING)")
        return False

def check_import(module_name):
    """Check if a Python module can be imported."""
    try:
        __import__(module_name)
        print(f"✅ Dependency: {module_name}")
        return True
    except ImportError as e:
        print(f"❌ Dependency: {module_name} (NOT INSTALLED - {e})")
        return False

def main():
    """Main verification function."""
    print("\n" + "=" * 80)
    print("Excel MCP Server - Installation Verification")
    print("=" * 80 + "\n")

    base_dir = Path(__file__).parent
    all_good = True

    # Check directories
    print("Checking directories...")
    all_good &= check_directory(base_dir / "utils", "Utils directory")
    all_good &= check_directory(base_dir / "services", "Services directory")
    all_good &= check_directory(base_dir / "models", "Models directory")
    all_good &= check_directory(base_dir / "examples", "Examples directory")
    all_good &= check_directory(base_dir / "static", "Static directory")
    print()

    # Check core files
    print("Checking core files...")
    all_good &= check_file(base_dir / "server.py", "MCP Server entry point")
    all_good &= check_file(base_dir / "mcp_tools.py", "MCP tool definitions")
    all_good &= check_file(base_dir / "mcp_handler.py", "MCP handler")
    all_good &= check_file(base_dir / "requirements.txt", "Requirements file")
    print()

    # Check utils
    print("Checking utils files...")
    all_good &= check_file(base_dir / "utils/__init__.py", "Utils package init")
    all_good &= check_file(base_dir / "utils/http_client.py", "HTTP client")
    all_good &= check_file(base_dir / "utils/token_validator.py", "Token validator")
    all_good &= check_file(base_dir / "utils/color_detector.py", "Color detector")
    all_good &= check_file(base_dir / "utils/session_manager.py", "Session manager")
    print()

    # Check services
    print("Checking services files...")
    all_good &= check_file(base_dir / "services/__init__.py", "Services package init")
    all_good &= check_file(base_dir / "services/excel_loader.py", "Excel loader")
    all_good &= check_file(base_dir / "services/excel_analyzer.py", "Excel analyzer")
    all_good &= check_file(base_dir / "services/task_queue.py", "Task queue")
    print()

    # Check models
    print("Checking models files...")
    all_good &= check_file(base_dir / "models/__init__.py", "Models package init")
    all_good &= check_file(base_dir / "models/excel_dataframe.py", "Excel DataFrame model")
    all_good &= check_file(base_dir / "models/session_data.py", "Session data model")
    all_good &= check_file(base_dir / "models/analysis_result.py", "Analysis result model")
    print()

    # Check documentation
    print("Checking documentation...")
    all_good &= check_file(base_dir / "README.md", "README documentation")
    all_good &= check_file(base_dir / "QUICKSTART.md", "Quick start guide")
    all_good &= check_file(base_dir / "IMPLEMENTATION_SUMMARY.md", "Implementation summary")
    print()

    # Check dependencies
    print("Checking Python dependencies...")
    dependencies = [
        'mcp',
        'openpyxl',
        'pandas',
        'requests',
        'aiohttp',
        'jwt',
        'langdetect'
    ]

    for dep in dependencies:
        all_good &= check_import(dep)
    print()

    # Summary
    print("=" * 80)
    if all_good:
        print("✅ All checks passed! Excel MCP Server is ready to run.")
        print("\nTo start the server, run:")
        print(f"  python3 {base_dir / 'server.py'}")
        print("\nTo generate a test token, run:")
        print(f"  python3 {base_dir / 'test_token.py'}")
    else:
        print("❌ Some checks failed. Please review the errors above.")
        print("\nTo install dependencies, run:")
        print(f"  pip install -r {base_dir / 'requirements.txt'}")
    print("=" * 80 + "\n")

    return 0 if all_good else 1


if __name__ == "__main__":
    sys.exit(main())
