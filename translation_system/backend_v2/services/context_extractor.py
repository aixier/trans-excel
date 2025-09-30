"""Context extraction service."""

import pandas as pd
from typing import Dict, Any, Optional, List
from models.excel_dataframe import ExcelDataFrame
from models.game_info import GameInfo


class ContextExtractor:
    """Extract context information for translation tasks."""

    def __init__(self, game_info: GameInfo = None, context_options: Dict[str, bool] = None):
        """
        Initialize context extractor.

        Args:
            game_info: Game information
            context_options: Dict specifying which context types to extract:
                - 'game_info': Game context (default: True)
                - 'comments': Cell comments (default: True)
                - 'neighbors': Neighboring cells (default: True)
                - 'content_analysis': Content characteristics (default: True)
                - 'sheet_type': Sheet type inference (default: True)
                Note: Column header is always extracted (required for translation)
        """
        self.game_info = game_info

        # Default: all enabled
        default_options = {
            'game_info': True,
            'comments': True,
            'neighbors': True,
            'content_analysis': True,
            'sheet_type': True
        }

        self.context_options = {**default_options, **(context_options or {})}

    def extract_context(
        self,
        excel_df: ExcelDataFrame,
        sheet_name: str,
        row_idx: int,
        col_idx: int
    ) -> str:
        """Extract context for a specific cell."""
        context_parts = []

        # 1. Add game context if available and enabled
        if self.context_options.get('game_info', True) and self.game_info:
            game_context = self.game_info.to_context_string()
            if game_context:
                context_parts.append(f"[Game] {game_context}")

        # 2. Extract from cell comment (if enabled)
        if self.context_options.get('comments', True):
            comment = excel_df.get_cell_comment(sheet_name, row_idx, col_idx)
            if comment:
                context_parts.append(f"[Comment] {comment}")

        # 3. Extract from column header (ALWAYS - required for translation)
        df = excel_df.get_sheet(sheet_name)
        if df is not None and col_idx < len(df.columns):
            col_header = str(df.columns[col_idx])
            if col_header and not col_header.startswith('Unnamed'):
                context_parts.append(f"[Column] {col_header}")

        # 4. Extract from neighboring cells (if enabled)
        if self.context_options.get('neighbors', True):
            neighbor_context = self._extract_neighbor_context(excel_df, sheet_name, row_idx, col_idx)
            if neighbor_context:
                context_parts.append(neighbor_context)

        # 5. Infer from content characteristics (if enabled)
        if self.context_options.get('content_analysis', True):
            value = excel_df.get_cell_value(sheet_name, row_idx, col_idx)
            if value and isinstance(value, str):
                content_context = self._infer_content_context(value)
                if content_context:
                    context_parts.append(content_context)

        # 6. Add sheet context (if enabled)
        if self.context_options.get('sheet_type', True):
            sheet_context = self._get_sheet_context(sheet_name)
            if sheet_context:
                context_parts.append(sheet_context)

        return " | ".join(context_parts) if context_parts else ""

    def _extract_neighbor_context(
        self,
        excel_df: ExcelDataFrame,
        sheet_name: str,
        row_idx: int,
        col_idx: int
    ) -> str:
        """Extract context from neighboring cells."""
        df = excel_df.get_sheet(sheet_name)
        if df is None:
            return ""

        context_parts = []

        # Check if previous row is a header/category
        if row_idx > 0:
            prev_cell = df.iloc[row_idx - 1, col_idx] if row_idx - 1 < len(df) else None
            if prev_cell and isinstance(prev_cell, str):
                # Check if it looks like a header
                if prev_cell.isupper() or prev_cell.endswith(':') or len(prev_cell) < 20:
                    context_parts.append(f"[Category] {prev_cell}")

        # Check first cell in row (often contains context)
        if col_idx > 0:
            first_cell = df.iloc[row_idx, 0]
            if first_cell and isinstance(first_cell, str) and len(first_cell) < 50:
                context_parts.append(f"[Row Label] {first_cell}")

        return " | ".join(context_parts)

    def _infer_content_context(self, value: str) -> str:
        """Infer context from content characteristics."""
        context_parts = []

        # Length-based inference
        if len(value) <= 10:
            context_parts.append("[Type] Short text/UI element")
        elif len(value) <= 30:
            context_parts.append("[Type] Medium text/Menu item")
        elif len(value) <= 100:
            context_parts.append("[Type] Description text")
        else:
            context_parts.append("[Type] Long text/Dialog")

        # Content-based inference
        if value.endswith('?'):
            context_parts.append("[Format] Question")
        elif value.endswith('!'):
            context_parts.append("[Format] Exclamation")
        elif '\\n' in value:
            context_parts.append("[Format] Multi-line text")

        # Special markers
        if '{' in value and '}' in value:
            context_parts.append("[Format] Contains variables")
        if '%' in value:
            context_parts.append("[Format] Contains percentage")
        if any(char.isdigit() for char in value):
            context_parts.append("[Format] Contains numbers")

        return " | ".join(context_parts)

    def _get_sheet_context(self, sheet_name: str) -> str:
        """Get context based on sheet name."""
        sheet_lower = sheet_name.lower()

        if 'ui' in sheet_lower or 'interface' in sheet_lower:
            return "[Sheet Type] UI/Interface text"
        elif 'dialog' in sheet_lower or 'dialogue' in sheet_lower:
            return "[Sheet Type] Dialog/Conversation"
        elif 'item' in sheet_lower:
            return "[Sheet Type] Item descriptions"
        elif 'skill' in sheet_lower or 'ability' in sheet_lower:
            return "[Sheet Type] Skills/Abilities"
        elif 'npc' in sheet_lower:
            return "[Sheet Type] NPC related"
        elif 'quest' in sheet_lower or 'mission' in sheet_lower:
            return "[Sheet Type] Quest/Mission text"
        elif 'tutorial' in sheet_lower or 'help' in sheet_lower:
            return "[Sheet Type] Tutorial/Help text"

        return ""

    def extract_batch_context(
        self,
        excel_df: ExcelDataFrame,
        tasks: List[Dict[str, Any]]
    ) -> str:
        """Extract shared context for a batch of tasks."""
        if not tasks:
            return ""

        # Find common patterns
        sheets = list(set(t['sheet_name'] for t in tasks))
        langs = list(set(t['target_lang'] for t in tasks))

        context_parts = []

        # Game context
        if self.game_info:
            context_parts.append(self.game_info.to_context_string())

        # Sheet context
        if len(sheets) == 1:
            context_parts.append(f"All from sheet: {sheets[0]}")

        # Language context
        if len(langs) == 1:
            context_parts.append(f"Target language: {langs[0]}")

        return " | ".join(context_parts)