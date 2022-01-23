from __future__ import annotations

from typing import TYPE_CHECKING

from components.base_component import BaseComponent
from components_types import EquipmentType
from ranged_value import Range

if TYPE_CHECKING:
    from entity import Item


class Equippable(BaseComponent):
    _bonuses = ["power", "defense"]
    parent: Item

    def __init__(
            self,
            equipment_type: EquipmentType,
            power_bonus: Range = None,
            defense_bonus: Range = None,
    ):
        self.equipment_type = equipment_type

        self.power_bonus = power_bonus or Range(0)
        self.defense_bonus = defense_bonus or Range(0)

    def bonuses(self) -> list[tuple[str, int]]:
        return [(name, getattr(self, f"{name}_bonus")) for name in self._bonuses]

    def description(self) -> list[str]:
        data = []
        for (name, value) in self.bonuses():
            data.append(f"{name.title()} bonus: {value}")
        return data


class Weapon(Equippable):
    def __init__(self, power_bonus: Range = None) -> None:
        super().__init__(equipment_type=EquipmentType.WEAPON, power_bonus=power_bonus)


class Armor(Equippable):
    def __init__(self, defense_bonus: Range = 0) -> None:
        super().__init__(equipment_type=EquipmentType.ARMOR, defense_bonus=defense_bonus)
