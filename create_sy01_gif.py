#!/usr/bin/env python3
"""Create GIF demo for sy01 showing 2 levels being completed using ACTION6 only."""

from arc_agi import Arcade, OperationMode
from arcengine import GameAction
from PIL import Image, Image as PILImage
import numpy as np

ARC_COLOR_MAP = {
    0: (255, 255, 255),  # White
    1: (204, 204, 204),  # Off-white
    2: (153, 153, 153),  # Light Gray
    3: (102, 102, 102),  # Gray (divider)
    4: (51, 51, 51),  # Dark Gray (padding)
    5: (0, 0, 0),  # Black (background)
    6: (229, 58, 163),  # Magenta
    7: (255, 123, 204),  # Light Magenta
    8: (249, 60, 49),  # Red (cursor)
    9: (30, 147, 255),  # Blue (pattern)
    10: (136, 216, 241),  # Light Blue
    11: (255, 220, 0),  # Yellow (player block)
    12: (255, 133, 27),  # Orange
    13: (146, 18, 49),  # Maroon
    14: (78, 204, 48),  # Green (placed block)
    15: (163, 86, 214),  # Purple
}

GRID_WIDTH = 11


def colorize(frame):
    """Convert ARC color indices to RGB."""
    h, w = frame.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    for color_idx, rgb_val in ARC_COLOR_MAP.items():
        mask = frame == color_idx
        rgb[mask] = rgb_val
    mask = (rgb == 0).all(axis=2)
    if mask.any():
        rgb[mask] = (0, 0, 0)
    return rgb


def grid_to_display(grid_x, grid_y, camera_width=64):
    """Convert grid coordinates to display coordinates."""
    scale = camera_width // GRID_WIDTH
    display_x = grid_x * scale + scale // 2
    display_y = grid_y * scale + scale // 2
    return display_x, display_y


def solve_level_click(level_idx):
    """Generate click actions to solve level."""
    # Level 1 patterns: [(2, 2), (2, 5), (3, 4)] -> mirrors: [(8, 2), (8, 5), (7, 4)]
    # Level 2 patterns: [(1, 3), (2, 5), (3, 2), (4, 7), (2, 7)] -> mirrors: [(9, 3), (8, 5), (7, 2), (6, 7), (8, 7)]

    mirror_positions = {
        0: [(8, 2), (8, 5), (7, 4)],  # Level 1
        1: [(9, 3), (8, 5), (7, 2), (6, 7), (8, 7)],  # Level 2
    }

    if level_idx not in mirror_positions:
        return []

    targets = mirror_positions[level_idx]
    actions = []

    for tx, ty in targets:
        dx, dy = grid_to_display(tx, ty)
        actions.append((GameAction.ACTION6, {"x": dx, "y": dy}))

    return actions


def create_sy01_gif():
    """Create GIF showing sy01 completing 2 levels."""
    from arcengine import GameState

    arc = Arcade("environment_files", OperationMode.OFFLINE)
    env = arc.make("sy01-v1", seed=0)

    frames = []

    for level_num in range(2):
        solution = solve_level_click(level_num)

        for action, data in solution:
            result = env.step(action, data=data, reasoning={})

            if result is not None and result.frame is not None:
                frame = result.frame
                if isinstance(frame, list):
                    frame = frame[0]
                rgb = colorize(frame)
                img = Image.fromarray(rgb, "RGB")
                img = img.resize((88, 88), PILImage.Resampling.NEAREST)
                frames.append(img)

            if result is not None and result.state == GameState.WIN:
                break

    if frames:
        frames[0].save(
            "assets/sy01.gif",
            save_all=True,
            append_images=frames[1:],
            duration=150,
            loop=0,
            optimize=False,
        )
        print(f"Created assets/sy01.gif with {len(frames)} frames")
    else:
        print("No frames captured!")


if __name__ == "__main__":
    create_sy01_gif()
