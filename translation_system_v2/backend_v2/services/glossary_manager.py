"""Glossary manager for game terminology."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class GlossaryManager:
    """Manage game glossaries for translation consistency."""

    def __init__(self):
        """Initialize glossary manager."""
        self.glossaries_dir = Path(__file__).parent.parent / 'data' / 'glossaries'
        self.glossaries_dir.mkdir(parents=True, exist_ok=True)
        self.cache = {}  # Memory cache for loaded glossaries
        self.logger = logging.getLogger(self.__class__.__name__)

    def load_glossary(self, glossary_id: str) -> Optional[Dict]:
        """
        Load glossary by ID.

        Args:
            glossary_id: Glossary identifier

        Returns:
            Glossary dictionary or None if not found
        """
        # Check cache first
        if glossary_id in self.cache:
            return self.cache[glossary_id]

        # Load from file
        file_path = self.glossaries_dir / f"{glossary_id}.json"

        if not file_path.exists():
            self.logger.warning(f"Glossary not found: {glossary_id}")
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                glossary = json.load(f)

            # Cache it
            self.cache[glossary_id] = glossary
            self.logger.info(f"Loaded glossary: {glossary_id} ({len(glossary.get('terms', []))} terms)")
            return glossary

        except Exception as e:
            self.logger.error(f"Failed to load glossary {glossary_id}: {e}")
            return None

    def match_terms_in_text(
        self,
        source_text: str,
        glossary: Dict,
        target_lang: str
    ) -> List[Dict[str, Any]]:
        """
        Match terms that appear in the source text.

        Args:
            source_text: Text to analyze
            glossary: Glossary dictionary
            target_lang: Target language code

        Returns:
            List of matched terms with translations
        """
        if not glossary or not glossary.get('terms'):
            return []

        matched_terms = []
        terms = glossary.get('terms', [])

        # Sort by length (longer terms first to avoid partial matches)
        sorted_terms = sorted(terms, key=lambda t: len(t.get('source', '')), reverse=True)

        matched_positions = set()

        for term in sorted_terms:
            source = term.get('source', '')
            if not source:
                continue

            # Find all occurrences
            pos = source_text.find(source)
            while pos != -1:
                # Check if position already matched
                term_range = set(range(pos, pos + len(source)))
                if not term_range.intersection(matched_positions):
                    # Get translation for target language
                    translation = term.get('translations', {}).get(target_lang)

                    if translation:
                        matched_terms.append({
                            'source': source,
                            'target': translation,
                            'priority': term.get('priority', 5),
                            'category': term.get('category', '')
                        })
                        matched_positions.update(term_range)

                # Find next occurrence
                pos = source_text.find(source, pos + 1)

        # Sort by priority (high priority first)
        matched_terms.sort(key=lambda x: x['priority'], reverse=True)

        return matched_terms

    def match_terms_in_batch(
        self,
        texts: List[str],
        glossary: Dict,
        target_lang: str
    ) -> List[Dict[str, Any]]:
        """
        Match terms across multiple texts (for batch translation).

        Args:
            texts: List of texts to analyze
            glossary: Glossary dictionary
            target_lang: Target language code

        Returns:
            Unified list of matched terms (no duplicates)
        """
        all_matched = {}  # Use dict to deduplicate

        for text in texts:
            matched = self.match_terms_in_text(text, glossary, target_lang)
            for term in matched:
                key = term['source']
                if key not in all_matched:
                    all_matched[key] = term

        # Convert to list and sort by priority
        result = list(all_matched.values())
        result.sort(key=lambda x: x['priority'], reverse=True)

        return result

    def format_glossary_for_prompt(self, matched_terms: List[Dict]) -> str:
        """
        Format matched terms for prompt injection.

        Args:
            matched_terms: List of matched terms

        Returns:
            Formatted string for prompt
        """
        if not matched_terms:
            return ""

        lines = ["相关游戏术语（请严格使用以下翻译）:"]

        for term in matched_terms:
            lines.append(f"- {term['source']} → {term['target']}")

        return "\n".join(lines)

    def list_available_glossaries(self) -> List[Dict[str, Any]]:
        """
        List all available glossaries.

        Returns:
            List of glossary metadata
        """
        glossaries = []

        for file_path in self.glossaries_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    glossary = json.load(f)

                glossaries.append({
                    'id': glossary.get('id', file_path.stem),
                    'name': glossary.get('name', file_path.stem),
                    'description': glossary.get('description', ''),
                    'version': glossary.get('version', '1.0'),
                    'term_count': len(glossary.get('terms', [])),
                    'languages': glossary.get('languages', [])
                })

            except Exception as e:
                self.logger.warning(f"Failed to load glossary metadata from {file_path}: {e}")

        return glossaries

    def save_glossary(self, glossary_id: str, glossary_data: Dict) -> bool:
        """
        Save glossary to file.

        Args:
            glossary_id: Glossary identifier
            glossary_data: Glossary data

        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = self.glossaries_dir / f"{glossary_id}.json"

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(glossary_data, f, ensure_ascii=False, indent=2)

            # Update cache
            self.cache[glossary_id] = glossary_data

            self.logger.info(f"Saved glossary: {glossary_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save glossary {glossary_id}: {e}")
            return False


# Global instance
glossary_manager = GlossaryManager()
