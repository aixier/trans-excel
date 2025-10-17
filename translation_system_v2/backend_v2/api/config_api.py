"""Configuration API endpoints."""

from fastapi import APIRouter, HTTPException
import logging
from pathlib import Path
import yaml

from utils.config_manager import config_manager

router = APIRouter(prefix="/api/config", tags=["config"])
logger = logging.getLogger(__name__)


@router.get("/options")
async def get_config_options():
    """
    Get available configuration options (rules, processors, etc).

    Returns:
        Available rules, rule_sets, processors, and processor_sets
    """
    try:
        # Load rules config
        rules_config_path = Path(__file__).parent.parent / 'config' / 'rules.yaml'
        processors_config_path = Path(__file__).parent.parent / 'config' / 'processors.yaml'

        rules_data = {}
        processors_data = {}

        # Load rules if file exists
        if rules_config_path.exists():
            with open(rules_config_path, 'r', encoding='utf-8') as f:
                rules_data = yaml.safe_load(f) or {}

        # Load processors if file exists
        if processors_config_path.exists():
            with open(processors_config_path, 'r', encoding='utf-8') as f:
                processors_data = yaml.safe_load(f) or {}

        # Convert rules dict to list with id field
        rules_list = []
        for rule_id, rule_config in rules_data.get('rules', {}).items():
            rules_list.append({
                'id': rule_id,
                'name': rule_config.get('name', rule_id),
                'description': rule_config.get('description', ''),
                'enabled': rule_config.get('enabled', True),
                'priority': rule_config.get('priority', 5),
                'requiresTranslationFirst': rule_config.get('requires_translation_first', False),
                'parameters': rule_config.get('parameters', {})
            })

        # Convert processors dict to list with id field
        processors_list = []
        for processor_id, processor_config in processors_data.get('processors', {}).items():
            processors_list.append({
                'id': processor_id,
                'name': processor_config.get('name', processor_id),
                'description': processor_config.get('description', ''),
                'type': processor_config.get('type', 'unknown'),
                'enabled': processor_config.get('enabled', True),
                'requiresLLM': processor_config.get('requires_llm', True),
                'parameters': processor_config.get('parameters', {})
            })

        # Extract available options
        return {
            'rules': rules_list,
            'rule_sets': list(rules_data.get('rule_sets', {}).keys()),
            'processors': processors_list,
            'processor_sets': list(processors_data.get('processor_sets', {}).keys()),
            'target_languages': ['EN', 'JP', 'TH', 'PT', 'VN', 'KR'],  # Common target languages
            'llm_models': list(config_manager.get('llm.providers', {}).keys())
        }

    except Exception as e:
        logger.error(f"Failed to get config options: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get config options: {str(e)}")


@router.get("/templates")
async def get_config_templates():
    """
    Get pre-configured task configuration templates.

    Returns:
        List of configuration templates for common workflows
    """
    try:
        templates = [
            {
                'id': 'standard_translation',
                'name': '标准翻译',
                'description': '标准翻译流程，支持空单元格和黄色标记',
                'config': {
                    'rule_set': 'translation',
                    'processor': 'llm_qwen',
                    'target_langs': ['EN', 'JP', 'TH'],
                    'extract_context': True,
                    'max_workers': 10
                }
            },
            {
                'id': 'caps_transformation',
                'name': 'CAPS大写转换',
                'description': '将翻译结果转换为大写（需要先完成翻译）',
                'config': {
                    'rule_set': 'caps_only',
                    'processor': 'uppercase',
                    'requires_parent': True,
                    'max_workers': 20
                }
            },
            {
                'id': 'quick_translation',
                'name': '快速翻译',
                'description': '仅翻译空单元格，速度较快',
                'config': {
                    'rule_set': 'translation',
                    'processor': 'llm_qwen',
                    'target_langs': ['EN'],
                    'extract_context': False,
                    'max_workers': 20
                }
            },
            {
                'id': 're_translation',
                'name': '重新翻译',
                'description': '重新翻译黄色标记的单元格',
                'config': {
                    'rule_set': 'translation',
                    'processor': 'llm_qwen',
                    'target_langs': ['EN', 'JP'],
                    'extract_context': True,
                    'max_workers': 10
                }
            }
        ]

        return {
            'templates': templates,
            'count': len(templates)
        }

    except Exception as e:
        logger.error(f"Failed to get config templates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get config templates: {str(e)}")


@router.get("/rules")
async def get_rules():
    """Get all available rules configuration."""
    try:
        rules_config_path = Path(__file__).parent.parent / 'config' / 'rules.yaml'

        if not rules_config_path.exists():
            return {'rules': {}, 'rule_sets': {}}

        with open(rules_config_path, 'r', encoding='utf-8') as f:
            rules_data = yaml.safe_load(f) or {}

        return rules_data

    except Exception as e:
        logger.error(f"Failed to get rules: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get rules: {str(e)}")


@router.get("/rule_sets")
async def get_rule_sets():
    """Get all available rule sets."""
    try:
        rules_config_path = Path(__file__).parent.parent / 'config' / 'rules.yaml'

        if not rules_config_path.exists():
            return {'rule_sets': {}}

        with open(rules_config_path, 'r', encoding='utf-8') as f:
            rules_data = yaml.safe_load(f) or {}

        return {'rule_sets': rules_data.get('rule_sets', {})}

    except Exception as e:
        logger.error(f"Failed to get rule sets: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get rule sets: {str(e)}")


@router.get("/processors")
async def get_processors():
    """Get all available processors configuration."""
    try:
        processors_config_path = Path(__file__).parent.parent / 'config' / 'processors.yaml'

        if not processors_config_path.exists():
            return {'processors': {}, 'processor_sets': {}}

        with open(processors_config_path, 'r', encoding='utf-8') as f:
            processors_data = yaml.safe_load(f) or {}

        return processors_data

    except Exception as e:
        logger.error(f"Failed to get processors: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get processors: {str(e)}")


@router.get("/processor_sets")
async def get_processor_sets():
    """Get all available processor sets."""
    try:
        processors_config_path = Path(__file__).parent.parent / 'config' / 'processors.yaml'

        if not processors_config_path.exists():
            return {'processor_sets': {}}

        with open(processors_config_path, 'r', encoding='utf-8') as f:
            processors_data = yaml.safe_load(f) or {}

        return {'processor_sets': processors_data.get('processor_sets', {})}

    except Exception as e:
        logger.error(f"Failed to get processor sets: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get processor sets: {str(e)}")
