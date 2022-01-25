from functools import total_ordering
from enum import Enum, IntFlag, auto


class EquipmentType(IntFlag):
    WEAPON = auto()
    ARMOR = auto()
    HELMET = auto()
    SHIELD = auto()
    NECKLACE = auto()

    def get_types(self) -> list[str]:
        return list(value.name for value in self)


@total_ordering
class ConsumableTarget(IntFlag):
    SELF = auto()
    RANDOM = auto()
    NEAREST = auto()
    ALL = auto()
    SELECTED = auto()
    RANGED = auto()

    def __gt__(self, other: "ConsumableTarget") -> bool:
        return self.value > other.value


class ConsumableType(IntFlag):
    NONE = auto()
    POTION = auto()
    SCROLL = auto()
    BOOK = auto()
