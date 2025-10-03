"""Color detection with configurable ranges for Excel cells."""

import yaml
from pathlib import Path
from typing import Dict, List, Optional


class ColorDetector:
    """Advanced color detector with configurable ranges."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize color detector with config."""
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'config' / 'color_config.yaml'

        self.config = self._load_config(config_path)

    def _load_config(self, config_path) -> Dict:
        """Load color configuration from YAML."""
        try:
            if Path(config_path).exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Failed to load color config: {e}")

        # Return fallback config
        return {
            'fallback': {
                'yellow': {'r_min': 200, 'g_min': 200, 'b_max': 100},
                'blue': {'r_max': 100, 'g_min': 150, 'b_min': 200}
            }
        }

    def is_yellow_color(self, color_hex: str) -> bool:
        """
        Check if a color is in the yellow range.

        Supports:
        1. Pattern matching (e.g., contains "FFFF")
        2. Exact hex matching
        3. RGB range matching
        """
        if not color_hex or not color_hex.startswith('#'):
            return False

        try:
            # Remove # and parse
            hex_clean = color_hex.lstrip('#')

            # Handle ARGB format
            if len(hex_clean) == 8:
                hex_clean = hex_clean[2:]  # Skip alpha
            elif len(hex_clean) != 6:
                return False

            # Check configured yellow ranges
            if 'yellow_colors' in self.config:
                for yellow_config in self.config['yellow_colors']:
                    # Pattern matching
                    if 'pattern' in yellow_config:
                        if yellow_config['pattern'].upper() in hex_clean.upper():
                            return True

                    # Exact hex matching
                    if 'hex_values' in yellow_config:
                        if hex_clean.upper() in [h.upper() for h in yellow_config['hex_values']]:
                            return True

                    # RGB range matching
                    if 'rgb_range' in yellow_config:
                        r = int(hex_clean[0:2], 16)
                        g = int(hex_clean[2:4], 16)
                        b = int(hex_clean[4:6], 16)

                        rgb_range = yellow_config['rgb_range']
                        r_min, r_max = rgb_range.get('r', [0, 255])
                        g_min, g_max = rgb_range.get('g', [0, 255])
                        b_min, b_max = rgb_range.get('b', [0, 255])

                        if (r_min <= r <= r_max and
                            g_min <= g <= g_max and
                            b_min <= b <= b_max):
                            return True

            # Fallback to simple detection
            if 'fallback' in self.config and 'yellow' in self.config['fallback']:
                r = int(hex_clean[0:2], 16)
                g = int(hex_clean[2:4], 16)
                b = int(hex_clean[4:6], 16)

                fallback = self.config['fallback']['yellow']
                if (r >= fallback.get('r_min', 200) and
                    g >= fallback.get('g_min', 200) and
                    b <= fallback.get('b_max', 100)):
                    return True

            return False

        except (ValueError, IndexError):
            return False

    def is_blue_color(self, color_hex: str) -> bool:
        """
        Check if a color is in the blue range.

        Supports:
        1. Pattern matching (e.g., contains "0000FF")
        2. Exact hex matching
        3. RGB range matching
        """
        if not color_hex or not color_hex.startswith('#'):
            return False

        try:
            # Remove # and parse
            hex_clean = color_hex.lstrip('#')

            # Handle ARGB format
            if len(hex_clean) == 8:
                hex_clean = hex_clean[2:]  # Skip alpha
            elif len(hex_clean) != 6:
                return False

            # Check configured blue ranges
            if 'blue_colors' in self.config:
                for blue_config in self.config['blue_colors']:
                    # Pattern matching
                    if 'pattern' in blue_config:
                        if blue_config['pattern'].upper() in hex_clean.upper():
                            return True

                    # Exact hex matching
                    if 'hex_values' in blue_config:
                        if hex_clean.upper() in [h.upper() for h in blue_config['hex_values']]:
                            return True

                    # RGB range matching
                    if 'rgb_range' in blue_config:
                        r = int(hex_clean[0:2], 16)
                        g = int(hex_clean[2:4], 16)
                        b = int(hex_clean[4:6], 16)

                        rgb_range = blue_config['rgb_range']
                        r_min, r_max = rgb_range.get('r', [0, 255])
                        g_min, g_max = rgb_range.get('g', [0, 255])
                        b_min, b_max = rgb_range.get('b', [0, 255])

                        if (r_min <= r <= r_max and
                            g_min <= g <= g_max and
                            b_min <= b <= b_max):
                            return True

            # Fallback to simple detection
            if 'fallback' in self.config and 'blue' in self.config['fallback']:
                r = int(hex_clean[0:2], 16)
                g = int(hex_clean[2:4], 16)
                b = int(hex_clean[4:6], 16)

                fallback = self.config['fallback']['blue']
                if (r <= fallback.get('r_max', 100) and
                    g >= fallback.get('g_min', 150) and
                    b >= fallback.get('b_min', 200)):
                    return True

            return False

        except (ValueError, IndexError):
            return False


# Global detector instance
_detector = None


def get_detector() -> ColorDetector:
    """Get global color detector instance."""
    global _detector
    if _detector is None:
        _detector = ColorDetector()
    return _detector


def is_yellow_color(color_hex: str) -> bool:
    """Check if color is yellow (convenience function)."""
    return get_detector().is_yellow_color(color_hex)


def is_blue_color(color_hex: str) -> bool:
    """Check if color is blue (convenience function)."""
    return get_detector().is_blue_color(color_hex)


def get_color_type(color_hex: str) -> str:
    """
    Determine the color type (yellow, blue, or other).

    Returns:
        'yellow', 'blue', or 'other'
    """
    if is_yellow_color(color_hex):
        return 'yellow'
    elif is_blue_color(color_hex):
        return 'blue'
    else:
        return 'other'
