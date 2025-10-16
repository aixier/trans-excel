"""Excel DataFrame model definition - Unified DataFrame Pipeline Architecture.

核心设计：
- DataFrame Pipeline: 所有数据状态都是相同格式的 DataFrame
- 单一数据源: 数据和元数据都在 DataFrame 中
- 格式一致性: 输入输出格式完全一致，支持无限级联

DataFrame 列结构约定：
- 数据列: 直接使用 Excel 列名 (如 'CH', 'EN', 'TH')
- 颜色列: 'color_' + 列名 (如 'color_CH', 'color_EN')
- 注释列: 'comment_' + 列名 (如 'comment_CH', 'comment_EN')
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import pandas as pd
import pickle


@dataclass
class ExcelDataFrame:
    """
    ExcelDataFrame: DataFrame Pipeline 的数据容器

    核心理念：
    - sheets 中的每个 DataFrame 包含所有信息（数据+元数据）
    - 不再使用单独的字典存储颜色和注释
    - 格式一致，支持级联处理

    DataFrame 列命名约定：
    - 数据列: Excel原始列名 (key, CH, EN, ...)
    - 颜色列: color_CH, color_EN, color_TH, ...
    - 注释列: comment_CH, comment_EN, comment_TH, ...
    """

    # ✅ 核心数据：Dict[sheet_name, DataFrame]
    sheets: Dict[str, pd.DataFrame] = field(default_factory=dict)

    # ✅ 文件元数据
    filename: str = ""
    excel_id: str = ""

    def add_sheet(self, sheet_name: str, df: pd.DataFrame) -> None:
        """
        添加一个 sheet 到 Excel 结构。

        Args:
            sheet_name: Sheet名称
            df: DataFrame（必须包含数据列和元数据列）
        """
        self.sheets[sheet_name] = df

    def get_sheet(self, sheet_name: str) -> Optional[pd.DataFrame]:
        """获取指定 sheet 的 DataFrame"""
        return self.sheets.get(sheet_name)

    def get_sheet_names(self) -> List[str]:
        """获取所有 sheet 名称"""
        return list(self.sheets.keys())

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取 Excel 文件的统计信息

        Returns:
            统计信息字典
        """
        stats = {
            'filename': self.filename,
            'excel_id': self.excel_id,
            'sheet_count': len(self.sheets),
            'sheets': []
        }

        for sheet_name, df in self.sheets.items():
            # 识别数据列（不以 color_ 或 comment_ 开头）
            data_cols = [col for col in df.columns
                        if not col.startswith('color_') and not col.startswith('comment_')]

            # 识别颜色列
            color_cols = [col for col in df.columns if col.startswith('color_')]

            # 识别注释列
            comment_cols = [col for col in df.columns if col.startswith('comment_')]

            # 统计有颜色的单元格（颜色列中非空的数量）
            colored_cells = 0
            for col in color_cols:
                colored_cells += df[col].notna().sum()

            # 统计有注释的单元格（注释列中非空的数量）
            cells_with_comments = 0
            for col in comment_cols:
                cells_with_comments += df[col].notna().sum()

            # 统计非空数据单元格
            non_empty = 0
            for col in data_cols:
                non_empty += df[col].notna().sum()

            sheet_stats = {
                'name': sheet_name,
                'rows': int(len(df)),
                'data_columns': len(data_cols),
                'color_columns': len(color_cols),
                'comment_columns': len(comment_cols),
                'cells': int(len(df) * len(data_cols)),
                'non_empty_cells': int(non_empty),
                'colored_cells': int(colored_cells),
                'cells_with_comments': int(cells_with_comments)
            }
            stats['sheets'].append(sheet_stats)

        stats['total_rows'] = int(sum(s['rows'] for s in stats['sheets']))
        stats['total_data_columns'] = int(max((s['data_columns'] for s in stats['sheets']), default=0))
        stats['total_cells'] = int(sum(s['cells'] for s in stats['sheets']))
        stats['total_non_empty'] = int(sum(s['non_empty_cells'] for s in stats['sheets']))

        return stats

    def clone(self) -> 'ExcelDataFrame':
        """
        创建 ExcelDataFrame 的深拷贝

        Returns:
            新的 ExcelDataFrame 实例
        """
        new_excel = ExcelDataFrame()
        new_excel.filename = self.filename
        new_excel.excel_id = self.excel_id

        # 深拷贝每个 sheet 的 DataFrame
        for sheet_name, df in self.sheets.items():
            new_excel.add_sheet(sheet_name, df.copy())

        return new_excel

    def save_to_pickle(self, file_path: str) -> None:
        """
        保存 ExcelDataFrame 到 pickle 文件

        Args:
            file_path: 保存路径
        """
        with open(file_path, 'wb') as f:
            pickle.dump(self, f, protocol=pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def load_from_pickle(file_path: str) -> 'ExcelDataFrame':
        """
        从 pickle 文件加载 ExcelDataFrame

        Args:
            file_path: 文件路径

        Returns:
            ExcelDataFrame 实例
        """
        with open(file_path, 'rb') as f:
            return pickle.load(f)

    def get_data_columns(self, sheet_name: str) -> List[str]:
        """
        获取指定 sheet 的数据列（不包括 color_ 和 comment_ 列）

        Args:
            sheet_name: Sheet名称

        Returns:
            数据列名列表
        """
        df = self.get_sheet(sheet_name)
        if df is None:
            return []

        return [col for col in df.columns
                if not col.startswith('color_') and not col.startswith('comment_')]

    def get_language_columns(self, sheet_name: str) -> List[str]:
        """
        获取指定 sheet 的语言列（通常是 CH, EN, TH 等，排除 key 列）

        Args:
            sheet_name: Sheet名称

        Returns:
            语言列名列表
        """
        data_cols = self.get_data_columns(sheet_name)
        # 排除 key 列
        return [col for col in data_cols if col.lower() != 'key']
