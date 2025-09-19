# 后端服务选项说明

## 当前可用的后端服务

### 1. 测试服务器 (推荐用于测试)
- **地址**: `http://localhost:8001`
- **状态**: ✅ 运行中
- **特点**:
  - 简单的模拟服务器
  - 无需数据库
  - 专门为前端测试设计
  - 支持文件上传模拟

### 2. Docker容器服务
- **地址**: `http://localhost:8101`
- **容器ID**: 9e6bd363f5e9
- **状态**: ✅ 运行中 (有健康检查)
- **问题**:
  - 上传接口参数不匹配
  - 需要真实的数据库连接
  - API参数要求不同

## 使用说明

### 方式一：使用测试服务器（推荐）
1. 确保测试服务器运行中:
   ```bash
   cd /mnt/d/work/trans_excel/translation_system/backend
   SERVER_PORT=8001 python3 minimal_server.py
   ```

2. 打开前端页面 `index.html`

3. 在"后端地址"输入框填写: `http://localhost:8001`

4. 点击"连接"按钮

5. 上传Excel文件测试

### 方式二：停止Docker容器，只使用测试服务器
```bash
# 停止Docker容器
docker stop 9e6bd363f5e9

# 启动测试服务器
SERVER_PORT=8001 python3 minimal_server.py
```

### 方式三：修改Docker容器映射端口
```bash
# 停止并删除当前容器
docker stop 9e6bd363f5e9
docker rm 9e6bd363f5e9

# 重新运行，映射到不同端口
docker run -d -p 8102:8000 translation-system:0.1
```

## 测试文件
- `test_data.xlsx` - 包含测试数据的真实Excel文件
- 大小: 5.6KB
- 包含中英文文本用于翻译测试

## 故障排除

### 问题：500错误 - file_name参数错误
- **原因**: Docker容器的API接口参数与前端不匹配
- **解决**: 使用端口8001的测试服务器

### 问题：连接失败
- **检查**:
  1. 确认后端服务运行中
  2. 检查端口是否正确
  3. 查看浏览器控制台日志