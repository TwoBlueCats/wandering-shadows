from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from components.base_component import BaseComponent
from components_types import EquipmentType
from ranged_value import Range
from combat import Damage, DamageType, Defense, DefenseType

if TYPE_CHECKING:
    from entity import Item


class Equippable(BaseComponent):
    _bonuses = ["power", "defense"]
    parent: Item

    def __init__(
            self,
            equipment_type: EquipmentType,
            power_bonus: Range = None,
            defense_bonus: Union[Defense, Range] = None,
    ):
        self.equipment_type = equipment_type

        self.power_bonus = power_bonus or Range(0)

        if isinstance(defense_bonus, Defense):
            self.defense_bonus: Defense = defense_bonus
        else:
            self.defense_bonus: Defense = Defense({DamageType.DEFAULT: (Range(), defense_bonus or Range())})

    def bonuses(self) -> list[tuple[str, Any]]:
        return [(name, getattr(self, f"{name}_bonus")) for name in self._bonuses]

    def description(self) -> list[str]:
        data = [f"Power bonus: {str(self.power_bonus)}"]
        if self.defense_bonus:
            data.append("")
            data.extend(self.defense_bonus.describe())
        return data


class Weapon(Equippable):
    def __init__(self, power_bonus: Range = None) -> None:
        super().__init__(equipment_type=EquipmentType.WEAPON, power_bonus=power_bonus)


class Armor(Equippable):
    def __init__(self, defense_bonus: Union[Defense, Range] = None) -> None:
        super().__init__(equipment_type=EquipmentType.ARMOR, defense_bonus=defense_bonus)
