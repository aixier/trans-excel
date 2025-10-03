"""Analysis result model."""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class AnalysisResult:
    """Comprehensive Excel analysis result."""

    # File information
    file_info: Dict[str, Any] = field(default_factory=dict)

    # Language detection results
    language_detection: Dict[str, Any] = field(default_factory=dict)

    # Statistics
    statistics: Dict[str, Any] = field(default_factory=dict)

    # Format analysis (colors, comments, etc.)
    format_analysis: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'file_info': self.file_info,
            'language_detection': self.language_detection,
            'statistics': self.statistics,
            'format_analysis': self.format_analysis
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisResult':
        """Create AnalysisResult from dictionary."""
        return cls(
            file_info=data.get('file_info', {}),
            language_detection=data.get('language_detection', {}),
            statistics=data.get('statistics', {}),
            format_analysis=data.get('format_analysis', {})
        )
