from enum import IntFlag, auto


class EquipmentType(IntFlag):
    WEAPON = auto()
    ARMOR = auto()
    HELMET = auto()

    def get_types(self) -> list[str]:
        return list(value.name for value in self)
