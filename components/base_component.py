from __future__ import annotations

import copy
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity
    from game_map import GameMap

T = TypeVar("T", bound="BaseComponent")


class BaseComponent:
    parent: Entity  # Owning entity instance.

    @property
    def game_map(self) -> GameMap:
        return self.parent.game_map

    @property
    def engine(self) -> Engine:
        return self.game_map.engine

    def copy(self: T) -> T:
        return copy.deepcopy(self)
