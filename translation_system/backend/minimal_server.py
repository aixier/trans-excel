#!/usr/bin/env python3
"""
最小化API服务器 - 完全独立运行
不依赖任何项目配置和数据库
"""
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn
from datetime import datetime
import os
import json
import uuid
import asyncio
from typing import Optional
import io

# 创建FastAPI应用
app = FastAPI(
    title="Translation System Minimal Server",
    description="游戏本地化翻译系统最小服务器",
    version="1.0.0-minimal",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件 - 支持所有来源包括file://
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，包括file://
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],  # 暴露所有响应头
)

# 根路径
@app.get("/")
async def root():
    """根路径信息"""
    return {
        "service": "Translation System Minimal Server",
        "version": "1.0.0-minimal",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "🎮 游戏本地化翻译系统最小服务器",
        "docs": "/docs"
    }

# 健康检查
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "translation-system-minimal",
        "version": "1.0.0-minimal"
    }

# API健康检查 (匹配前端调用)
@app.get("/api/health/status")
async def api_health_status():
    """API健康检查状态"""
    return {
        "status": "online",
        "service": "translation-system-api",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0-minimal",
        "message": "API服务正常运行"
    }

# 系统信息
@app.get("/api/info")
async def system_info():
    """系统信息"""
    return {
        "service": "Translation System Minimal",
        "version": "1.0.0-minimal",
        "config": {
            "app_name": "游戏本地化翻译系统",
            "debug_mode": True,
            "server_port": 8000,
            "environment": "minimal"
        },
        "supported_languages": ["pt", "th", "ind"],
        "supported_regions": ["na", "sa", "eu", "me", "as"],
        "features": [
            "基础API服务",
            "健康检查",
            "系统信息查询",
            "API文档"
        ]
    }

# 测试接口
@app.get("/api/test/ping")
async def test_ping():
    """测试连接"""
    return {
        "status": "success",
        "message": "pong",
        "timestamp": datetime.utcnow().isoformat()
    }

# 全局存储任务状态 (内存中)
tasks = {}

# 文件上传和翻译启动
@app.post("/api/translation/upload")
async def upload_and_translate(
    file: UploadFile = File(...),
    target_languages: str = Form("pt,th,ind"),
    region_code: str = Form("na"),
    batch_size: int = Form(3),
    max_concurrent: int = Form(10)
):
    """上传Excel文件并启动翻译"""

    # 检查文件类型
    if not file.filename.endswith(('.xlsx', '.xls')):
        return JSONResponse(
            status_code=400,
            content={"detail": "只支持Excel文件 (.xlsx 或 .xls)"}
        )

    # 生成任务ID
    task_id = str(uuid.uuid4())

    # 读取文件内容
    contents = await file.read()
    file_size = len(contents)

    # 创建任务状态
    tasks[task_id] = {
        "task_id": task_id,
        "filename": file.filename,
        "file_size": file_size,
        "target_languages": target_languages.split(','),
        "region_code": region_code,
        "batch_size": batch_size,
        "max_concurrent": max_concurrent,
        "status": "processing",
        "progress": 0,
        "total_rows": 100,  # 模拟数据
        "processed_rows": 0,
        "current_step": "准备处理",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }

    # 启动异步任务模拟翻译进度
    asyncio.create_task(simulate_translation_progress(task_id))

    return {
        "task_id": task_id,
        "filename": file.filename,
        "file_size": file_size,
        "message": "文件上传成功，翻译任务已启动"
    }

# 模拟翻译进度
async def simulate_translation_progress(task_id: str):
    """模拟翻译进度"""
    task = tasks[task_id]
    steps = [
        ("解析Excel文件", 10),
        ("检测需要翻译的列", 20),
        ("准备翻译批次", 30),
        ("正在翻译...", 70),
        ("生成结果文件", 90),
        ("翻译完成", 100)
    ]

    for step_name, progress in steps:
        await asyncio.sleep(2)  # 模拟处理时间
        task["current_step"] = step_name
        task["progress"] = progress
        task["processed_rows"] = int(task["total_rows"] * progress / 100)
        task["updated_at"] = datetime.utcnow().isoformat()

        if progress == 100:
            task["status"] = "completed"
            task["completed_at"] = datetime.utcnow().isoformat()

# 查询翻译状态
@app.get("/api/translation/status/{task_id}")
async def get_translation_status(task_id: str):
    """获取翻译任务状态"""
    if task_id not in tasks:
        return JSONResponse(
            status_code=404,
            content={"detail": f"任务ID {task_id} 不存在"}
        )

    return tasks[task_id]

# 下载翻译结果
@app.get("/api/translation/download/{task_id}")
async def download_translation_result(task_id: str):
    """下载翻译结果"""
    if task_id not in tasks:
        return JSONResponse(
            status_code=404,
            content={"detail": f"任务ID {task_id} 不存在"}
        )

    task = tasks[task_id]
    if task["status"] != "completed":
        return JSONResponse(
            status_code=400,
            content={"detail": "翻译任务尚未完成"}
        )

    # 创建模拟的Excel文件内容
    # 这里只是返回一个简单的文本文件作为示例
    content = f"""翻译结果文件
任务ID: {task_id}
文件名: {task["filename"]}
目标语言: {', '.join(task["target_languages"])}
地区代码: {task["region_code"]}
处理行数: {task["processed_rows"]}/{task["total_rows"]}
完成时间: {task.get("completed_at", "N/A")}

[这是一个模拟的翻译结果文件]
"""

    # 返回文件流
    file_stream = io.BytesIO(content.encode('utf-8'))

    return StreamingResponse(
        file_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=translation_result_{task_id}.xlsx"
        }
    )

# 获取所有任务列表
@app.get("/api/translation/tasks")
async def get_all_tasks():
    """获取所有翻译任务"""
    return {
        "tasks": list(tasks.values()),
        "total": len(tasks)
    }

def main():
    """启动服务器"""
    port = int(os.getenv("SERVER_PORT", 8000))

    print("🎮 游戏本地化翻译系统 - 最小服务器")
    print("=" * 60)
    print(f"🌐 服务地址: http://localhost:{port}")
    print(f"📚 API文档: http://localhost:{port}/docs")
    print(f"🔍 健康检查: http://localhost:{port}/health")
    print(f"ℹ️ 系统信息: http://localhost:{port}/api/info")
    print("=" * 60)
    print("按 Ctrl+C 停止服务器")
    print()

    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n⏹️ 服务器已停止")
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")

if __name__ == "__main__":
    main()