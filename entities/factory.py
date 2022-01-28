from typing import Callable

from components import consumable, equippable
from components.ai import HostileEnemy
from components.equipment import Equipment
from components.fighter import Fighter
from components.inventory import Inventory
from components.level import Level
from entity import Entity, Actor, Item


class Factory:
    def construct(self, floor: int) -> Entity:
        raise NotImplementedError()


class EnemyFactory(Factory):
    def __init__(self, char: str, color: tuple[int, int, int], name: str, fighter: Fighter, xp: int, base_floor: int,
                 fit_to_level: Callable = None, fix_dungeon_level: bool = True):
        self.char = char
        self.color = color
        self.name = name
        self.fighter = fighter
        self.xp = xp
        self.base_level = base_floor
        self.fit_to_level = fit_to_level
        self.fix_level = fix_dungeon_level

    def construct(self, floor: int) -> Actor:
        enemy = Actor(
            char=self.char,
            color=self.color,
            name=self.name,
            ai_cls=HostileEnemy,
            equipment=Equipment(),
            fighter=self.fighter.copy(),
            inventory=Inventory(capacity=0),
            level=Level(xp_given=self.xp),
            dungeon_level=floor,
        )
        if self.fit_to_level and floor > self.base_level:
            self.fit_to_level(enemy, floor, self.base_level)
        if self.fix_level:
            enemy.level.current_level = floor
        return enemy


class ItemFactory(Factory):
    def __init__(self, char: str, color: tuple[int, int, int], name: str,
                 consume: consumable.Consumable = None,
                 equip: equippable.Equippable = None,
                 base_floor: int = 0,
                 fit_to_level: Callable = None):
        self.char = char
        self.color = color
        self.name = name
        self.consume = consume
        self.equip = equip
        self.base_level = base_floor
        self.fit_to_level = fit_to_level

    def construct(self, floor: int) -> Item:
        item = Item(
            char=self.char,
            color=self.color,
            name=self.name,
            consumable=self.consume.copy() if self.consume is not None else None,
            equippable=self.equip.copy() if self.equip is not None else None,
            dungeon_level=floor,
        )
        if self.fit_to_level and floor > self.base_level:
            self.fit_to_level(item, floor, self.base_level)
        return item
