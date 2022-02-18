from __future__ import annotations

import copy
import math
from itertools import chain
from typing import Optional, Type, TypeVar, TYPE_CHECKING, Union

import color
from config import Config
from render_order import RenderOrder
from components.params import ActorStats

if TYPE_CHECKING:
    from components.ai import BaseAI
    from components.consumable import Consumable
    from components.equipment import Equipment
    from components.equippable import Equippable
    from components.fighter import Fighter
    from components.inventory import Inventory
    from components.level import Level
    from components.effects import Effect
    from components.params import FighterParams
    from game_map import GameMap

T = TypeVar("T", bound="Entity")


class Entity:
    """
    A generic object to represent players, enemies, items, etc.
    """

    parent: Union[GameMap, Inventory]

    def __init__(
            self,
            parent: Optional[GameMap] = None,
            x: int = 0,
            y: int = 0,
            char: str = "?",
            color: tuple[int, int, int] = (255, 255, 255),
            name: str = "<Unnamed>",
            blocks_movement: bool = False,
            render_order: RenderOrder = RenderOrder.CORPSE,
            dungeon_level: int = -1,
    ):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks_movement = blocks_movement
        self.render_order = render_order
        if parent:
            # If parent isn't provided now then it will be set later.
            self.parent = parent
            parent.entities.add(self)
        self.dungeon_level = dungeon_level

    @property
    def position(self) -> tuple[int, int]:
        return self.x, self.y

    def move(self, dx: int, dy: int) -> None:
        # Move the entity by a given amount
        self.x += dx
        self.y += dy

    def distance(self, x: int, y: int) -> float:
        """
        Return the distance between the current entity and the given (x, y) coordinate.
        """
        return math.hypot(x - self.x, y - self.y)

    @property
    def game_map(self) -> GameMap:
        return self.parent.game_map

    def spawn(self: T, game_map: GameMap, x: int, y: int) -> T:
        """Spawn a copy of this instance at the given location."""
        clone = self.copy()
        clone.x = x
        clone.y = y
        clone.parent = game_map
        game_map.entities.add(clone)
        return clone

    def place(self, x: int, y: int, game_map: Optional[GameMap] = None) -> None:
        """Place this entity at a new location.  Handles moving across GameMaps."""
        self.x = x
        self.y = y
        if game_map:
            if hasattr(self, "parent"):  # Possibly uninitialized.
                if self.parent is self.game_map:
                    self.game_map.entities.remove(self)
            self.parent = game_map
            game_map.entities.add(self)

    def copy(self: T) -> T:
        return copy.deepcopy(self)

    def description(self) -> list[str]:
        raise NotImplementedError


class Actor(Entity):
    def __init__(
            self,
            *,
            x: int = 0,
            y: int = 0,
            char: str = "?",
            color: tuple[int, int, int] = (255, 255, 255),
            name: str = "<Unnamed>",
            ai_cls: Type[BaseAI],
            equipment: Equipment,
            fighter: Fighter,
            inventory: Inventory,
            level: Level,
            dungeon_level: int = -1,
            stats: Optional[ActorStats] = None
    ):
        super().__init__(
            x=x,
            y=y,
            char=char,
            color=color,
            name=name,
            blocks_movement=True,
            render_order=RenderOrder.ACTOR,
            dungeon_level=dungeon_level,
        )

        self.ai: Optional[BaseAI] = ai_cls(self)

        self.equipment: Equipment = equipment
        self.equipment.parent = self

        self.fighter = fighter
        self.fighter.parent = self

        self.inventory = inventory
        self.inventory.parent = self

        self.level = level
        self.level.parent = self

        self.effects: list[Effect] = []
        self.stats = stats or ActorStats()

    @property
    def is_alive(self) -> bool:
        """Returns True as long as this actor can perform actions."""
        return bool(self.ai)

    def description(self) -> list[str]:
        messages = [
            f"Name: {self.name}",
            f"Level: {self.level.current_level}",
        ]

        if self.is_alive:
            messages.append("")
            messages.extend(self.fighter.description())
            if self.effects:
                messages.append("")
                messages.append("Effects:")
                messages.extend(chain.from_iterable(effect.describe() for effect in self.effects))

        return messages

    def add_effect(self, effect: Effect):
        effect.parent = self
        self.effects.append(effect)

    def apply_effects(self):
        if not self.is_alive:
            return False

        was = len(self.effects) != 0
        for effect in self.effects:
            effect.apply(self, False)

        if self.parent.engine.turn - self.in_rest > self.params.mana_regen_turns:
            self.fighter.restore_mana(round(self.fighter.max_mp * self.params.mana_regen_percent / 100, 2))

        if self.parent.engine.turn - self.in_rest > self.params.energy_regen_turns:
            add = round(self.fighter.max_ep * self.params.energy_regen_percent / 100, 2)
            self.fighter.restore_energy(add)

        return was

    @property
    def in_rest(self) -> int:
        return max(self.fighter.energy_decrease_turn, self.fighter.mana_decrease_turn, self.fighter.hp_decrease_turn)

    @property
    def params(self) -> FighterParams:
        return self.stats.params


class Item(Entity):
    def __init__(
            self,
            *,
            x: int = 0,
            y: int = 0,
            char: str = "?",
            color: tuple[int, int, int] = (255, 255, 255),
            name: str = "<Unnamed>",
            consumable: Optional[Consumable] = None,
            equippable: Optional[Equippable] = None,
            dungeon_level: int = -1,
    ):
        super().__init__(
            x=x,
            y=y,
            char=char,
            color=color,
            name=name,
            blocks_movement=False,
            render_order=RenderOrder.ITEM,
            dungeon_level=dungeon_level,
        )

        self.consumable = consumable
        if self.consumable:
            self.consumable.parent = self

        self.equippable = equippable
        if self.equippable:
            self.equippable.parent = self

    def description(self) -> list[str]:
        messages = [
            f"Name: {self.name}",
            f"Dungeon level: {self.dungeon_level}",
        ]

        if self.equippable is not None:
            messages.append("")
            messages.extend(self.equippable.description())
        if self.consumable is not None:
            messages.append("")
            messages.extend(self.consumable.description())

        return messages


class Torch(Entity):
    def __init__(self, x=0, y=0, r=Config.fov_radius):
        super().__init__(x=x, y=y, char="!", color=color.red, name="Torch", render_order=RenderOrder.CORPSE)
        self.radius = r

    def description(self) -> list[str]:
        return ["Torch", f"Radius: {self.radius}"]
