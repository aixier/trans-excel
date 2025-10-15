"""Translation result post-processor."""

import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class PostProcessor:
    """翻译后处理器，用于根据任务类型对翻译结果进行特殊处理"""

    # 后处理器映射表
    PROCESSORS = {
        'caps': lambda x: x.upper(),
        'lower': lambda x: x.lower(),
        'title': lambda x: x.title(),
        'reverse': lambda x: x[::-1],
    }

    @staticmethod
    def process_caps(text: str) -> str:
        """
        将文本转换为全大写

        Args:
            text: 原始文本

        Returns:
            转换为大写的文本
        """
        return text.upper()

    @staticmethod
    def process_lower(text: str) -> str:
        """
        将文本转换为全小写

        Args:
            text: 原始文本

        Returns:
            转换为小写的文本
        """
        return text.lower()

    @staticmethod
    def process_title(text: str) -> str:
        """
        将文本转换为首字母大写

        Args:
            text: 原始文本

        Returns:
            首字母大写的文本
        """
        return text.title()

    @staticmethod
    def process_reverse(text: str) -> str:
        """
        反转文本（用于测试）

        Args:
            text: 原始文本

        Returns:
            反转的文本
        """
        return text[::-1]

    @staticmethod
    def apply_post_processing(task: Dict[str, Any], result: str) -> str:
        """
        根据任务类型应用相应的后处理

        Args:
            task: 任务字典
            result: LLM翻译结果

        Returns:
            经过后处理的最终结果
        """
        task_type = task.get('task_type', 'normal')

        # 如果是普通任务类型，直接返回
        if task_type == 'normal':
            return result

        # 获取对应的后处理器
        processor = PostProcessor.PROCESSORS.get(task_type)

        if processor:
            try:
                processed_result = processor(result)
                logger.debug(
                    f"Applied post-processing for task {task.get('task_id')}: "
                    f"'{result}' → '{processed_result}'"
                )
                return processed_result
            except Exception as e:
                logger.error(
                    f"Post-processing failed for task {task.get('task_id')}: {e}"
                )
                return result
        else:
            # 未知的任务类型，直接返回原结果
            logger.warning(f"Unknown task type: {task_type}, no post-processing applied")
            return result

    @staticmethod
    def get_supported_types() -> list:
        """
        获取支持的后处理类型列表

        Returns:
            支持的类型列表
        """
        return list(PostProcessor.PROCESSORS.keys())

    @staticmethod
    def register_processor(task_type: str, processor_func):
        """
        注册新的后处理器

        Args:
            task_type: 任务类型名称
            processor_func: 处理函数
        """
        PostProcessor.PROCESSORS[task_type] = processor_func
        logger.info(f"Registered post-processor for type: {task_type}")