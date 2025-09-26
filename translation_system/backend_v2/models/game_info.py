"""Game information model definition."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class GameInfo:
    """Game background information for translation context."""

    game_type: str = ""           # RPG/FPS/MOBA/Strategy/Puzzle etc.
    world_view: str = ""          # Game world description
    target_regions: List[str] = field(default_factory=list)  # ["BR", "TH", "VN"]
    game_style: str = ""          # Realistic/Cartoon/Pixel/Anime etc.
    additional_context: str = ""  # Additional context information

    def to_context_string(self) -> str:
        """Convert game info to context string for LLM."""
        context_parts = []

        if self.game_type:
            context_parts.append(f"Game Type: {self.game_type}")

        if self.world_view:
            context_parts.append(f"World View: {self.world_view}")

        if self.target_regions:
            context_parts.append(f"Target Regions: {', '.join(self.target_regions)}")

        if self.game_style:
            context_parts.append(f"Game Style: {self.game_style}")

        if self.additional_context:
            context_parts.append(f"Additional Context: {self.additional_context}")

        return " | ".join(context_parts) if context_parts else ""

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'game_type': self.game_type,
            'world_view': self.world_view,
            'target_regions': self.target_regions,
            'game_style': self.game_style,
            'additional_context': self.additional_context
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'GameInfo':
        """Create from dictionary."""
        return cls(
            game_type=data.get('game_type', ''),
            world_view=data.get('world_view', ''),
            target_regions=data.get('target_regions', []),
            game_style=data.get('game_style', ''),
            additional_context=data.get('additional_context', '')
        )