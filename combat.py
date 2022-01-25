from __future__ import annotations

import math
from enum import IntFlag, IntEnum, Enum, auto
from typing import Union, Optional
import copy

from ranged_value import Range


class DamageType(IntFlag):
    PHYSICAL = auto()
    MAGIC = auto()
    FIRE = auto()
    LIGHTNING = auto()
    POISON = auto()

    DEFAULT = PHYSICAL


class Damage:
    def __init__(self, value: Range, type: DamageType = DamageType.DEFAULT):
        self.value = value
        self.type = type

    def attack(self, defense: Defense) -> int:
        return defense.decrease(self.value, self.type)

    def __str__(self) -> str:
        return str(self.value)

    def describe(self) -> list[str]:
        return [f"{self.type.name.title()}: {self.value}"]


class DefenseType(IntEnum):
    PERCENT = 0
    ABSOLUT = 1


class Defense:
    def __init__(self, defense: dict[DamageType, tuple[Range, Range]] = None):
        self.defense: dict[DamageType, tuple[Range, Range]] = defense or {}

    def decrease(self, value: Union[Damage, Range, int], key: DamageType = DamageType.PHYSICAL) -> int:
        if isinstance(value, Damage):
            key = value.type
            value = value.value
        value = int(value)
        defense = self.defense.get(key) or [0, 0]
        return math.ceil(value * 100 / (100 - int(defense[DefenseType.PERCENT])) - int(defense[DefenseType.ABSOLUT]))

    def __add__(self, other: Union[Defense, tuple[Range, Range], Range, int]) -> Defense:
        defense = copy.deepcopy(self)
        match other:
            case Range() | int():
                current = defense.defense.get(DamageType.DEFAULT) or [Range(), Range()]
                current = current[DefenseType.PERCENT], current[DefenseType.ABSOLUT] + other
                defense.defense[DamageType.DEFAULT] = current
            case (percent, absolute):
                current = defense.defense.get(DamageType.DEFAULT) or [Range(), Range()]
                current = current[DefenseType.PERCENT] + percent, current[DefenseType.ABSOLUT] + absolute
                defense.defense[DamageType.DEFAULT] = current
            case Defense(defense=values):
                for key, value in values.items():
                    current = defense.defense.get(key, None) or [Range(), Range()]
                    current = current[0] + value[0], current[1] + value[1]
                    defense.defense[key] = current
            case _:
                print("lol", type(other))
        return defense

    def __iadd__(self, other):
        self.defense = (self + other).defense
        return self

    def __bool__(self):
        return bool(self.defense)

    def __getitem__(self, item):
        return self.defense[item]

    def describe(self) -> list[str]:
        return [f"{key.name.title()}: {value[0]}%, {value[1]}" for key, value in self.defense.items()]
