"""Rule factory for creating rule instances from configuration."""

import yaml
import logging
from pathlib import Path
from typing import List, Dict, Any
from importlib import import_module

logger = logging.getLogger(__name__)


class RuleFactory:
    """Factory for creating rule instances from YAML configuration."""

    def __init__(self, config_path: str = None):
        """Initialize factory with configuration.

        Args:
            config_path: Path to rules.yaml (default: config/rules.yaml)
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / 'config' / 'rules.yaml'

        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load rules configuration from YAML.

        Returns:
            Configuration dictionary
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                logger.info(f"Loaded rules config from {self.config_path}")
                return config
        except Exception as e:
            logger.error(f"Failed to load rules config: {e}")
            return {'rules': {}, 'rule_sets': {}, 'default_rule_set': 'translation'}

    def create_rule(self, rule_name: str):
        """Create a single rule instance.

        Args:
            rule_name: Rule name (e.g., 'empty', 'yellow')

        Returns:
            Rule instance

        Raises:
            ValueError: If rule not found or disabled
        """
        if rule_name not in self.config['rules']:
            raise ValueError(f"Rule '{rule_name}' not found in configuration")

        rule_config = self.config['rules'][rule_name]

        if not rule_config.get('enabled', True):
            raise ValueError(f"Rule '{rule_name}' is disabled")

        # Import rule class
        class_path = rule_config['class']
        module_path, class_name = class_path.rsplit('.', 1)

        try:
            module = import_module(module_path)
            rule_class = getattr(module, class_name)

            # Create instance
            rule_instance = rule_class()
            logger.debug(f"Created rule: {rule_name} ({class_name})")

            return rule_instance

        except Exception as e:
            logger.error(f"Failed to create rule '{rule_name}': {e}")
            raise

    def create_rules(self, rule_names: List[str]) -> List:
        """Create multiple rule instances.

        Args:
            rule_names: List of rule names

        Returns:
            List of rule instances
        """
        rules = []
        for rule_name in rule_names:
            try:
                rule = self.create_rule(rule_name)
                rules.append(rule)
            except Exception as e:
                logger.warning(f"Skipping rule '{rule_name}': {e}")

        return rules

    def create_rule_set(self, set_name: str) -> List:
        """Create rules from a predefined set.

        Args:
            set_name: Rule set name (e.g., 'translation', 'caps_only')

        Returns:
            List of rule instances

        Raises:
            ValueError: If rule set not found
        """
        if set_name not in self.config['rule_sets']:
            raise ValueError(f"Rule set '{set_name}' not found")

        rule_names = self.config['rule_sets'][set_name]
        return self.create_rules(rule_names)

    def get_default_rules(self) -> List:
        """Get default rule set.

        Returns:
            List of rule instances from default set
        """
        default_set = self.config.get('default_rule_set', 'translation')
        return self.create_rule_set(default_set)

    def list_available_rules(self) -> List[Dict[str, Any]]:
        """List all available rules.

        Returns:
            List of rule information dictionaries
        """
        rules_info = []
        for rule_name, rule_config in self.config['rules'].items():
            rules_info.append({
                'name': rule_name,
                'description': rule_config.get('description', ''),
                'priority': rule_config.get('priority', 5),
                'enabled': rule_config.get('enabled', True),
                'requires_translation_first': rule_config.get('requires_translation_first', False)
            })

        return rules_info

    def list_rule_sets(self) -> Dict[str, List[str]]:
        """List all available rule sets.

        Returns:
            Dictionary of rule set names to rule lists
        """
        return self.config.get('rule_sets', {})


# Global instance
rule_factory = RuleFactory()
