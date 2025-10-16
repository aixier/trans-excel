"""Color detection utilities for Excel cells."""

def is_yellow_color(color_hex: str) -> bool:
    """
    Check if a color is in the yellow range.
    Yellow colors typically have high R and G values, low B value.
    """
    if not color_hex or not color_hex.startswith('#'):
        return False

    try:
        # Remove # and parse RGB
        hex_clean = color_hex.lstrip('#')

        # Handle different hex formats (RGB, ARGB)
        if len(hex_clean) == 8:  # ARGB format
            hex_clean = hex_clean[2:]  # Skip alpha channel
        elif len(hex_clean) != 6:  # Not a valid RGB hex
            return False

        r = int(hex_clean[0:2], 16)
        g = int(hex_clean[2:4], 16)
        b = int(hex_clean[4:6], 16)

        # Yellow detection criteria:
        # - Red and Green should be high (> 180)
        # - Blue should be low (< 150)
        # - Red and Green should be close to each other
        is_yellow = (
            r > 180 and
            g > 180 and
            b < 150 and
            abs(r - g) < 60  # R and G should be similar
        )

        return is_yellow

    except (ValueError, IndexError):
        return False


def is_blue_color(color_hex: str) -> bool:
    """
    Check if a color is in the blue range.
    Blue colors typically have high B value, low R and G values.
    """
    if not color_hex or not color_hex.startswith('#'):
        return False

    try:
        # Remove # and parse RGB
        hex_clean = color_hex.lstrip('#')

        # Handle different hex formats (RGB, ARGB)
        if len(hex_clean) == 8:  # ARGB format
            hex_clean = hex_clean[2:]  # Skip alpha channel
        elif len(hex_clean) != 6:  # Not a valid RGB hex
            return False

        r = int(hex_clean[0:2], 16)
        g = int(hex_clean[2:4], 16)
        b = int(hex_clean[4:6], 16)

        # Blue detection criteria:
        # - Blue should be high (> 150)
        # - Red and Green should be relatively low (< 150)
        # - Blue should be notably higher than Red and Green
        is_blue = (
            b > 150 and
            r < 150 and
            g < 180 and  # Allow slightly higher green for cyan-ish blues
            b > r + 50 and
            b > g + 30
        )

        return is_blue

    except (ValueError, IndexError):
        return False


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