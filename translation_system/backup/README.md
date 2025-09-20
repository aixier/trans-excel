# Backup目录说明

此目录包含系统开发过程中的测试文件和临时文件，已移出主代码库以避免混淆。

## test_servers/
包含开发过程中创建的测试服务器文件：
- **minimal_server.py** - 最小化API服务器（独立测试用）
- **simple_server.py** - 简化的测试服务器
- **start_minimal.py** - 最小化启动脚本
- **start_without_db.py** - 无数据库启动脚本
- **test_basic.py** - 基础测试脚本
- **test_full_config.py** - 配置测试脚本

这些文件在主系统稳定后不再需要，但保留作为参考。

## docs/
包含重复或过时的文档：
- **README-Docker.md** - 与主目录重复的Docker文档

## 注意事项
- 这些文件不应该被包含在生产部署中
- 如果需要参考测试代码，可以从这里查看
- 主系统使用 `/backend/start.py` 和 `/backend/api_gateway/main.py`