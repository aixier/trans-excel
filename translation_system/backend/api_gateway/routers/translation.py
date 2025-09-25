"""
翻译服务API路由
基于架构文档的HTTP接口实现，支持文件上传和进度轮询
"""
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from datetime import datetime
from typing import List, Optional
import uuid
import logging
import pandas as pd
import os
import glob

from database.connection import get_db, AsyncSession
from database.models import TranslationTask
from translation_core.translation_engine import TranslationEngine
from project_manager.manager import ProjectManager
from file_service.storage.oss_storage import OSSStorage
from ..models.task import (
    TranslationUploadRequest, TaskResponse, TaskStatusResponse,
    TaskProgressResponse, TaskListResponse, TaskStatus,
    TaskProgress, TranslationMetrics
)


router = APIRouter()
logger = logging.getLogger(__name__)

# 内存中存储任务（临时解决方案）
# 格式: {task_id: {"task_id": str, "status": str, "created_at": datetime, ...}}
TASK_STORE = {}


def process_language_params(
    source_langs: Optional[str],
    target_languages: Optional[str]
) -> tuple[Optional[List[str]], Optional[List[str]]]:
    """
    处理源语言和目标语言参数，实现智能语言选择策略

    Args:
        source_langs: 源语言列表字符串，如 "CH,EN"
        target_languages: 目标语言列表字符串，如 "PT,TH,VN"

    Returns:
        (source_list, target_list): 处理后的源语言和目标语言列表
    """
    # 1. 解析源语言
    source_list = None
    if source_langs:
        source_list = [s.strip().upper() for s in source_langs.split(',')]
        logger.info(f"用户指定源语言: {source_list}")

    # 2. 解析目标语言
    target_list = None
    if target_languages:
        target_list = [t.strip().upper() for t in target_languages.split(',')]

    # 3. 智能源语言选择（当未指定时）
    if not source_list and target_list:
        # 定义亚洲语言集合
        asian_langs = {'VN', 'JP', 'KR', 'TH', 'TW'}

        # 检查目标语言类型
        if any(t in asian_langs for t in target_list):
            # 亚洲语言优先使用中文作为源语言
            source_list = ['CH']
            logger.info(f"目标包含亚洲语言，自动选择源语言: CH")
        else:
            # 其他语言优先英文，中文作为备选
            source_list = ['EN', 'CH']
            logger.info(f"目标为其他语言，自动选择源语言优先级: EN > CH")

    # 4. 确保源语言不在目标语言中
    if source_list and target_list:
        original_targets = target_list.copy()
        target_list = [t for t in target_list if t not in source_list]

        excluded = set(original_targets) - set(target_list)
        if excluded:
            logger.info(f"从目标语言中排除源语言: {excluded}")

    return source_list, target_list


# 依赖注入
def get_translation_engine():
    """获取翻译引擎实例"""
    return TranslationEngine()


def get_project_manager():
    """获取项目管理器实例"""
    return ProjectManager(OSSStorage())


