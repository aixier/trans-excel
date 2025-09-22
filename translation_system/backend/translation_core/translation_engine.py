"""
翻译引擎核心类
基于test_concurrent_batch.py的完整架构化实现
支持多LLM提供商切换
"""
import asyncio
import json
import pandas as pd
import time
from datetime import datetime
from typing import List, Dict, Optional, Any
from database.connection import AsyncSession
from project_manager.manager import ProjectManager
from .placeholder_protector import PlaceholderProtector
from .localization_engine import LocalizationEngine
from .terminology_manager import TerminologyManager
from excel_analysis.header_analyzer import HeaderAnalyzer
from excel_analysis.translation_detector import TranslationDetector
from excel_analysis.enhanced_excel_reader import EnhancedExcelReader
from excel_analysis.color_task_detector import ColorTaskDetector, TaskType
from .phase_translation_manager import PhaseTranslationManager

# 使用LLM配置管理器作为唯一数据源
from llm_providers import (
    LLMConfigManager,
    LLMMessage,
    ResponseFormat,
    BaseLLM
)
from config.settings import settings

import logging

logger = logging.getLogger(__name__)


class TranslationEngine:
    """翻译引擎 - 基于Demo的架构化实现"""

    def __init__(self, llm_profile: Optional[str] = None):
        """
        初始化翻译引擎

        Args:
            llm_profile: LLM配置文件名，如果为None则使用active_profile
        """
        self.llm_profile = llm_profile
        self.llm_instance: Optional['BaseLLM'] = None
        self.llm_manager = LLMConfigManager()
        self.client = None  # 不再使用旧的OpenAI客户端

        # 其他组件
        self.project_manager = ProjectManager(None)  # OSS storage will be injected
        self.placeholder_protector = PlaceholderProtector()
        self.localization_engine = LocalizationEngine()
        self.terminology_manager = TerminologyManager()
        self.header_analyzer = HeaderAnalyzer()
        self.translation_detector = TranslationDetector()
        self.enhanced_reader = EnhancedExcelReader()  # 增强的Excel读取器
        self.excel_metadata = {}  # 存储Excel元数据
        self.color_detector = ColorTaskDetector()  # 颜色任务检测器
        self.phase_manager = PhaseTranslationManager(self)  # 三阶段管理器

        # 术语管理相关
        self.current_project_id = None  # 当前项目ID
        self.terminology_loaded = False  # 术语是否已加载

        # 统计信息 (基于Demo)
        self.completed_batches = 0
        self.total_batches = 0
        self.failed_batches = []
        self.total_translated_rows = 0  # 累计翻译的行数

    async def initialize_llm(self):
        """初始化LLM实例"""
        if not self.llm_instance:
            if not self.llm_profile:
                # 使用配置文件中的active_profile
                active_profile = self.llm_manager.get_active_profile()
                if active_profile and active_profile in self.llm_manager.list_profiles():
                    self.llm_profile = active_profile
                    logger.info(f"使用配置文件中的活动配置: {active_profile}")
                else:
                    raise ValueError("没有配置活动的LLM profile，请在llm_configs.json中设置active_profile")

            # 获取LLM实例
            try:
                self.llm_instance = await self.llm_manager.get_llm(self.llm_profile)
                logger.info(f"成功初始化LLM: {self.llm_instance.get_provider_name()} - {self.llm_profile}")
            except Exception as e:
                logger.error(f"初始化LLM失败 ({self.llm_profile}): {e}")
                # 如果失败，尝试使用备用配置
                if self.llm_profile != "qwen-plus" and "qwen-plus" in self.llm_manager.list_profiles():
                    logger.info("尝试使用备用配置: qwen-plus")
                    self.llm_profile = "qwen-plus"
                    self.llm_instance = await self.llm_manager.get_llm(self.llm_profile)
                    logger.info(f"使用备用配置成功: {self.llm_instance.get_provider_name()}")
                else:
                    raise

    async def switch_llm(self, profile_name: str):
        """
        切换LLM配置

        Args:
            profile_name: 新的配置文件名
        """
        if profile_name not in self.llm_manager.list_profiles():
            raise ValueError(f"Profile {profile_name} not found")

        self.llm_profile = profile_name
        self.llm_instance = await self.llm_manager.get_llm(profile_name)
        logger.info(f"Switched to LLM: {self.llm_instance.get_provider_name()} - {profile_name}")

    def get_available_profiles(self) -> List[str]:
        """获取可用的LLM配置文件列表"""
        if self.llm_manager:
            return self.llm_manager.list_profiles()
        return []

    def get_model_info(self) -> Dict[str, Any]:
        """获取当前模型信息"""
        if self.llm_instance:
            return self.llm_instance.get_model_info()
        return {}

    async def process_translation_task(
        self,
        db: AsyncSession,
        task_id: str,
        file_path: str,
        target_languages: List[str] = None,  # None = 自动检测所有需要的语言
        batch_size: int = 3,
        max_concurrent: int = 10,
        max_iterations: int = 5,
        region_code: str = 'na',
        game_background: str = None,
        sheet_names: List[str] = None,  # None = 处理所有sheets
        auto_detect: bool = True,  # 自动检测需要翻译的sheets
        project_id: Optional[str] = None  # 项目ID，用于术语管理
    ):
        """处理翻译任务 - 支持多Sheet处理"""
        try:
            # 初始化LLM
            await self.initialize_llm()

            # 打印模型信息
            if self.llm_instance:
                model_info = self.llm_instance.get_model_info()
                logger.info(f"🚀 开始执行翻译任务: {task_id}")
                logger.info(f"🤖 当前使用模型: {model_info.get('provider', 'Unknown')} - {model_info.get('model', 'Unknown')}")
                logger.info(f"📝 模型详情: {model_info.get('model_name', 'Unknown')}")
                logger.info(f"⚡ 配置文件: {self.llm_profile or 'active_profile'}")
            else:
                logger.error(f"❌ 无法初始化LLM，请检查配置")
                raise RuntimeError("LLM initialization failed")

            # 预加载术语表（如果启用且提供了project_id）
            if settings.terminology_enabled and project_id:
                self.current_project_id = project_id
                try:
                    await self.terminology_manager.preload_all_terminology(db, project_id)
                    self.terminology_loaded = True
                    logger.info(f"✅ 术语表预加载成功: {project_id}")
                except Exception as e:
                    logger.warning(f"⚠️ 术语表预加载失败: {e}，继续翻译但不使用术语")
                    self.terminology_loaded = False
            elif not settings.terminology_enabled:
                logger.info("术语系统已禁用（通过配置）")

            # 更新任务状态
            await self.project_manager.update_task_progress(
                db, task_id, status='analyzing'
            )

            # 1. 分析Excel文件结构
            xl_file = pd.ExcelFile(file_path)
            all_sheet_names = xl_file.sheet_names
            logger.info(f"Excel文件包含 {len(all_sheet_names)} 个Sheet: {all_sheet_names}")

            # 2. 确定要处理的sheets
            if sheet_names:
                sheets_to_process = [s for s in sheet_names if s in all_sheet_names]
            else:
                sheets_to_process = all_sheet_names

            # 3. 自动检测需要翻译的sheets
            # 注意：现在不依赖target_languages，让TranslationDetector自动检测所有需要翻译的内容
            if auto_detect:
                sheets_to_process = await self._detect_sheets_with_content(
                    file_path, sheets_to_process
                )

            logger.info(f"将处理 {len(sheets_to_process)}/{len(all_sheet_names)} 个Sheets: {sheets_to_process}")

            if not sheets_to_process:
                logger.info("没有需要翻译的Sheet")
                await self.project_manager.update_task_progress(
                    db, task_id, status='completed'
                )
                return

            # 4. 存储所有Sheet的结果
            all_results = {}
            total_translated = 0
            self.total_translated_rows = 0  # 重置累计翻译行数

            # 初始化Sheet进度字典
            sheet_progress = {}
            for sheet in sheets_to_process:
                sheet_progress[sheet] = {
                    'total_rows': len(pd.read_excel(file_path, sheet_name=sheet)),
                    'translated_rows': 0,
                    'status': 'pending'
                }

            # 5. 逐个处理每个Sheet
            for sheet_idx, sheet_name in enumerate(sheets_to_process, 1):
                logger.info(f"\n{'='*50}")
                logger.info(f"处理Sheet {sheet_idx}/{len(sheets_to_process)}: {sheet_name}")
                logger.info(f"{'='*50}")

                # 使用增强读取器加载当前Sheet（包含元数据）
                try:
                    df, sheet_metadata = self.enhanced_reader.read_excel_with_metadata(file_path, sheet_name)

                    # 存储元数据供后续使用
                    if sheet_metadata:
                        self.excel_metadata[sheet_name] = sheet_metadata.get(sheet_name, {})

                        # 提取批注作为翻译上下文
                        comments = self.enhanced_reader.extract_comments_as_context(
                            self.excel_metadata[sheet_name]
                        )
                        if comments:
                            logger.info(f"发现 {len(comments)} 个批注，将作为翻译参考")

                        # 提取带颜色的单元格
                        colored_cells = self.enhanced_reader.get_colored_cells(
                            self.excel_metadata[sheet_name]
                        )
                        if colored_cells:
                            logger.info(f"发现 {len(colored_cells)} 个带颜色的单元格")

                    logger.info(f"Sheet '{sheet_name}' 加载成功（含元数据），总行数: {len(df)}")

                except Exception as e:
                    logger.warning(f"增强读取失败，降级到普通读取: {e}")
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    logger.info(f"Sheet '{sheet_name}' 加载成功（普通模式），总行数: {len(df)}")

                # 清理列名（去除特殊字符如冒号）
                df.columns = [col.strip(':').strip() for col in df.columns]

                # 动态调整批次大小（大文件优化）
                if len(df) > 5000:
                    current_batch_size = min(30, batch_size * 3)  # 最大30行
                    logger.info(f"大文件优化：批次大小调整为 {current_batch_size}")
                elif len(df) > 1000:
                    current_batch_size = min(20, batch_size * 2)  # 中等文件20行
                    logger.info(f"中等文件优化：批次大小调整为 {current_batch_size}")
                else:
                    current_batch_size = min(10, batch_size)  # 小文件10行

                # 2. 智能分析表头结构
                sheet_info = self.header_analyzer.analyze_sheet(df, sheet_name)
                logger.info(f"表头分析完成，可翻译行数: {sheet_info.translatable_rows}")

                # 3. 初始任务检测
                initial_tasks = self.translation_detector.detect_translation_tasks(df, sheet_info)
                logger.info(f"初始检测到翻译任务: {len(initial_tasks)}个")

                if not initial_tasks:
                    logger.info(f"Sheet '{sheet_name}' 没有需要翻译的内容")
                    all_results[sheet_name] = df
                    continue

                await self.project_manager.update_task_progress(
                    db, task_id,
                    status='translating',
                    current_sheet=sheet_name
                )

                # 记录当前Sheet的初始行数
                sheet_total_rows = len(df)
                sheet_translated_rows = 0
                sheet_progress[sheet_name]['status'] = 'translating'

                # 4. 迭代翻译 - 真正的增量处理
                current_df = df.copy()
                iteration = 0
                failed_batch_count = 0

                # 动态调整参数
                dynamic_batch_size = current_batch_size
                dynamic_timeout = 90  # 初始超时90秒

                while iteration < max_iterations:
                    iteration += 1

                    # 每轮重新检测剩余任务 - 关键改进！
                    remaining_tasks = self.translation_detector.detect_translation_tasks(current_df, sheet_info)

                    if not remaining_tasks:
                        logger.info(f"Sheet '{sheet_name}' - 第{iteration}轮迭代：所有任务已完成")
                        break

                    logger.info(f"Sheet '{sheet_name}' - 第{iteration}轮迭代：检测到 {len(remaining_tasks)} 个剩余任务")

                    # 根据迭代次数和失败情况动态调整批次大小
                    if iteration > 1 and failed_batch_count > 0:
                        # 有失败，减小批次大小
                        dynamic_batch_size = max(1, dynamic_batch_size // 2)
                        # 增加超时时间
                        dynamic_timeout = min(300, dynamic_timeout * 1.5)  # 增加最大超时到300秒
                        logger.info(f"调整策略：批次大小={dynamic_batch_size}，超时={dynamic_timeout}秒")

                    # 检测长文本任务，进一步调整
                    max_text_length = max([len(task.source_text) for task in remaining_tasks] or [0])
                    if max_text_length > 300:  # 降低阈值，更早优化
                        dynamic_batch_size = min(dynamic_batch_size, 3)  # 最多3个任务一批
                        dynamic_timeout = max(dynamic_timeout, 180)  # 至少180秒超时
                        if max_text_length > 500:  # 长文本
                            dynamic_batch_size = min(dynamic_batch_size, 2)  # 最多2个任务一批
                            dynamic_timeout = max(dynamic_timeout, 240)  # 4分钟超时
                        if max_text_length > 800:  # 超长文本（如909字符）
                            dynamic_batch_size = 1  # 单个任务一批
                            dynamic_timeout = 360  # 6分钟超时
                        logger.info(f"检测到长文本(最长{max_text_length}字符)，调整批次大小={dynamic_batch_size}，超时={dynamic_timeout}秒")

                    # 创建新批次
                    batches = self.translation_detector.group_tasks_by_batch(remaining_tasks, dynamic_batch_size)
                    self.total_batches = len(batches)
                    self.completed_batches = 0
                    self.failed_batches = []

                    logger.info(f"Sheet '{sheet_name}' - 第{iteration}轮迭代：创建 {len(batches)} 个批次")

                    # 更新迭代状态
                    status = 'iterating' if iteration > 1 else 'translating'
                    await self.project_manager.update_task_progress(
                        db, task_id,
                        current_iteration=iteration,
                        status=status
                    )

                    # 并发处理批次（传入动态超时参数和Sheet信息）
                    semaphore = asyncio.Semaphore(max_concurrent)
                    translation_results = await self._process_batches_concurrent_with_timeout(
                        db, task_id, batches, target_languages, semaphore,
                        region_code, game_background, iteration, dynamic_timeout,
                        sheet_name, sheet_progress
                    )

                    # 记录失败批次数
                    failed_batch_count = len(self.failed_batches)
                    if failed_batch_count > 0:
                        logger.warning(f"第{iteration}轮有 {failed_batch_count} 个批次失败")

                    # 应用翻译结果到DataFrame
                    translated_count = self._apply_translation_results(current_df, translation_results)
                    total_translated += translated_count

                    # 更新进度
                    await self.project_manager.update_task_progress(
                        db, task_id,
                        translated_rows=total_translated
                    )

                    # 检查剩余任务数
                    final_remaining = self._count_remaining_tasks(current_df, sheet_info)
                    logger.info(f"Sheet '{sheet_name}' - 第{iteration}轮迭代完成，剩余任务: {final_remaining}")

                # 保存当前Sheet结果
                all_results[sheet_name] = current_df

            # 6. 保存所有Sheet结果并完成任务
            await self._save_multi_sheet_results(db, task_id, all_results, file_path)

        except Exception as e:
            logger.error(f"翻译任务处理失败: {task_id}, 错误: {e}")
            await self.project_manager.update_task_progress(
                db, task_id,
                status='failed',
                error_message=str(e)
            )
            raise

    async def _process_batches_concurrent(
        self,
        db: AsyncSession,
        task_id: str,
        batches: List[List],
        target_languages: List[str],
        semaphore: asyncio.Semaphore,
        region_code: str,
        game_background: str,
        iteration: int
    ) -> Dict:
        """并发处理批次 - 基于Demo的并发逻辑"""
        # 保留原方法用于兼容性，调用新方法with默认超时
        return await self._process_batches_concurrent_with_timeout(
            db, task_id, batches, target_languages, semaphore,
            region_code, game_background, iteration, 90
        )

    async def _process_batches_concurrent_with_timeout(
        self,
        db: AsyncSession,
        task_id: str,
        batches: List[List],
        target_languages: List[str],
        semaphore: asyncio.Semaphore,
        region_code: str,
        game_background: str,
        iteration: int,
        timeout: int,
        sheet_name: str = None,
        sheet_progress: dict = None
    ) -> Dict:
        """并发处理批次 - 支持动态超时"""
        tasks = []

        for batch_id, batch in enumerate(batches, 1):
            task = self._translate_batch_with_retry(
                db, task_id, batch, batch_id, target_languages,
                semaphore, region_code, game_background, iteration,
                timeout=timeout, sheet_name=sheet_name, sheet_progress=sheet_progress
            )
            tasks.append(task)

        # 并发执行所有批次
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 合并结果
        translation_results = {}
        for result in results:
            if isinstance(result, dict):
                translation_results.update(result)
            else:
                logger.error(f"批次处理失败: {result}")

        return translation_results

    async def _translate_batch_with_retry(
        self,
        db: AsyncSession,
        task_id: str,
        batch: List,
        batch_id: int,
        target_languages: List[str],
        semaphore: asyncio.Semaphore,
        region_code: str,
        game_background: str,
        iteration: int,
        max_retry_attempts: int = 2,
        retry_base_delay: float = 3.0,
        timeout: int = 90,  # 支持动态超时
        sheet_name: str = None,
        sheet_progress: dict = None
    ) -> Dict:
        """批次翻译带重试机制 - 支持动态超时和智能重试"""
        async with semaphore:
            start_time = time.time()

            # 检测批次中的最长文本
            max_length = max([len(task.source_text) for task in batch] or [0])

            # 动态调整重试参数
            if max_length > 1000:
                max_retry_attempts = 3  # 长文本增加重试次数
                retry_base_delay = 5.0  # 增加基础延迟
                logger.info(f"📦 批次{batch_id}: 处理 {len(batch)}个任务 (最长{max_length}字符, 超时: {timeout}秒, 最多重试{max_retry_attempts}次)")
            else:
                logger.info(f"📦 批次{batch_id}: 开始处理 {len(batch)}个任务 (超时: {timeout}秒)")

            # 准备输入数据 - 添加占位符保护
            input_texts = []
            protected_texts = {}  # 保存占位符映射

            for i, task in enumerate(batch):
                # 保护占位符
                protected_text, placeholders = self.placeholder_protector.protect_placeholders(task.source_text)
                protected_texts[f"batch_{batch_id}_text_{i}"] = placeholders

                input_texts.append({
                    "id": f"batch_{batch_id}_text_{i}",
                    "text": protected_text
                })

            # 重试机制 - 增强版
            for attempt in range(max_retry_attempts + 1):
                try:
                    if attempt > 0:
                        retry_delay = retry_base_delay * (2 ** (attempt - 1))
                        # 每次重试增加超时时间
                        current_timeout = min(timeout * (1 + attempt * 0.5), 600)  # 最多10分钟
                        logger.info(f"🔄 批次{batch_id}: 第{attempt + 1}次尝试，延迟{retry_delay:.1f}s，超时{current_timeout:.0f}s")
                        await asyncio.sleep(retry_delay)
                    else:
                        current_timeout = timeout

                    # 从批次中提取目标语言（每个任务都知道自己的目标语言）
                    batch_target_languages = list(set([task.target_language for task in batch]))

                    # 如果区域代码是'auto'，根据语言自动选择
                    actual_region_code = region_code
                    if region_code == 'auto' and batch_target_languages:
                        # 使用第一个目标语言来确定区域
                        actual_region_code = self.localization_engine.get_region_for_language(batch_target_languages[0])
                        logger.debug(f"自动选择区域: {batch_target_languages[0]} -> {actual_region_code}")

                    # 提取批次的批注信息
                    batch_comments = {}
                    for idx, task in enumerate(batch):
                        # 获取源单元格地址
                        source_cell_addr = self._get_cell_address_from_task(task)
                        # 查找批注
                        if source_cell_addr and sheet_name in self.excel_metadata:
                            sheet_metadata = self.excel_metadata[sheet_name]
                            if source_cell_addr in sheet_metadata:
                                cell_meta = sheet_metadata[source_cell_addr]
                                if cell_meta.comment:
                                    batch_comments[f"text_{idx}"] = cell_meta.comment

                    # 术语匹配（如果启用且已加载术语）
                    matched_terms = {}
                    terminology_text = ""
                    if settings.terminology_enabled and self.terminology_loaded and self.current_project_id:
                        batch_texts = [task.source_text for task in batch]
                        matched_terms = self.terminology_manager.match_terminology_for_batch(
                            batch_texts,
                            self.current_project_id,
                            batch_target_languages if batch_target_languages else ['en']
                        )

                        # 格式化术语用于prompt
                        if matched_terms:
                            terminology_text = self.terminology_manager.format_terminology_for_prompt(
                                matched_terms,
                                batch_target_languages if batch_target_languages else ['en']
                            )
                            logger.debug(f"批次{batch_id}: 匹配到{len(matched_terms)}个术语")

                            # 检查是否可以使用直接替换策略（如果配置允许）
                            if settings.terminology_direct_replace_enabled:
                                can_direct_replace = self._check_direct_replace_strategy(batch_texts, matched_terms)
                            else:
                                can_direct_replace = False

                            # 如果可以直接替换，跳过LLM调用
                            if can_direct_replace:
                                batch_results = self._apply_direct_replacement(
                                    batch,
                                    matched_terms,
                                    batch_target_languages if batch_target_languages else ['en']
                                )

                                # 记录统计信息
                                self.completed_batches += 1
                                self.total_translated_rows += len(batch)

                                end_time = time.time()
                                logger.info(f"✅ 批次{batch_id}: 直接替换完成，耗时 {end_time - start_time:.1f}秒")

                                return batch_results

                    # 创建区域化提示词 (升级Demo的通用提示词，带批注和术语)
                    system_prompt = self.localization_engine.create_batch_prompt(
                        [task.source_text for task in batch],
                        batch_target_languages if batch_target_languages else ['en'],  # 默认英语
                        actual_region_code,
                        game_background,
                        batch[0].task_type if batch else 'new',
                        cell_comments=batch_comments,  # 传递批注信息
                        terminology=matched_terms  # 传递匹配的术语
                    )

                    # 构建请求消息
                    user_message = f"请翻译以下中文文本：\n{json.dumps(input_texts, ensure_ascii=False, indent=2)}"

                    # 调用LLM
                    if self.llm_instance:
                        # 使用LLM Provider
                        model_info = self.llm_instance.get_model_info()
                        if batch_id == 1 and attempt == 0:  # 只在第一个批次的第一次尝试时打印
                            logger.info(f"🤖 使用模型: {model_info.get('provider', 'Unknown')} - {model_info.get('model', 'Unknown')} ({model_info.get('model_name', 'Unknown')})")
                            logger.info(f"🛠️  配置: 温度={0.3}, 最大tokens={4000}, 区域={actual_region_code}")

                        llm_messages = [
                            LLMMessage(role="system", content=system_prompt),
                            LLMMessage(role="user", content=user_message)
                        ]

                        # 使用配置的max_tokens值，如果没有则使用默认值
                        max_tokens = self.llm_instance.config.max_tokens if hasattr(self.llm_instance, 'config') else 8000

                        response = await self.llm_instance.chat_completion(
                            messages=llm_messages,
                            temperature=0.3,
                            max_tokens=max_tokens,
                            response_format=ResponseFormat.JSON,
                            timeout=current_timeout
                        )

                        # 处理响应
                        result = json.loads(response.content)
                        translations = result.get("translations", [])

                        # 记录token使用
                        tokens_used = response.usage.get("total_tokens", 0) if response.usage else 0
                    else:
                        # LLM未初始化
                        raise RuntimeError("LLM instance not initialized")

                    # 还原占位符
                    for translation_item in translations:
                        if "id" in translation_item and translation_item["id"] in protected_texts:
                            placeholders = protected_texts[translation_item["id"]]
                            # 还原所有语言的翻译结果
                            for lang_key in translation_item:
                                if lang_key != "id" and translation_item[lang_key]:
                                    translation_item[lang_key] = self.placeholder_protector.restore_placeholders(
                                        translation_item[lang_key], placeholders
                                    )

                    # 记录API统计
                    api_calls = 1

                    # 每个批次都更新进度，让用户能实时看到进度变化
                    try:
                        # 更新API调用统计（累加）
                        await self.project_manager.update_task_progress(
                            db, task_id,
                            api_calls=api_calls,
                            tokens_used=tokens_used
                        )
                    except Exception as update_error:
                        logger.warning(f"更新进度失败: {update_error}")

                    # 构建返回结果
                    batch_results = {}
                    for i, translation in enumerate(translations):
                        if i < len(batch):
                            task = batch[i]
                            # 使用任务自己的目标语言
                            batch_results[task.row_index] = {
                                task.target_language: translation.get(task.target_language, translation) if isinstance(translation, dict) else translation
                            }

                    elapsed = time.time() - start_time
                    self.completed_batches += 1

                    # 计算批次中的唯一行数（同一行的多个任务算一行）
                    unique_rows_in_batch = len(set(task.row_index for task in batch))
                    self.total_translated_rows += unique_rows_in_batch

                    # 如果有Sheet信息，更新Sheet级别的进度
                    if sheet_name and sheet_progress:
                        sheet_progress[sheet_name]['translated_rows'] += unique_rows_in_batch

                    # 实时更新翻译行数进度（包括Sheet进度）
                    try:
                        await self.project_manager.update_task_progress(
                            db, task_id,
                            translated_rows=self.total_translated_rows,
                            sheet_progress=sheet_progress if sheet_progress else None
                        )
                    except Exception as update_error:
                        logger.warning(f"更新行数进度失败: {update_error}")

                    retry_info = f" (第{attempt + 1}次尝试)" if attempt > 0 else ""
                    logger.info(f"✅ 批次{batch_id}: 完成翻译{retry_info} {len(translations)}条 | "
                              f"耗时{elapsed:.1f}s | tokens: {tokens_used} | "
                              f"进度: {self.completed_batches}/{self.total_batches}")

                    return batch_results

                except Exception as e:
                    elapsed = time.time() - start_time

                    if attempt < max_retry_attempts:
                        logger.warning(f"⚠️ 批次{batch_id}: 第{attempt + 1}次尝试失败 | 错误: {e}")
                    else:
                        logger.error(f"❌ 批次{batch_id}: 重试{max_retry_attempts}次后最终失败 | 总耗时{elapsed:.1f}s | 错误: {e}")
                        self.failed_batches.append(batch_id)

            return {}  # 失败时返回空结果

    def _apply_translation_results(self, df: pd.DataFrame, results: Dict) -> int:
        """应用翻译结果到DataFrame"""
        translated_count = 0

        for row_index, translations in results.items():
            for lang, translation in translations.items():
                if translation and translation.strip():
                    # 找到对应的语言列 - 更精确的匹配
                    lang_upper = lang.upper()
                    matched_col = None

                    # 首先尝试精确匹配
                    if lang_upper in df.columns:
                        matched_col = lang_upper
                    # 其次尝试小写匹配
                    elif lang.lower() in [col.lower() for col in df.columns]:
                        for col in df.columns:
                            if col.lower() == lang.lower():
                                matched_col = col
                                break

                    # 如果列不存在，创建新列
                    if not matched_col:
                        matched_col = lang_upper
                        if matched_col not in df.columns:
                            df[matched_col] = ''
                            logger.info(f"创建新语言列: {matched_col}")

                    # 应用翻译
                    if matched_col:
                        df.at[row_index, matched_col] = translation
                        translated_count += 1
                        logger.debug(f"应用翻译: 行{row_index}, 列{matched_col} = {translation[:30]}...")

        return translated_count

    def _get_cell_address_from_task(self, task) -> Optional[str]:
        """从任务获取单元格地址"""
        if hasattr(task, 'row_index') and hasattr(task, 'source_column'):
            # 简单实现：假设列索引
            col_letter = 'B'  # 通常中文在B列
            row_num = task.row_index + 2  # +2因为有标题行且Excel从1开始
            return f"{col_letter}{row_num}"
        return None

    def _count_remaining_tasks(self, df: pd.DataFrame, sheet_info) -> int:
        """统计剩余翻译任务数量"""
        tasks = self.translation_detector.detect_translation_tasks(df, sheet_info)
        return len([task for task in tasks if task.task_type in ['new', 'modify', 'shorten']])

    async def _detect_sheets_with_content(
        self,
        file_path: str,
        sheet_names: List[str]
    ) -> List[str]:
        """检测哪些sheets有内容需要翻译（不依赖target_languages）"""
        translatable_sheets = []

        for sheet_name in sheet_names:
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                # 清理列名
                df.columns = [col.strip(':').strip() for col in df.columns]

                # 使用HeaderAnalyzer和TranslationDetector检测
                sheet_info = self.header_analyzer.analyze_sheet(df, sheet_name)
                tasks = self.translation_detector.detect_translation_tasks(df, sheet_info)

                if tasks:
                    translatable_sheets.append(sheet_name)
                    logger.info(f"✅ Sheet '{sheet_name}' 需要翻译 ({len(tasks)} 个任务)")
                else:
                    logger.info(f"⏭️ Sheet '{sheet_name}' 跳过（无需翻译）")

            except Exception as e:
                logger.warning(f"检测Sheet '{sheet_name}' 失败: {e}")

        return translatable_sheets


    async def _save_multi_sheet_results(
        self,
        db: AsyncSession,
        task_id: str,
        all_results: Dict[str, pd.DataFrame],
        original_file_path: str
    ):
        """保存多Sheet结果"""
        try:
            # 生成输出文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = original_file_path.rsplit('.', 1)[0]
            output_path = f"{base_name}_translated_{timestamp}.xlsx"

            # 检查是否有元数据需要保留
            if self.excel_metadata:
                logger.info(f"保留原始格式和批注...")
                # 先用pandas写入基础数据
                with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                    for sheet_name, df in all_results.items():
                        df.to_excel(writer, sheet_name=sheet_name, index=False)

                        # 如果有元数据，应用到工作表
                        if sheet_name in self.excel_metadata:
                            worksheet = writer.sheets[sheet_name]
                            metadata = self.excel_metadata[sheet_name]

                            # 应用批注和颜色
                            from openpyxl.comments import Comment
                            from openpyxl.styles import Font, PatternFill

                            for cell_address, cell_metadata in metadata.items():
                                try:
                                    cell = worksheet[cell_address]

                                    # 添加批注
                                    if cell_metadata.comment:
                                        comment = Comment(cell_metadata.comment, "Translation System")
                                        cell.comment = comment

                                    # 设置字体颜色
                                    if cell_metadata.font_color:
                                        color_hex = cell_metadata.font_color.replace('#', '')
                                        cell.font = Font(
                                            color=color_hex,
                                            bold=cell_metadata.font_bold,
                                            italic=cell_metadata.font_italic
                                        )

                                    # 设置填充色
                                    if cell_metadata.fill_color:
                                        color_hex = cell_metadata.fill_color.replace('#', '')
                                        cell.fill = PatternFill(
                                            start_color=color_hex,
                                            end_color=color_hex,
                                            fill_type='solid'
                                        )
                                except Exception as e:
                                    logger.warning(f"应用元数据失败 {cell_address}: {e}")
            else:
                # 没有元数据，使用普通保存
                with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                    for sheet_name, df in all_results.items():
                        df.to_excel(writer, sheet_name=sheet_name, index=False)

            logger.info(f"✅ 多Sheet翻译结果已保存: {output_path}")

            # 更新任务状态
            await self.project_manager.update_task_progress(
                db, task_id,
                status='completed'
            )

        except Exception as e:
            logger.error(f"保存多Sheet结果失败: {e}")
            raise

    async def _save_and_complete_task(self, db: AsyncSession, task_id: str, df: pd.DataFrame, original_file_path: str):
        """保存结果并完成任务（单Sheet兼容）"""
        try:
            # 生成输出文件名 (基于Demo的命名规则)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = original_file_path.rsplit('.', 1)[0]
            output_path = f"{base_name}_completed_{timestamp}.xlsx"

            # 保存Excel文件
            df.to_excel(output_path, index=False)
            logger.info(f"翻译结果已保存: {output_path}")

            # 更新任务状态
            await self.project_manager.update_task_progress(
                db, task_id,
                status='completed'
            )

        except Exception as e:
            logger.error(f"保存翻译结果失败: {e}")
            raise

    def _check_direct_replace_strategy(self, batch_texts: List[str], matched_terms: Dict) -> bool:
        """检查是否可以使用直接替换策略（简单术语替换，不需要LLM）"""
        if not matched_terms:
            return False

        # 检查每个文本是否只包含术语（不含其他需要翻译的内容）
        for text in batch_texts:
            # 移除所有术语后，如果还有中文字符，则不能直接替换
            temp_text = text
            for term in matched_terms.keys():
                temp_text = temp_text.replace(term, '')

            # 检查是否还有中文字符（需要LLM翻译）
            if any('\u4e00' <= char <= '\u9fff' for char in temp_text):
                return False

        return True

    def _apply_direct_replacement(
        self,
        batch: List,
        matched_terms: Dict,
        target_languages: List[str]
    ) -> Dict:
        """直接应用术语替换，跳过LLM调用"""
        batch_results = {}

        for task in batch:
            translated_text = task.source_text
            # 按优先级排序术语，优先替换长的术语
            sorted_terms = sorted(
                matched_terms.items(),
                key=lambda x: (len(x[0]), x[1].priority),
                reverse=True
            )

            # 应用术语替换
            for source, entry in sorted_terms:
                if task.target_language in entry.target:
                    translated_text = translated_text.replace(
                        source,
                        entry.target[task.target_language]
                    )

            batch_results[task.row_index] = {
                task.target_language: translated_text
            }

        logger.info(f"✨ 使用直接替换策略处理{len(batch)}个任务（节省API调用）")
        return batch_results

    def _verify_terminology_usage(
        self,
        source_text: str,
        translated_text: str,
        matched_terms: Dict,
        target_language: str
    ) -> Dict[str, Any]:
        """验证术语是否被正确使用"""
        verification_result = {
            'all_terms_used': True,
            'missing_terms': [],
            'incorrect_terms': [],
            'success_rate': 100.0
        }

        if not matched_terms:
            return verification_result

        total_terms = 0
        correct_terms = 0

        for source, entry in matched_terms.items():
            if source in source_text and target_language in entry.target:
                total_terms += 1
                expected_translation = entry.target[target_language]

                # 检查译文中是否包含期望的术语翻译
                if expected_translation in translated_text:
                    correct_terms += 1
                else:
                    verification_result['missing_terms'].append({
                        'source': source,
                        'expected': expected_translation,
                        'found': False
                    })

        if total_terms > 0:
            verification_result['success_rate'] = (correct_terms / total_terms) * 100
            verification_result['all_terms_used'] = (correct_terms == total_terms)

        if verification_result['success_rate'] < 100:
            logger.warning(
                f"术语使用验证: 成功率 {verification_result['success_rate']:.1f}%, "
                f"缺失术语: {len(verification_result['missing_terms'])}"
            )

        return verification_result

    async def cleanup(self):
        """清理资源"""
        if self.llm_instance and hasattr(self.llm_instance, 'close'):
            await self.llm_instance.close()
            logger.info("LLM instance closed")

        # 清理管理器中的所有实例
        if self.llm_manager and hasattr(self.llm_manager, '_llm_instances'):
            for profile, llm in self.llm_manager._llm_instances.items():
                if llm != self.llm_instance and hasattr(llm, 'close'):
                    await llm.close()
            logger.info("All LLM resources cleaned up")