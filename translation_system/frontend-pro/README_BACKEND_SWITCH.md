# 前端后端切换说明

## 切换后端服务器

只需修改一个文件即可切换后端服务器：

### 修改文件
```
/mnt/d/work/trans_excel/translation_system/frontend-pro/.env.development
```

### 配置内容
```env
# API Backend Configuration (修改此处切换后端)
VITE_API_BASE_URL=http://localhost:8102  # 修改端口号即可切换
VITE_API_TIMEOUT=300000
```

### 可用后端
- 生产环境：`http://localhost:8101` (容器ID: 84731dd28b48)
- 测试环境：`http://localhost:8102` (容器ID: 2710c69695db)

### 切换步骤
1. 修改 `VITE_API_BASE_URL` 的端口号
2. 重启前端开发服务器（如果正在运行）
3. 刷新浏览器页面

### 说明
- vite.config.ts 会自动从环境变量读取 API 地址
- 代理配置会动态使用环境变量中的地址
- 无需修改其他任何配置文件