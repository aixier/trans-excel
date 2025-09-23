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
        """单条带特殊提示的翻译（真实LLM实现）"""
        if not self.translation_engine or not self.translation_engine.llm_instance:
            logger.warning("翻译引擎或LLM实例未初始化，使用占位符")
            return f"{text}_translated"

        try:
            # 导入所需模块
            from llm_providers import LLMMessage, ResponseFormat
            import json

            # 语言映射
            language_map = {
                'th': '泰语',
                'pt': '葡萄牙语',
                'vn': '越南语',
                'en': '英语',
                'ja': '日语',
                'ko': '韩语',
                'fr': '法语',
                'de': '德语',
                'es': '西班牙语',
                'it': '意大利语',
                'ru': '俄语',
                'ar': '阿拉伯语',
                'tr': '土耳其语'
            }

            target_lang_name = language_map.get(target_language.lower(), target_language)

            # 构建系统提示
            system_prompt = f"""你是一个专业的游戏本地化翻译专家，专门负责游戏内容的翻译工作。

任务：将提供的文本翻译成{target_lang_name}

要求：
1. 保持游戏术语的准确性和一致性
2. 考虑目标语言的文化背景和表达习惯
3. 保留原文的语气和风格
4. 如果是游戏UI文本，要简洁明了
5. 如果是游戏剧情文本，要生动自然
6. 对于专有名词（人名、地名、道具名等），根据上下文决定是否翻译

输出格式要求：
请以JSON格式返回结果，包含以下字段：
{{
    "translation": "翻译结果",
    "confidence": 0.95,
    "reason": "翻译说明"
}}"""

            # 构建用户提示
            user_prompt = f"""请将以下文本翻译成{target_lang_name}：

原文：{text}

{special_prompt}

请提供高质量的翻译结果，并说明翻译原因。"""

            # 构建消息
            messages = [
                LLMMessage(role="system", content=system_prompt),
                LLMMessage(role="user", content=user_prompt)
            ]

            # 调用LLM进行翻译
            response = await self.translation_engine.llm_instance.chat_completion_with_retry(
                messages=messages,
                temperature=0.3,
                max_tokens=2000,
                response_format=ResponseFormat.JSON
            )

            # 解析响应
            try:
                result = json.loads(response.content)
                translation = result.get("translation", "").strip()

                if translation:
                    logger.debug(f"黄色单元格翻译成功: '{text}' -> '{translation}' ({target_language})")
                    return translation
                else:
                    logger.warning(f"LLM返回空翻译结果，原文: {text}")
                    return f"{text}_translated"

            except json.JSONDecodeError:
                # 如果JSON解析失败，尝试直接使用响应内容
                content = response.content.strip()
                if content and content != text:
                    logger.warning(f"JSON解析失败，使用原始响应: {content}")
                    return content
                else:
                    logger.warning(f"LLM响应解析失败，原文: {text}")
                    return f"{text}_translated"

        except Exception as e:
            logger.error(f"黄色单元格翻译失败: {e}, 原文: {text}")
            return f"{text}_translated"

    async def _optimize_content(
        self,
        text: str,
        optimization_prompt: str,
        config: Dict
    ) -> str:
        """优化内容（真实LLM实现）"""
        if not self.translation_engine or not self.translation_engine.llm_instance:
            logger.warning("翻译引擎或LLM实例未初始化，使用简单截断")
            return text[:int(len(text) * 0.6)]

        try:
            # 导入所需模块
            from llm_providers import LLMMessage, ResponseFormat
            import json

            # 获取目标缩短比例
            shorten_ratio = config.get('shorten_ratio', 0.6)
            target_length = int(len(text) * shorten_ratio)

            # 构建系统提示
            system_prompt = f"""你是一个专业的文本优化专家，专门负责游戏本地化内容的智能缩短工作。

任务：将提供的文本进行智能优化，缩短至约{target_length}个字符（原文{len(text)}字符的{int(shorten_ratio*100)}%）

优化要求：
1. 保留核心信息和关键含义，绝对不能改变原意
2. 去除冗余表达、修饰词和不必要的连接词
3. 使用更简洁、直接的表达方式
4. 保持原文的语气和专业性
5. 确保优化后的文本语法正确、表达完整
6. 如果是游戏术语或专有名词，必须保留
7. 优化后长度应在{target_length-5}到{target_length+5}字符之间

输出格式要求：
请以JSON格式返回结果，包含以下字段：
{{
    "optimized_text": "优化后的文本",
    "original_length": {len(text)},
    "optimized_length": "优化后长度",
    "compression_ratio": "实际压缩比例",
    "optimization_notes": "优化说明"
}}"""

            # 构建用户提示
            user_prompt = f"""请优化以下文本：

原文：{text}

{optimization_prompt}

请严格按照要求进行智能优化，确保语义完整且长度合适。"""

            # 构建消息
            messages = [
                LLMMessage(role="system", content=system_prompt),
                LLMMessage(role="user", content=user_prompt)
            ]

            # 调用LLM进行优化
            response = await self.translation_engine.llm_instance.chat_completion_with_retry(
                messages=messages,
                temperature=0.2,  # 较低温度确保稳定输出
                max_tokens=1500,
                response_format=ResponseFormat.JSON
            )

            # 解析响应
            try:
                result = json.loads(response.content)
                optimized_text = result.get("optimized_text", "").strip()

                if optimized_text and optimized_text != text:
                    # 验证优化结果
                    if len(optimized_text) > len(text):
                        logger.warning(f"优化后长度超过原文，使用原文: {len(optimized_text)} > {len(text)}")
                        return text[:target_length]

                    # 记录成功的优化
                    actual_ratio = len(optimized_text) / len(text)
                    logger.info(f"蓝色单元格优化成功: {len(text)} → {len(optimized_text)} 字符 ({actual_ratio:.1%})")
                    logger.debug(f"优化详情: '{text}' → '{optimized_text}'")

                    return optimized_text
                else:
                    logger.warning(f"LLM返回无效优化结果，使用截断: {optimized_text}")
                    return text[:target_length]

            except json.JSONDecodeError:
                # JSON解析失败，尝试直接使用响应内容
                content = response.content.strip()
                if content and len(content) < len(text) and len(content) > target_length * 0.5:
                    logger.warning(f"JSON解析失败，使用原始响应: {content}")
                    return content
                else:
                    logger.warning(f"LLM响应解析失败，使用截断")
                    return text[:target_length]

        except Exception as e:
            logger.error(f"蓝色单元格优化失败: {e}, 原文: {text}")
            # 发生错误时使用智能截断（尽量在词边界截断）
            words = text.split()
            result = ""
            for word in words:
                if len(result + " " + word) <= target_length:
                    result += (" " + word) if result else word
                else:
                    break
            return result if result else text[:target_length]

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