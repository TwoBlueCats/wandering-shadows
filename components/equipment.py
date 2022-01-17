from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from components.base_component import BaseComponent
from equipment_types import EquipmentType

if TYPE_CHECKING:
    from entity import Actor, Item


class Equipment(BaseComponent):
    parent: Actor

    def __init__(self, items: Optional[dict[EquipmentType, Item]] = None):
        self.items: dict[EquipmentType, Item] = items or {}

    @property
    def defense_bonus(self) -> int:
        bonus = 0
        for item in self.items.values():
            if item.equippable is not None:
                bonus += item.equippable.defense_bonus

        return bonus

    @property
    def power_bonus(self) -> int:
        bonus = 0
        for item in self.items.values():
            if item.equippable is not None:
                bonus += item.equippable.power_bonus

        return bonus

    def item_is_equipped(self, item: Item) -> bool:
        return item in self.items.values()

    def unequip_message(self, item_name: str) -> None:
        self.parent.game_map.engine.message_log.add_message(f"You remove the {item_name}.")

    def equip_message(self, item_name: str) -> None:
        self.parent.game_map.engine.message_log.add_message(f"You equip the {item_name}.")

    def equip_to_slot(self, slot: EquipmentType, item: Item, add_message: bool = True) -> None:
        current_item = self.items.get(slot, None)

        if current_item is not None:
            self.unequip_from_slot(slot, add_message)

        self.items[slot] = item
        if add_message:
            self.equip_message(item.name)

    def unequip_from_slot(self, slot: EquipmentType, add_message: bool = True) -> None:
        current_item = self.items.get(slot, None)

        if current_item is not None and add_message:
            self.unequip_message(current_item.name)
        del self.items[slot]

    def toggle_equip(self, item: Item, add_message: bool = True) -> None:
        if not item.equippable:
            self.parent.game_map.engine.message_log.add_message(f"You can not equip the {item.name}.")
            return
        slot = item.equippable.equipment_type

        if self.items.get(slot) == item:
            self.unequip_from_slot(slot, add_message)
        else:
            self.equip_to_slot(slot, item, add_message)
