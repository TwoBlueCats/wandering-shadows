from __future__ import annotations

from typing import Iterable, Iterator, Optional, TYPE_CHECKING

import numpy as np  # type: ignore
from tcod.console import Console

import color
from config import Config, MapConfig
from entity import Actor, Item
import tile_types

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity


class GameMap:
    def __init__(
            self, engine: Engine, width: int, height: int, entities: Iterable[Entity] = ()
    ):
        self.engine = engine
        self.width, self.height = width, height
        self.entities = set(entities)
        self.tiles = np.full((width, height), fill_value=tile_types.wall, order="F")

        self.visible = np.full((width, height), fill_value=False, order="F")
        self.explored = np.full((width, height), fill_value=False, order="F")

        self.tiles_rgb = np.select(
            condlist=[self.visible, self.explored],
            choicelist=[self.tiles["light"], self.tiles["dark"]],
            default=tile_types.DARKNESS
        )

        self.downstairs_location = (0, 0)

        self.block_top = 0
        self.block_left = 0

    def update_tiles_rgb(self):
        self.tiles_rgb = np.select(
            condlist=[self.visible, self.explored],
            choicelist=[self.tiles["light"], self.tiles["dark"]],
            default=tile_types.DARKNESS
        )

    def in_bounds(self, x: int, y: int) -> bool:
        """Return True if x and y are inside of the bounds of this map."""
        return 0 <= x < self.width and 0 <= y < self.height

    def shown(self, x: int, y: int) -> bool:
        width, height = Config.sample_map_width, Config.sample_map_height
        return self.block_left <= x < self.block_left + width and self.block_top <= y < self.block_top + height

    def update_block_locs(self):
        mm_clip = lambda v, l, u: max(l, min(u, v))

        width, height = Config.sample_map_width, Config.sample_map_height

        x, y = self.engine.player.position
        # in bound x-axis
        if not (self.block_left + width // 4 <= x < self.block_left + width // 4 * 3):
            left = x - width // 2
            self.block_left = mm_clip(left, 0, self.width - width)
        # in bound y-axis
        if not (self.block_top + height // 4 <= y < self.block_top + height // 4 * 3):
            top = y - height // 2
            self.block_top = mm_clip(top, 0, self.height - height)

    @property
    def game_map(self) -> GameMap:
        return self

    @property
    def actors(self) -> Iterator[Actor]:
        """Iterate over this map's living actors."""
        yield from (
            entity
            for entity in self.entities
            if isinstance(entity, Actor) and entity.is_alive
        )

    @property
    def items(self) -> Iterator[Item]:
        yield from (entity for entity in self.entities if isinstance(entity, Item))

    def get_blocking_entity_at_location(self, location_x: int, location_y: int) -> Optional[Entity]:
        for entity in self.entities:
            if entity.blocks_movement and entity.x == location_x and entity.y == location_y:
                return entity

        return None

    def get_actor_at_location_abs(self, x: int, y: int) -> Optional[Actor]:
        for actor in self.actors:
            if actor.x == x and actor.y == y:
                return actor
        return None

    def get_location_abs(self, x: int, y: int) -> tuple[int, int]:
        return x + self.block_left, y + self.block_top

    def get_actor_at_shown_location(self, x: int, y: int) -> Optional[Actor]:
        return self.get_actor_at_location_abs(*self.get_location_abs(x, y))

    def render(self, console: Console) -> None:
        """
        Renders the map.

        If a tile is in the "visible" array, then draw it with the "light" colors.
        If it isn't, but it's in the "explored" array, then draw it with the "dark" colors.
        Otherwise, the default is "DARKNESS".
        """
        self.update_block_locs()
        self.update_tiles_rgb()
        m_x, m_y = Config.sample_map_x, Config.sample_map_y
        width, height = Config.sample_map_width, Config.sample_map_height
        console.tiles_rgb[m_x:m_x + width, m_y:m_y + height] = self.tiles_rgb[
                                                               self.block_left:self.block_left + width,
                                                               self.block_top:self.block_top + height
                                                               ]

        if Config.DEBUG:
            console.draw_frame(x=m_x + width // 4, y=0, width=1, height=height, fg=color.red, clear=False)
            console.draw_frame(x=m_x + width // 4 * 3, y=0, width=1, height=height, fg=color.red, clear=False)
            console.draw_frame(x=0, y=m_y + height // 4, width=width, height=1, fg=color.red, clear=False)
            console.draw_frame(x=0, y=m_y + height // 4 * 3, width=width, height=1, fg=color.red, clear=False)

        entities_sorted_for_rendering = sorted(
            self.entities, key=lambda v: v.render_order.value
        )

        for entity in entities_sorted_for_rendering:
            if self.visible[entity.x, entity.y]:
                console.print(x=entity.x - self.block_left, y=entity.y - self.block_top, string=entity.char,
                              fg=entity.color)


class GameWorld:
    """
    Holds the settings for the GameMap, and generates new maps when moving down the stairs.
    """

    def __init__(
            self,
            *,
            engine: Engine,
            big_map: MapConfig,
            little_map: MapConfig,
            current_floor: int = 0
    ):
        self.engine = engine

        self.big_map = big_map
        self.little_map = little_map

        self.current_floor = current_floor

    def generate_floor(self) -> None:
        from procgen import generate_dungeon

        self.current_floor += 1

        if self.current_floor % Config.big_floor == 0:
            config = self.big_map
        else:
            config = self.little_map

        self.engine.game_map = generate_dungeon(
            max_rooms=config.max_rooms,
            room_min_size=config.room_min_size,
            room_max_size=config.room_max_size,
            map_width=config.width,
            map_height=config.height,
            engine=self.engine,
        )