@router.post("/upload", response_model=TaskResponse)
async def upload_translation_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    source_langs: Optional[str] = Form(None, description="源语言列表，逗号分隔，如：CH,EN。不传则自动检测"),
    target_languages: str = Form(None, description="目标语言列表，逗号分隔，如：pt,th,ind,vn。不传则自动检测所有需要的语言"),
    sheet_names: Optional[str] = Form(None, description="要处理的Sheet名称，逗号分隔，不填则处理所有"),
    batch_size: int = Form(10, description="批次大小，最大30行"),
    max_concurrent: int = Form(20, description="最大并发数，限制20"),
    region_code: str = Form("cn-hangzhou", description="地区代码"),
    game_background: Optional[str] = Form(None, description="游戏背景"),
    auto_detect: bool = Form(True, description="自动检测需要翻译的sheets"),
    project_id: Optional[str] = Form(None, description="项目ID，用于术语管理"),  # 新增project_id
    db: AsyncSession = Depends(get_db),
    translation_engine: TranslationEngine = Depends(get_translation_engine),
    project_manager: ProjectManager = Depends(get_project_manager)
):
    """
    上传翻译文件并开始翻译任务
    基于Demo的完整工作流程
    """
    try:
        # 验证文件格式
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Only Excel files are supported")

        # 处理源语言和目标语言
        source_langs_list, target_languages_list = process_language_params(
            source_langs, target_languages
        )

        logger.info(f"源语言配置: {source_langs_list}")
        logger.info(f"目标语言配置: {target_languages_list}")

        # 解析sheet名称
        sheets_to_process = None
        if sheet_names:
            sheets_to_process = [s.strip() for s in sheet_names.split(',')]

        # 创建翻译任务记录
        task_id = str(uuid.uuid4())

        # 存储任务信息到内存
        TASK_STORE[task_id] = {
            "task_id": task_id,
            "file_name": file.filename,
            "status": TaskStatus.UPLOADING.value,
            "created_at": datetime.utcnow(),
            "source_langs": source_langs,
            "target_languages": target_languages,
            "progress": 0,
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0
        }

        # 保存上传的文件
        file_content = await file.read()
        file_path = f"temp/{task_id}_{file.filename}"

        # 保存到临时目录
        with open(file_path, "wb") as f:
            f.write(file_content)

        # 计算总翻译任务数（分析Excel文件实际结构）
        xl_file = pd.ExcelFile(file_path)
        total_translation_tasks = 0

        # 导入分析工具
        from excel_analysis.header_analyzer import HeaderAnalyzer
        header_analyzer = HeaderAnalyzer()

        sheets_to_analyze = sheets_to_process if sheets_to_process else xl_file.sheet_names

        for sheet_name in sheets_to_analyze:
            if sheet_name in xl_file.sheet_names:
                # 读取Sheet数据
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                sheet_rows = len(df)

                # 分析Sheet结构获取目标语言列数
                try:
                    sheet_info = header_analyzer.analyze_sheet(df, sheet_name)
                    if sheet_info and sheet_info.columns:
                        # 计算目标语言列数（TYPE=TARGET的列）
                        target_columns = [col for col in sheet_info.columns if col.column_type.value == 'target']
                        lang_count = len(target_columns)

                        if lang_count == 0:
                            # 如果没有检测到目标列，使用指定的语言数
                            lang_count = len(target_languages_list) if target_languages_list else 0
                    else:
                        # 分析失败时使用指定语言数
                        lang_count = len(target_languages_list) if target_languages_list else 0
                except Exception as e:
                    logger.warning(f"Sheet '{sheet_name}' 分析失败: {e}")
                    lang_count = len(target_languages_list) if target_languages_list else 0

                sheet_translation_count = sheet_rows * lang_count
                total_translation_tasks += sheet_translation_count

                logger.info(f"Sheet '{sheet_name}': {sheet_rows}行 × {lang_count}语言列 = {sheet_translation_count}个翻译任务")

        total_rows = total_translation_tasks
        logger.info(f"文件总翻译任务数: {total_rows}")

        # 更新内存存储中的任务总数
        if task_id in TASK_STORE:
            TASK_STORE[task_id]["total_tasks"] = total_rows

        # 准备配置信息
        task_config = {
            'source_langs': source_langs_list,  # 新增源语言配置
            'target_languages': target_languages_list,
            'sheet_names': sheets_to_process,  # 新增
            'batch_size': batch_size,
            'max_concurrent': max_concurrent,
            'region_code': region_code,
            'game_background': game_background,
            'auto_detect': auto_detect,  # 新增
            'file_name': file.filename
        }

        translation_task = TranslationTask(
            id=task_id,
            project_id=project_id or 'default',  # 使用传入的project_id
            version_id='temp-version',
            task_name=f"Translation: {file.filename}",
            input_file_id='temp-file',
            config=task_config,
            total_rows=total_rows,
            max_iterations=5,
            sheet_names=sheets_to_process,  # 新增
            total_sheets=len(sheets_to_process) if sheets_to_process else len(xl_file.sheet_names),  # 新增
            status='uploading'
        )

        db.add(translation_task)
        await db.commit()

        logger.info(f"📁 文件上传成功: {file.filename}, 任务ID: {task_id}")

        # 后台启动翻译任务（传递project_id和source_langs）
        background_tasks.add_task(
            start_translation_task,
            task_id, file_path, source_langs_list, target_languages_list,
            batch_size, max_concurrent, region_code, game_background,
            translation_engine, sheets_to_process, auto_detect, project_id
        )

        return TaskResponse(
            task_id=task_id,
            status=TaskStatus.UPLOADING,
            message="文件上传成功，翻译任务已启动",
            created_at=datetime.utcnow()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


async def start_translation_task(
    task_id: str,
    file_path: str,
    source_langs: Optional[List[str]],  # 添加源语言参数
    target_languages: List[str],
    batch_size: int,
    max_concurrent: int,
    region_code: str,
    game_background: str,
    translation_engine: TranslationEngine,
    sheet_names: List[str] = None,
    auto_detect: bool = True,
    project_id: Optional[str] = None  # 添加project_id参数
):
    """后台翻译任务执行函数"""
    # 创建新的数据库会话
    from database.connection import get_async_session

    try:
        logger.info(f"🚀 开始执行翻译任务: {task_id}, 项目: {project_id or 'default'}")

        # 更新任务状态为处理中
        if task_id in TASK_STORE:
            TASK_STORE[task_id]["status"] = TaskStatus.PROCESSING.value

        # 使用独立的数据库会话
        async with get_async_session() as db:
            # 调用翻译引擎处理，传递project_id和source_langs
            await translation_engine.process_translation_task(
                db=db,
                task_id=task_id,
                file_path=file_path,
                source_langs=source_langs,  # 传递源语言配置
                target_languages=target_languages,
                batch_size=batch_size,
                max_concurrent=max_concurrent,
                region_code=region_code,
                game_background=game_background,
                sheet_names=sheet_names,
                auto_detect=auto_detect,
                project_id=project_id  # 传递project_id
            )

            # 任务成功完成，更新状态
            if task_id in TASK_STORE:
                TASK_STORE[task_id]["status"] = TaskStatus.COMPLETED.value
                TASK_STORE[task_id]["progress"] = 100

    except Exception as e:
        logger.error(f"翻译任务执行失败: {task_id}, 错误: {e}")
        # 更新任务状态为失败
        if task_id in TASK_STORE:
            TASK_STORE[task_id]["status"] = TaskStatus.FAILED.value
            TASK_STORE[task_id]["error_message"] = str(e)
        # 更新任务状态为失败
        async with get_async_session() as db:
            from sqlalchemy import text
            await db.execute(
                text("UPDATE translation_tasks SET status = 'failed', error_message = :error WHERE id = :task_id"),
                {"error": str(e), "task_id": task_id}
            )
            await db.commit()


@router.get("/tasks/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    project_manager: ProjectManager = Depends(get_project_manager)
):
    """
    获取翻译任务状态
    基于HTTP轮询的进度查询接口
    """
    try:
        # 先从内存存储中查找
        if task_id in TASK_STORE:
            task = TASK_STORE[task_id]
            return TaskStatusResponse(
                task_id=task_id,
                status=TaskStatus(task["status"]),
                file_name=task.get("file_name", "Unknown"),
                source_language=task.get("source_langs", "auto"),
                target_languages=task.get("target_languages", []),
                created_at=task["created_at"],
                updated_at=task.get("updated_at", task["created_at"]),
                progress=TaskProgress(
                    current=task.get("completed_tasks", 0),
                    total=task.get("total_tasks", 0),
                    percentage=task.get("progress", 0)
                ),
                metrics=TranslationMetrics(
                    total_tasks=task.get("total_tasks", 0),
                    completed_tasks=task.get("completed_tasks", 0),
                    failed_tasks=task.get("failed_tasks", 0),
                    processing_rate=0.0,
                    estimated_time_remaining=0
                ),
                error_message=task.get("error_message", None),
                result_file=task.get("result_file", None)
            )

        # 如果内存中没有，尝试从数据库获取
        # 获取任务详细进度
        task_progress = await project_manager.get_task_progress(db, task_id)

        return TaskStatusResponse(
            task_id=task_progress['task_id'],
            status=TaskStatus(task_progress['status']),
            progress=TaskProgress(
                total_rows=task_progress['progress']['total_rows'],
                translated_rows=task_progress['progress']['translated_rows'],
                current_iteration=task_progress['progress']['current_iteration'],
                max_iterations=task_progress['progress']['max_iterations'],
                completion_percentage=task_progress['progress']['completion_percentage'],
                estimated_time_remaining=task_progress['progress']['estimated_time_remaining']
            ),
            error_message=task_progress['error_message'],
            created_at=task_progress['created_at'],
            updated_at=task_progress['updated_at'],
            download_url=None  # 完成后生成下载链接
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取任务状态失败: {task_id}, 错误: {e}")
        raise HTTPException(status_code=500, detail="Failed to get task status")


@router.get("/tasks/{task_id}/progress", response_model=TaskProgressResponse)
async def get_task_progress(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    project_manager: ProjectManager = Depends(get_project_manager)
):
    """
    获取任务进度详情 - 高频轮询接口
    优化的进度查询，返回最少必要信息
    """
    try:
        # 先从内存存储中查找
        if task_id in TASK_STORE:
            task = TASK_STORE[task_id]
            return TaskProgressResponse(
                task_id=task_id,
                status=TaskStatus(task["status"]),
                progress=TaskProgress(
                    current=task.get("completed_tasks", 0),
                    total=task.get("total_tasks", 0),
                    percentage=task.get("progress", 0)
                ),
                statistics=TranslationMetrics(
                    total_tasks=task.get("total_tasks", 0),
                    completed_tasks=task.get("completed_tasks", 0),
                    failed_tasks=task.get("failed_tasks", 0),
                    processing_rate=0.0,
                    estimated_time_remaining=0
                )
            )

        # 如果内存中没有，尝试从数据库获取
        task_progress = await project_manager.get_task_progress(db, task_id)

        return TaskProgressResponse(
            task_id=task_progress['task_id'],
            status=TaskStatus(task_progress['status']),
            progress=TaskProgress(
                total_rows=task_progress['progress']['total_rows'],
                translated_rows=task_progress['progress']['translated_rows'],
                current_iteration=task_progress['progress']['current_iteration'],
                max_iterations=task_progress['progress']['max_iterations'],
                completion_percentage=task_progress['progress']['completion_percentage'],
                estimated_time_remaining=task_progress['progress']['estimated_time_remaining']
            ),
            statistics=TranslationMetrics(
                total_api_calls=task_progress['statistics']['total_api_calls'],
                total_tokens_used=task_progress['statistics']['total_tokens_used'],
                total_cost=task_progress['statistics']['total_cost'],
                average_response_time=0.0,  # 可以后续添加
                success_rate=0.95  # 可以后续添加
            ),
            last_updated=task_progress['updated_at']
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取任务进度失败: {task_id}, 错误: {e}")
        raise HTTPException(status_code=500, detail="Failed to get task progress")


@router.get("/tasks", response_model=TaskListResponse)
async def list_translation_tasks(
    status: Optional[TaskStatus] = None,
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """
    列出翻译任务
    支持状态筛选和分页
    """
    try:
        offset = (page - 1) * limit

        # 从内存存储中获取任务
        all_tasks = list(TASK_STORE.values())

        # 按状态过滤
        if status:
            filtered_tasks = [t for t in all_tasks if t["status"] == status.value]
        else:
            filtered_tasks = all_tasks

        # 按创建时间降序排序
        filtered_tasks.sort(key=lambda x: x["created_at"], reverse=True)

        # 分页
        total = len(filtered_tasks)
        paginated_tasks = filtered_tasks[offset:offset + limit]

        # 转换为响应格式
        task_responses = []
        for task in paginated_tasks:
            task_responses.append(TaskStatusResponse(
                task_id=task["task_id"],
                status=TaskStatus(task["status"]),
                file_name=task.get("file_name", "Unknown"),
                source_language=task.get("source_langs", "auto"),
                target_languages=task.get("target_languages", []),
                created_at=task["created_at"],
                updated_at=task.get("updated_at", task["created_at"]),
                progress=TaskProgress(
                    current=task.get("completed_tasks", 0),
                    total=task.get("total_tasks", 0),
                    percentage=task.get("progress", 0)
                ),
                metrics=TranslationMetrics(
                    total_tasks=task.get("total_tasks", 0),
                    completed_tasks=task.get("completed_tasks", 0),
                    failed_tasks=task.get("failed_tasks", 0),
                    processing_rate=0.0,
                    estimated_time_remaining=0
                ),
                error_message=task.get("error_message", None),
                result_file=task.get("result_file", None)
            ))

        return TaskListResponse(
            tasks=task_responses,
            total=total,
            page=page,
            limit=limit,
            pages=(total + limit - 1) // limit if total > 0 else 0
        )

    except Exception as e:
        logger.error(f"列出翻译任务失败: {e}")
        raise HTTPException(status_code=500, detail="Failed to list tasks")


@router.delete("/tasks/{task_id}")
async def cancel_translation_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    取消翻译任务
    """
    try:
        # 查找任务
        # 这里简化处理，实际应该使用SQLAlchemy查询
        task = None  # await db.get(TranslationTask, task_id)

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # 只能取消未完成的任务
        if task.status in ['completed', 'failed', 'cancelled']:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel task with status: {task.status}"
            )

        # 更新任务状态
        # task.status = 'cancelled'
        # await db.commit()

        logger.info(f"✅ 翻译任务已取消: {task_id}")

        return {"message": "Task cancelled successfully", "task_id": task_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消翻译任务失败: {task_id}, 错误: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel task")


@router.post("/analyze")
async def analyze_excel_structure(
    file: UploadFile = File(...)
):
    """分析Excel文件结构，返回Sheet信息"""
    try:
        # 保存临时文件
        temp_path = f"temp/analyze_{uuid.uuid4()}_{file.filename}"
        content = await file.read()

        # 创建temp目录（如果不存在）
        os.makedirs("temp", exist_ok=True)

        with open(temp_path, "wb") as f:
            f.write(content)

        # 分析文件
        xl_file = pd.ExcelFile(temp_path)
        sheets_info = []

        for sheet_name in xl_file.sheet_names:
            df = pd.read_excel(temp_path, sheet_name=sheet_name)

            # 清理列名
            df.columns = [col.strip(':').strip() for col in df.columns]

            # 检测语言列
            language_columns = []
            for col in df.columns:
                col_upper = col.upper()
                if col_upper in ['CH', 'EN', 'PT', 'TH', 'IND', 'VN', 'ES', 'TR', 'JA', 'KO']:
                    language_columns.append(col)

            sheets_info.append({
                "name": sheet_name,
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "columns": list(df.columns)[:20],  # 最多返回20列
                "language_columns": language_columns,
                "sample_data": df.head(3).to_dict('records')  # 返回前3行样本
            })

        # 清理临时文件
        os.remove(temp_path)

        return {
            "file_name": file.filename,
            "total_sheets": len(xl_file.sheet_names),
            "sheets": sheets_info
        }

    except Exception as e:
        logger.error(f"分析文件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}/download")
async def download_translation_result(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    project_manager: ProjectManager = Depends(get_project_manager)
):
    """
    下载翻译结果 - 直接返回文件
    """
    try:
        # 检查任务状态
        task_progress = await project_manager.get_task_progress(db, task_id)

        if task_progress['status'] != 'completed':
            raise HTTPException(
                status_code=400,
                detail="Task is not completed yet"
            )

        # 查找翻译结果文件
        # 文件保存格式: temp/{task_id}_{original_filename}_translated_{timestamp}.xlsx
        result_files = glob.glob(f"temp/{task_id}_*_translated_*.xlsx")

        if not result_files:
            # 如果没有找到带时间戳的文件，尝试查找其他格式
            result_files = glob.glob(f"temp/{task_id}_*.xlsx")
            # 过滤掉原始文件（不含translated的）
            result_files = [f for f in result_files if 'translated' in f]

        if not result_files:
            logger.error(f"翻译结果文件未找到: task_id={task_id}")
            raise HTTPException(
                status_code=404,
                detail="Translation result file not found"
            )

        # 使用最新的文件（如果有多个）
        result_file = sorted(result_files)[-1]

        # 获取原始文件名用于下载
        original_filename = "translated.xlsx"
        try:
            # 从任务配置中获取原始文件名
            from sqlalchemy import select
            task_query = select(TranslationTask).where(TranslationTask.id == task_id)
            result = await db.execute(task_query)
            task = result.scalar_one_or_none()
            if task and task.config:
                original_filename = task.config.get('file_name', 'translated.xlsx')
                # 移除扩展名并添加_translated后缀
                base_name = original_filename.rsplit('.', 1)[0]
                original_filename = f"{base_name}_translated.xlsx"
        except:
            pass

        logger.info(f"发送翻译结果文件: {result_file} as {original_filename}")

        # 直接返回文件
        return FileResponse(
            path=result_file,
            filename=original_filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成下载链接失败: {task_id}, 错误: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate download link")