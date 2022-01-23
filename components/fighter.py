from __future__ import annotations

from typing import TYPE_CHECKING, Union

import color
from components.base_component import BaseComponent
from render_order import RenderOrder

if TYPE_CHECKING:
    from entity import Actor
    from ranged_value import Range


class Fighter(BaseComponent):
    parent: Actor

    def __init__(self, hp: int, defense: Range, power: Range, mp: int = 0):
        self.max_hp = hp
        self._hp = hp

        self.max_mp = mp
        self._mp = mp

        self.base_defense = defense
        self.base_power = power

    @property
    def hp(self) -> int:
        return self._hp

    @hp.setter
    def hp(self, value: int) -> None:
        self._hp = max(0, min(value, self.max_hp))
        if self._hp == 0 and self.parent.ai:
            self.die()

    @property
    def defense(self) -> Range:
        return self.base_defense + self.defense_bonus

    @property
    def power(self) -> Range:
        return self.base_power + self.power_bonus

    @property
    def defense_bonus(self) -> Range:
        if self.parent.equipment:
            return self.parent.equipment.defense_bonus
        else:
            return Range(0)

    @property
    def power_bonus(self) -> Range:
        if self.parent.equipment:
            return self.parent.equipment.power_bonus
        else:
            return Range(0)

    @property
    def power_str(self) -> str:
        result = f"{self.base_power}"
        if self.power_bonus != 0:
            result += f" (+{self.power_bonus})"
        return result

    @property
    def defense_str(self) -> str:
        result = f"{self.base_defense}"
        if self.defense_bonus != 0:
            result += f" (+{self.defense_bonus})"
        return result

    @property
    def mp(self) -> int:
        return self._mp

    def use_mana(self, value: int) -> int:
        if self._mp >= value:
            self._mp -= value
            return value
        return 0

    def restore_mana(self, value: int) -> int:
        before = self.mp
        self._mp = max(0, min(before + value, self.max_mp))
        return self.mp - before

    def die(self) -> None:
        if self.engine.player is self.parent:
            death_message = "You died!"
            death_message_color = color.player_die
        else:
            death_message = f"{self.parent.name} is dead!"
            death_message_color = color.enemy_die
            self.engine.player.level.add_xp(self.parent.level.xp_given)

        self.parent.char = "%"
        self.parent.color = color.corps
        self.parent.blocks_movement = False
        self.parent.ai = None
        self.parent.render_order = RenderOrder.CORPSE
        self.parent.name = f"remains of {self.parent.name}"

        self.engine.message_log.add_message(death_message, death_message_color)

    def heal(self, amount: int) -> int:
        if not self.parent.is_alive:
            return 0
        before = self.hp
        self.hp += amount
        return self.hp - before

    def take_damage(self, amount: int) -> None:
        if self.parent.is_alive:
            self.hp -= amount

    def description(self) -> list[str]:
        return [f"HP: {self.hp}",
                f"Power: {self.power}",
                f"Defense: {self.defense}",
                ]
