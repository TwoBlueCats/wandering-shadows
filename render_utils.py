from __future__ import annotations

from typing import TYPE_CHECKING

import color
from config import Config

if TYPE_CHECKING:
    from tcod import Console
    from engine import Engine
    from game_map import GameMap


def get_names_at_location(x: int, y: int, game_map: GameMap) -> str:
    x, y = game_map.get_location_abs(x, y)
    if not game_map.in_bounds(x, y) or not game_map.visible[x, y]:
        return ""

    names = ", ".join(
        entity.name for entity in game_map.entities if entity.x == x and entity.y == y
    )

    return names.capitalize()


def render_bar(
        console: Console,
        current_value: int, maximum_value: int,
        bg: tuple[int, int, int], fg: tuple[int, int, int],
        x: int, y: int, total_width: int,
        text: str,
) -> None:
    bar_width = min(total_width, int(float(current_value) / maximum_value * total_width))

    console.draw_rect(x=x, y=y, width=total_width, height=1, ch=1, bg=bg)

    if bar_width > 0:
        console.draw_rect(
            x=x, y=y, width=bar_width, height=1, ch=1, bg=fg
        )

    console.print(
        x=x + 1, y=y, string=text, fg=color.bar_text
    )


def render_dungeon_level(
        console: Console, dungeon_level: int, location: tuple[int, int]
) -> None:
    """
    Render the level the player is currently on, at the given location.
    """
    console.print(*location, string=f"Dungeon level: {dungeon_level}")


def render_names_at_mouse_location(
        console: Console, x: int, y: int, engine: Engine
) -> None:
    mouse_x, mouse_y = engine.mouse_location

    names_at_mouse_location = get_names_at_location(
        x=mouse_x, y=mouse_y, game_map=engine.game_map
    )

    console.print(x=x, y=y, string=names_at_mouse_location)


def get_render_x_pos(engine: Engine) -> int:
    if engine.player.x <= Config.overlay_border:
        return Config.overlay_right_x
    else:
        return Config.overlay_left_x


def render_items_list(console: Console, items, equipment, x, y):
    for i, item in enumerate(items):
        item_key = chr(ord("a") + i)
        is_equipped = equipment.item_is_equipped(item)

        item_string = f"({item_key}) {item.name}"

        if is_equipped:
            item_string = f"{item_string} (E)"

        console.print(x + 1, y + i + 1, item_string)
