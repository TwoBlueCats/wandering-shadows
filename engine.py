from __future__ import annotations

import lzma
import pickle
from typing import TYPE_CHECKING

from tcod.console import Console
from tcod.map import compute_fov

import color
from config import Config
import exceptions
from message_log import MessageLog
import render_utils

if TYPE_CHECKING:
    from entity import Actor
    from game_map import GameMap, GameWorld


class Engine:
    game_map: GameMap
    game_world: GameWorld

    def __init__(self, player: Actor):
        self.message_log = MessageLog()
        self.mouse_location = (0, 0)
        self.player = player

    def handle_enemy_turns(self) -> None:
        for entity in set(self.game_map.actors) - {self.player}:
            if entity.ai:
                try:
                    entity.ai.perform()
                except exceptions.Impossible:
                    pass

    def update_fov(self) -> None:
        """Recompute the visible area based on the players point of view."""
        self.game_map.visible[:] = compute_fov(
            self.game_map.tiles["transparent"],
            (self.player.x, self.player.y),
            radius=Config.fov_radius,
        )
        # If a tile is "visible" it should be added to "explored".
        self.game_map.explored |= self.game_map.visible

    def render(self, console: Console) -> None:
        self.game_map.render(console)

        self.message_log.render(
            console=console,
            x=Config.data_right_x,
            y=Config.data_location_y,
            width=Config.log_width,
            height=Config.log_height,
        )

        render_utils.render_bar(
            console=console,
            current_value=self.player.fighter.hp,
            maximum_value=self.player.fighter.max_hp,
            bg=color.hp_empty,
            fg=color.hp_filled,
            x=Config.data_left_x,
            y=Config.data_location_y,
            total_width=Config.bar_width,
            text=f"HP: {self.player.fighter.hp}/{self.player.fighter.max_hp}"
        )
        render_utils.render_bar(
            console=console,
            current_value=self.player.level.current_xp,
            maximum_value=self.player.level.experience_to_next_level,
            bg=color.xp_empty,
            fg=color.xp_filled,
            x=Config.data_left_x,
            y=Config.data_location_y + 1,
            total_width=Config.bar_width,
            text=f"XP: {self.player.level.current_xp}/{self.player.level.experience_to_next_level}"
        )

        render_utils.render_dungeon_level(
            console=console,
            dungeon_level=self.game_world.current_floor,
            location=(Config.data_left_x, Config.names_location_y),
        )
        render_utils.render_names_at_mouse_location(
            console=console,
            x=Config.data_right_x,
            y=Config.names_location_y,
            engine=self,
        )

    def save_as(self, filename: str) -> None:
        """Save this Engine instance as a compressed file."""
        save_data = lzma.compress(pickle.dumps(self))
        with open(filename, "wb") as f:
            f.write(save_data)
