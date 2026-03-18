#!/usr/bin/env python3
"""Generate demo GIF for sv01 with smart pathfinding."""

import sys

sys.path.insert(0, ".")

from arc_agi import Arcade, OperationMode
from arcengine import GameAction
from PIL import Image
import numpy as np

COLOR_MAP = {
    0: (0, 0, 0),
    2: (255, 0, 0),
    3: (0, 255, 0),
    4: (255, 255, 0),
    6: (0, 255, 255),
    7: (0, 0, 255),
    9: (0, 128, 255),
}


def colorize(frame):
    h, w = frame.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    for color_idx, rgb_val in COLOR_MAP.items():
        mask = frame == color_idx
        rgb[mask] = rgb_val
    return rgb


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def is_in_warm_zone(x, y, warm_zones):
    return any(s.x == x and s.y == y for s in warm_zones)


def find_nearest(x, y, items):
    nearest = None
    nearest_dist = float("inf")
    for item in items:
        d = manhattan((x, y), (item.x, item.y))
        if d < nearest_dist:
            nearest_dist = d
            nearest = item
    return nearest, nearest_dist


def get_move_toward(target_x, target_y, player_x, player_y):
    dx = target_x - player_x
    dy = target_y - player_y

    if dy < 0:
        return GameAction.ACTION1
    elif dy > 0:
        return GameAction.ACTION2
    elif dx < 0:
        return GameAction.ACTION3
    elif dx > 0:
        return GameAction.ACTION4
    return GameAction.ACTION1


def smart_policy(env):
    game = env._game
    player_x = game._player.x
    player_y = game._player.y
    hunger = game._hunger
    warmth = game._warmth

    food_list = list(game._foods) if game._foods else []
    warm_zones = [s for s in game.current_level._sprites if s and "warm_zone" in s.tags]

    in_warm = is_in_warm_zone(player_x, player_y, warm_zones)

    nearest_food, food_dist = (
        find_nearest(player_x, player_y, food_list)
        if food_list
        else (None, float("inf"))
    )
    nearest_warm, warm_dist = find_nearest(player_x, player_y, warm_zones)

    critical_hunger = hunger < 30
    critical_warmth = warmth < 30 and not in_warm
    low_hunger = hunger < 50
    low_warmth = warmth < 50 and not in_warm

    target = None

    if critical_hunger and nearest_food:
        target = nearest_food
    elif critical_warmth and nearest_warm:
        target = nearest_warm
    elif low_hunger and nearest_food and food_dist <= warm_dist + 3:
        target = nearest_food
    elif low_warmth and nearest_warm:
        target = nearest_warm
    elif nearest_food and food_dist <= 3:
        target = nearest_food
    elif not in_warm and nearest_warm:
        target = nearest_warm
    elif nearest_food:
        target = nearest_food

    if target:
        return get_move_toward(target.x, target.y, player_x, player_y)

    if not in_warm and nearest_warm:
        return get_move_toward(nearest_warm.x, nearest_warm.y, player_x, player_y)

    return GameAction.ACTION1


def create_gif(game_id, output_path, max_steps_per_level=65):
    arc = Arcade(
        environments_dir="environment_files", operation_mode=OperationMode.OFFLINE
    )
    env = arc.make(game_id, seed=0, include_frame_data=True)

    frames = []
    total_steps = 0

    for level_num in range(5):
        for _ in range(max_steps_per_level):
            action = smart_policy(env)
            result = env.step(action)

            if result.frame:
                frame = result.frame[0]
                rgb = colorize(frame)
                img = Image.fromarray(rgb, "RGB")
                img = img.convert("P", palette=Image.ADAPTIVE, colors=256)
                frames.append(img)
                total_steps += 1

            if result.state.value in (1, 2):
                break

    if frames:
        frames[0].save(
            output_path,
            save_all=True,
            append_images=frames[1:],
            duration=150,
            loop=0,
            optimize=False,
        )
        print(
            f"GIF saved to {output_path} ({len(frames)} frames, {total_steps} total steps)"
        )


if __name__ == "__main__":
    create_gif("sv01-v1", "assets/sv01.gif")
