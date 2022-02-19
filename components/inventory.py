from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from components.base_component import BaseComponent

if TYPE_CHECKING:
    from entity import Actor, Item


class Inventory(BaseComponent):
    parent: Actor

    def __init__(self, capacity: int, slots: int = 0):
        self.capacity = capacity
        self.items: list[Item] = []
        self.slots_cnt = slots
        self.slots: list[Optional[Item]] = [None] * slots

    def remove(self, item: Item) -> None:
        self.items.remove(item)
        if item in self.slots:
            index = self.slots.index(item)
            self.slots[index] = None

    def drop(self, item: Item) -> None:
        """
        Removes an item from the inventory and restores it to the game map, at the player's current location.
        """
        self.remove(item)
        item.place(self.parent.x, self.parent.y, self.game_map)

        self.engine.message_log.add_message(f"You dropped the {item.name}.")
