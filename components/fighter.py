from __future__ import annotations

import math
from typing import TYPE_CHECKING, Union

import color
from components.base_component import BaseComponent
from render_order import RenderOrder
from ranged_value import Range
from combat import Damage, DamageType, Defense, DefenseType

if TYPE_CHECKING:
    from entity import Actor


class Fighter(BaseComponent):
    parent: Actor

    def __init__(self, hp: int, defense: Union[Defense, Range], power: Range, mp: int = 0):
        self.max_hp = hp
        self._hp = hp

        self.max_mp = mp
        self._mp = mp

        if isinstance(defense, Defense):
            self.base_defense: Defense = defense
        else:
            self.base_defense: Defense = Defense({DamageType.DEFAULT: (Range(), defense or Range())})
        self.base_power = power

        self.hp_decrease_turn = 0
        self.mana_decrease_turn = 0

        self.mana_regen_percent = 0.5
        self.mana_regen_turns = 10

    @property
    def hp(self) -> int:
        return math.ceil(self._hp)

    @hp.setter
    def hp(self, value: float) -> None:
        if value < self._hp:
            self.hp_decrease_turn = self.engine.turn
        self._hp = max(0., min(value, self.max_hp))
        if self._hp == 0 and self.parent.ai:
            self.die()

    @property
    def defense(self) -> Defense:
        return self.base_defense + self.defense_bonus

    @property
    def power(self) -> Range:
        return self.base_power + self.power_bonus

    @property
    def defense_bonus(self) -> Defense:
        if self.parent.equipment:
            return self.parent.equipment.defense_bonus
        else:
            return Defense()

    @property
    def power_bonus(self) -> Range:
        if self.parent.equipment:
            return self.parent.equipment.power_bonus
        else:
            return Range(0)

    @property
    def mp(self) -> int:
        return math.ceil(self._mp)

    def use_mana(self, value: int) -> int:
        if self._mp >= value:
            self._mp -= value
            self.mana_decrease_turn = self.engine.turn
            return value
        return 0

    def restore_mana(self, value: float) -> float:
        before = self._mp
        self._mp = max(0., min(before + value, self.max_mp))
        return self._mp - before

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

    def heal(self, amount: float) -> float:
        if not self.parent.is_alive:
            return 0
        before = self._hp
        self.hp += amount
        return self.hp - before

    def take_damage(self, amount: float) -> float:
        if self.parent.is_alive:
            before = self.hp
            self.hp -= amount
            return before - self.hp
        return 0

    def description(self) -> list[str]:
        return [f"HP: {self.hp}",
                f"MP: {self.mp}",
                f"Power: {self.power}",
                f"Defense:",
                *self.defense.describe()
                ]
