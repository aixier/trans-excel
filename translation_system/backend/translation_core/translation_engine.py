"""
翻译引擎核心类
基于test_concurrent_batch.py的完整架构化实现
"""
import asyncio
import json
import pandas as pd
import time
from datetime import datetime
from typing import List, Dict, Optional
from openai import AsyncOpenAI
from config.settings import settings
from database.connection import AsyncSession
from project_manager.manager import ProjectManager
from .placeholder_protector import PlaceholderProtector
from .localization_engine import LocalizationEngine
from .terminology_manager import TerminologyManager
from excel_analysis.header_analyzer import HeaderAnalyzer
from excel_analysis.translation_detector import TranslationDetector
import logging

logger = logging.getLogger(__name__)


class TranslationEngine:
    """翻译引擎 - 基于Demo的架构化实现"""

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url
        )
        self.project_manager = ProjectManager(None)  # OSS storage will be injected
        self.placeholder_protector = PlaceholderProtector()
        self.localization_engine = LocalizationEngine()
        self.terminology_manager = TerminologyManager()
        self.header_analyzer = HeaderAnalyzer()
        self.translation_detector = TranslationDetector()

        # 统计信息 (基于Demo)
        self.completed_batches = 0
        self.total_batches = 0
        self.failed_batches = []

    async def process_translation_task(
        self,
        db: AsyncSession,
        task_id: str,
        file_path: str,
        target_languages: List[str],
        batch_size: int = 3,
        max_concurrent: int = 10,
        max_iterations: int = 5,
        region_code: str = 'na',
        game_background: str = None,
        sheet_names: List[str] = None,  # None = 处理所有sheets
        auto_detect: bool = True  # 自动检测需要翻译的sheets
    ):
        """处理翻译任务 - 支持多Sheet处理"""
        try:
            logger.info(f"开始处理翻译任务: {task_id}")

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
            if auto_detect:
                sheets_to_process = await self._detect_translatable_sheets(
                    file_path, sheets_to_process, target_languages
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

            # 5. 逐个处理每个Sheet
            for sheet_idx, sheet_name in enumerate(sheets_to_process, 1):
                logger.info(f"\n{'='*50}")
                logger.info(f"处理Sheet {sheet_idx}/{len(sheets_to_process)}: {sheet_name}")
                logger.info(f"{'='*50}")

                # 加载当前Sheet
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                logger.info(f"Sheet '{sheet_name}' 加载成功，总行数: {len(df)}")

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

                # 3. 检测翻译任务
                translation_tasks = self.translation_detector.detect_translation_tasks(df, sheet_info)
                logger.info(f"检测到翻译任务: {len(translation_tasks)}个")

                if not translation_tasks:
                    logger.info(f"Sheet '{sheet_name}' 没有需要翻译的内容")
                    all_results[sheet_name] = df
                    continue

                # 4. 创建批次 (基于Demo的批处理逻辑)
                batches = self.translation_detector.group_tasks_by_batch(translation_tasks, current_batch_size)
                self.total_batches = len(batches)

                await self.project_manager.update_task_progress(
                    db, task_id,
                    status='translating',
                    current_sheet=sheet_name
                )

                # 5. 迭代翻译 (基于Demo的迭代逻辑)
                current_df = df.copy()
                iteration = 0

                while iteration < max_iterations:
                    iteration += 1
                    logger.info(f"Sheet '{sheet_name}' - 开始第{iteration}轮迭代翻译")

                    # 更新迭代状态
                    status = 'iterating' if iteration > 1 else 'translating'
                    await self.project_manager.update_task_progress(
                        db, task_id,
                        current_iteration=iteration,
                        status=status
                    )

                    # 并发处理批次 (基于Demo的并发逻辑)
                    semaphore = asyncio.Semaphore(max_concurrent)
                    translation_results = await self._process_batches_concurrent(
                        db, task_id, batches, target_languages, semaphore,
                        region_code, game_background, iteration
                    )

                    # 应用翻译结果到DataFrame
                    translated_count = self._apply_translation_results(current_df, translation_results)
                    total_translated += translated_count

                    # 更新进度
                    await self.project_manager.update_task_progress(
                        db, task_id,
                        translated_rows=total_translated
                    )

                    # 检查是否完成
                    remaining_tasks = self._count_remaining_tasks(current_df, sheet_info)
                    if remaining_tasks == 0:
                        logger.info(f"Sheet '{sheet_name}' - 第{iteration}轮迭代完成所有翻译")
                        break

                    logger.info(f"Sheet '{sheet_name}' - 第{iteration}轮迭代完成，剩余任务: {remaining_tasks}")

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
        tasks = []

        for batch_id, batch in enumerate(batches, 1):
            task = self._translate_batch_with_retry(
                db, task_id, batch, batch_id, target_languages,
                semaphore, region_code, game_background, iteration
            )
            tasks.append(task)

        # 并发执行所有批次 (与Demo逻辑一致)
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
        retry_base_delay: float = 3.0
    ) -> Dict:
        """批次翻译带重试机制 - 基于Demo的重试逻辑"""
        async with semaphore:
            start_time = time.time()
            logger.info(f"📦 批次{batch_id}: 开始处理 {len(batch)}个任务")

            # 准备输入数据 (与Demo格式一致)
            input_texts = []
            for i, task in enumerate(batch):
                input_texts.append({
                    "id": f"batch_{batch_id}_text_{i}",
                    "text": task.source_text
                })

            # 重试机制 (与Demo逻辑一致)
            for attempt in range(max_retry_attempts + 1):
                try:
                    if attempt > 0:
                        retry_delay = retry_base_delay * (2 ** (attempt - 1))
                        logger.info(f"🔄 批次{batch_id}: 第{attempt + 1}次尝试，延迟{retry_delay:.1f}s")
                        await asyncio.sleep(retry_delay)

                    # 创建区域化提示词 (升级Demo的通用提示词)
                    system_prompt = self.localization_engine.create_batch_prompt(
                        [task.source_text for task in batch],
                        target_languages,
                        region_code,
                        game_background,
                        batch[0].task_type if batch else 'new'
                    )

                    # 构建请求消息 (与Demo格式一致)
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"请翻译以下中文文本：\n{json.dumps(input_texts, ensure_ascii=False, indent=2)}"}
                    ]

                    # 调用LLM API (与Demo一致)
                    response = await self.client.chat.completions.create(
                        model=settings.llm_model,
                        messages=messages,
                        temperature=0.3,
                        max_tokens=4000,
                        response_format={"type": "json_object"},
                        timeout=90
                    )

                    # 处理响应 (与Demo格式一致)
                    result = json.loads(response.choices[0].message.content)
                    translations = result.get("translations", [])

                    # 记录API统计
                    api_calls = 1
                    tokens_used = response.usage.total_tokens if response.usage else 0

                    # 减少数据库更新频率，只在特定批次更新
                    if batch_id % 5 == 0 or batch_id == self.total_batches:
                        try:
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
                            # 动态构建结果，根据实际的目标语言
                            lang_result = {}
                            for lang in target_languages:
                                lang_result[lang] = translation.get(lang, '')
                            batch_results[task.row_index] = lang_result

                    elapsed = time.time() - start_time
                    self.completed_batches += 1

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

                    if matched_col:
                        df.at[row_index, matched_col] = translation
                        translated_count += 1
                        logger.debug(f"应用翻译: 行{row_index}, 列{matched_col} = {translation[:30]}...")
                    else:
                        logger.warning(f"找不到语言列: {lang} (可用列: {list(df.columns)})")

        return translated_count

    def _count_remaining_tasks(self, df: pd.DataFrame, sheet_info) -> int:
        """统计剩余翻译任务数量"""
        tasks = self.translation_detector.detect_translation_tasks(df, sheet_info)
        return len([task for task in tasks if task.task_type in ['new', 'modify', 'shorten']])

    async def _detect_translatable_sheets(
        self,
        file_path: str,
        sheet_names: List[str],
        target_languages: List[str]
    ) -> List[str]:
        """自动检测需要翻译的sheets"""
        translatable_sheets = []

        for sheet_name in sheet_names:
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)

                # 清理列名
                df.columns = [col.strip(':').strip() for col in df.columns]

                # 检查是否有目标语言列且为空
                has_empty_target = False
                for lang in target_languages:
                    lang_upper = lang.upper()
                    if lang_upper in [col.upper() for col in df.columns]:
                        # 找到对应列
                        for col in df.columns:
                            if col.upper() == lang_upper:
                                # 检查是否有空值
                                if df[col].isna().any() or (df[col] == '').any():
                                    has_empty_target = True
                                    break

                if has_empty_target:
                    translatable_sheets.append(sheet_name)
                    logger.info(f"✅ Sheet '{sheet_name}' 需要翻译")
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

            # 使用ExcelWriter保存多个sheets
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