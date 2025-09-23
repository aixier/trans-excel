"""
三阶段翻译管理器
模块化管理不同阶段的翻译任务
"""
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class TranslationPhase(Enum):
    """翻译阶段枚举"""
    PHASE_1_BLANK = "blank_fill"  # 阶段1：填充空白
    PHASE_2_YELLOW = "yellow_source"  # 阶段2：黄色源语言
    PHASE_3_BLUE = "blue_optimize"  # 阶段3：蓝色优化


@dataclass
class PhaseResult:
    """阶段执行结果"""
    phase: TranslationPhase
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    start_time: datetime
    end_time: datetime
    error_messages: List[str]

    @property
    def success_rate(self) -> float:
        """计算成功率"""
        if self.total_tasks == 0:
            return 0.0
        return self.completed_tasks / self.total_tasks

    @property
    def duration_seconds(self) -> float:
        """计算执行时长（秒）"""
        return (self.end_time - self.start_time).total_seconds()


class PhaseTranslationManager:
    """三阶段翻译管理器"""

    def __init__(self, translation_engine=None):
        """
        初始化管理器

        Args:
            translation_engine: 翻译引擎实例（保持LLM独立性）
        """
        self.translation_engine = translation_engine
        self.phase_results: List[PhaseResult] = []
        self.current_phase: Optional[TranslationPhase] = None
        self.phase_callbacks: Dict[TranslationPhase, List[Callable]] = {
            phase: [] for phase in TranslationPhase
        }

        logger.info("三阶段翻译管理器初始化完成")

    async def execute_all_phases(
        self,
        df: pd.DataFrame,
        metadata: Dict[str, Any],
        target_languages: List[str],
        config: Optional[Dict] = None
    ) -> pd.DataFrame:
        """
        执行所有翻译阶段

        Args:
            df: 数据DataFrame
            metadata: 单元格元数据
            target_languages: 目标语言列表
            config: 配置参数

        Returns:
            翻译后的DataFrame
        """
        config = config or {}
        result_df = df.copy()

        # 阶段1：空白单元格填充（带批注）
        if config.get('enable_phase_1', True):
            logger.info("=" * 50)
            logger.info("开始执行阶段1：空白单元格填充")
            logger.info("=" * 50)

            result_df = await self._execute_phase_1(
                result_df, metadata, target_languages, config
            )

        # 阶段2：黄色单元格作为源语言
        if config.get('enable_phase_2', True):
            logger.info("=" * 50)
            logger.info("开始执行阶段2：黄色单元格翻译")
            logger.info("=" * 50)

            result_df = await self._execute_phase_2(
                result_df, metadata, target_languages, config
            )

        # 阶段3：蓝色单元格优化
        if config.get('enable_phase_3', True):
            logger.info("=" * 50)
            logger.info("开始执行阶段3：蓝色单元格优化")
            logger.info("=" * 50)

            result_df = await self._execute_phase_3(
                result_df, metadata, config
            )

        # 生成执行报告
        self._generate_phase_report()

        return result_df

    async def _execute_phase_1(
        self,
        df: pd.DataFrame,
        metadata: Dict[str, Any],
        target_languages: List[str],
        config: Dict
    ) -> pd.DataFrame:
        """
        执行阶段1：空白单元格填充

        特点：
        - 检测空白的目标语言单元格
        - 使用批注作为翻译指导
        - 批量处理提高效率
        """
        self.current_phase = TranslationPhase.PHASE_1_BLANK
        start_time = datetime.now()
        completed = 0
        failed = 0
        errors = []

        try:
            # 使用颜色任务检测器
            from excel_analysis.color_task_detector import ColorTaskDetector
            detector = ColorTaskDetector()

            # 检测阶段1的任务
            tasks = detector.detect_tasks_by_phase(df, metadata, phase=1)
            total_tasks = len(tasks)

            if total_tasks == 0:
                logger.info("阶段1：没有检测到空白单元格需要填充")
                return df

            logger.info(f"阶段1：检测到{total_tasks}个空白单元格需要翻译")

            # 按批次处理
            batch_size = config.get('batch_size', 10)
            batches = self._create_batches(tasks, batch_size)

            for batch_idx, batch in enumerate(batches, 1):
                try:
                    logger.info(f"处理批次 {batch_idx}/{len(batches)}")

                    # 准备批注信息
                    batch_comments = self._extract_batch_comments(batch)

                    # 调用翻译引擎
                    if self.translation_engine:
                        results = await self._translate_batch_with_comments(
                            batch, target_languages, batch_comments, config
                        )

                        # 应用翻译结果
                        for task, result in zip(batch, results):
                            if result:
                                df.at[task.row_index, task.target_column] = result
                                completed += 1
                            else:
                                failed += 1

                    # 触发回调
                    await self._trigger_callbacks(
                        TranslationPhase.PHASE_1_BLANK,
                        {'batch': batch_idx, 'total': len(batches)}
                    )

                except Exception as e:
                    logger.error(f"批次{batch_idx}处理失败: {e}")
                    errors.append(str(e))
                    failed += len(batch)

        except Exception as e:
            logger.error(f"阶段1执行失败: {e}")
            errors.append(str(e))

        # 记录阶段结果
        self.phase_results.append(PhaseResult(
            phase=TranslationPhase.PHASE_1_BLANK,
            total_tasks=total_tasks if 'total_tasks' in locals() else 0,
            completed_tasks=completed,
            failed_tasks=failed,
            start_time=start_time,
            end_time=datetime.now(),
            error_messages=errors
        ))

        return df

    async def _execute_phase_2(
        self,
        df: pd.DataFrame,
        metadata: Dict[str, Any],
        target_languages: List[str],
        config: Dict
    ) -> pd.DataFrame:
        """
        执行阶段2：黄色单元格作为源语言

        特点：
        - 黄色单元格内容作为新的源文本
        - 翻译到同行的其他列
        - 可能覆盖已有内容
        """
        self.current_phase = TranslationPhase.PHASE_2_YELLOW
        start_time = datetime.now()
        completed = 0
        failed = 0
        errors = []

        try:
            from excel_analysis.color_task_detector import ColorTaskDetector
            detector = ColorTaskDetector()

            # 检测阶段2的任务
            tasks = detector.detect_tasks_by_phase(df, metadata, phase=2)
            total_tasks = len(tasks)

            if total_tasks == 0:
                logger.info("阶段2：没有检测到黄色单元格")
                return df

            logger.info(f"阶段2：检测到{total_tasks}个黄色单元格触发的翻译任务")

            # 处理黄色单元格任务
            for task in tasks:
                try:
                    # 特殊提示：这是来自黄色单元格的重要内容
                    special_prompt = f"【重要】此内容来自标记为黄色的单元格，需要特别准确的翻译。"

                    if task.comment:
                        special_prompt += f"\n额外说明：{task.comment}"

                    # 调用翻译
                    if self.translation_engine:
                        result = await self._translate_single_with_prompt(
                            task.source_text,
                            task.target_column,
                            special_prompt,
                            config
                        )

                        if result:
                            df.at[task.row_index, task.target_column] = result
                            completed += 1
                        else:
                            failed += 1

                except Exception as e:
                    logger.error(f"黄色单元格任务处理失败: {e}")
                    errors.append(str(e))
                    failed += 1

        except Exception as e:
            logger.error(f"阶段2执行失败: {e}")
            errors.append(str(e))

        # 记录阶段结果
        self.phase_results.append(PhaseResult(
            phase=TranslationPhase.PHASE_2_YELLOW,
            total_tasks=total_tasks if 'total_tasks' in locals() else 0,
            completed_tasks=completed,
            failed_tasks=failed,
            start_time=start_time,
            end_time=datetime.now(),
            error_messages=errors
        ))

        return df

    async def _execute_phase_3(
        self,
        df: pd.DataFrame,
        metadata: Dict[str, Any],
        config: Dict
    ) -> pd.DataFrame:
        """
        执行阶段3：蓝色单元格优化

        特点：
        - 缩短蓝色单元格的内容
        - 保持核心意思不变
        - 回写到原单元格
        """
        self.current_phase = TranslationPhase.PHASE_3_BLUE
        start_time = datetime.now()
        completed = 0
        failed = 0
        errors = []

        try:
            from excel_analysis.color_task_detector import ColorTaskDetector
            detector = ColorTaskDetector()

            # 检测阶段3的任务
            tasks = detector.detect_tasks_by_phase(df, metadata, phase=3)
            total_tasks = len(tasks)

            if total_tasks == 0:
                logger.info("阶段3：没有检测到蓝色单元格需要优化")
                return df

            logger.info(f"阶段3：检测到{total_tasks}个蓝色单元格需要优化")

            # 处理优化任务
            for task in tasks:
                try:
                    # 构建优化提示
                    optimization_prompt = self._build_optimization_prompt(
                        task.source_text,
                        task.comment,
                        config.get('shorten_ratio', 0.6)
                    )

                    # 调用优化
                    if self.translation_engine:
                        result = await self._optimize_content(
                            task.source_text,
                            optimization_prompt,
                            config
                        )

                        if result:
                            # 回写到原单元格
                            df.at[task.row_index, task.source_column] = result
                            completed += 1
                            logger.info(f"优化完成: 原长度{len(task.source_text)} → 新长度{len(result)}")
                        else:
                            failed += 1

                except Exception as e:
                    logger.error(f"蓝色单元格优化失败: {e}")
                    errors.append(str(e))
                    failed += 1

        except Exception as e:
            logger.error(f"阶段3执行失败: {e}")
            errors.append(str(e))

        # 记录阶段结果
        self.phase_results.append(PhaseResult(
            phase=TranslationPhase.PHASE_3_BLUE,
            total_tasks=total_tasks if 'total_tasks' in locals() else 0,
            completed_tasks=completed,
            failed_tasks=failed,
            start_time=start_time,
            end_time=datetime.now(),
            error_messages=errors
        ))

        return df

    def _create_batches(self, tasks: List, batch_size: int) -> List[List]:
        """创建任务批次"""
        batches = []
        current_batch = []

        for task in tasks:
            current_batch.append(task)
            if len(current_batch) >= batch_size:
                batches.append(current_batch)
                current_batch = []

        if current_batch:
            batches.append(current_batch)

        return batches

    def _extract_batch_comments(self, batch: List) -> Dict[str, str]:
        """提取批次中的批注信息"""
        comments = {}
        for idx, task in enumerate(batch):
            if task.comment:
                comments[f"text_{idx}"] = task.comment
        return comments

    def _build_optimization_prompt(
        self,
        text: str,
        comment: Optional[str],
        shorten_ratio: float
    ) -> str:
        """构建优化提示词"""
        target_length = int(len(text) * shorten_ratio)

        prompt = f"""
请将以下内容优化并缩短至约{target_length}个字符：

原文：{text}

优化要求：
1. 保留核心信息和关键含义
2. 去除冗余表达和修饰词
3. 使用更简洁的表达方式
4. 保持原文的语气和风格
"""

        if comment:
            prompt += f"5. 特别说明：{comment}\n"

        prompt += "\n请直接返回优化后的文本，不需要解释。"

        return prompt

    async def _translate_batch_with_comments(
        self,
        batch: List,
        target_languages: List[str],
        comments: Dict[str, str],
        config: Dict
    ) -> List[str]:
        """带批注的批量翻译（占位实现）"""
        # 这里应该调用translation_engine的方法
        # 保持与LLM的解耦
        if self.translation_engine:
            # 伪代码：实际调用翻译引擎
            # return await self.translation_engine.translate_batch_with_comments(
            #     batch, target_languages, comments, config
            # )
            pass
        return ["翻译结果" for _ in batch]

    async def _translate_single_with_prompt(
        self,
        text: str,
        target_language: str,
        special_prompt: str,
        config: Dict
    ) -> str:
        """单条带特殊提示的翻译（占位实现）"""
        if self.translation_engine:
            # 伪代码：实际调用翻译引擎
            # return await self.translation_engine.translate_with_prompt(
            #     text, target_language, special_prompt, config
            # )
            pass
        return f"{text}_translated"

    async def _optimize_content(
        self,
        text: str,
        optimization_prompt: str,
        config: Dict
    ) -> str:
        """优化内容（占位实现）"""
        if self.translation_engine:
            # 伪代码：实际调用翻译引擎
            # return await self.translation_engine.optimize_text(
            #     text, optimization_prompt, config
            # )
            pass
        return text[:int(len(text) * 0.6)]

    async def _trigger_callbacks(self, phase: TranslationPhase, data: Any):
        """触发阶段回调"""
        for callback in self.phase_callbacks.get(phase, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(phase, data)
                else:
                    callback(phase, data)
            except Exception as e:
                logger.error(f"回调执行失败: {e}")

    def register_callback(self, phase: TranslationPhase, callback: Callable):
        """注册阶段回调函数"""
        self.phase_callbacks[phase].append(callback)
        logger.info(f"为{phase.value}阶段注册了回调函数")

    def _generate_phase_report(self):
        """生成阶段执行报告"""
        logger.info("=" * 50)
        logger.info("三阶段翻译执行报告")
        logger.info("=" * 50)

        for result in self.phase_results:
            logger.info(f"\n{result.phase.value}阶段:")
            logger.info(f"  - 总任务数: {result.total_tasks}")
            logger.info(f"  - 完成数: {result.completed_tasks}")
            logger.info(f"  - 失败数: {result.failed_tasks}")
            logger.info(f"  - 成功率: {result.success_rate:.1%}")
            logger.info(f"  - 耗时: {result.duration_seconds:.2f}秒")

            if result.error_messages:
                logger.info(f"  - 错误信息: {', '.join(result.error_messages[:3])}")

        total_time = sum(r.duration_seconds for r in self.phase_results)
        total_tasks = sum(r.total_tasks for r in self.phase_results)
        total_completed = sum(r.completed_tasks for r in self.phase_results)

        logger.info(f"\n总计:")
        logger.info(f"  - 总任务数: {total_tasks}")
        logger.info(f"  - 总完成数: {total_completed}")
        logger.info(f"  - 总耗时: {total_time:.2f}秒")
        logger.info("=" * 50)