from __future__ import annotations

from typing import TYPE_CHECKING
import random

from components.base_component import BaseComponent

if TYPE_CHECKING:
    from entity import Actor


class Level(BaseComponent):
    parent: Actor

    def __init__(
            self,
            current_level: int = 1,
            current_xp: int = 0,
            level_up_base: int = 0,
            level_up_factor: int = 150,
            xp_given: int = 0,
    ):
        self.current_level = current_level
        self.current_xp = current_xp
        self.level_up_base = level_up_base
        self.level_up_factor = level_up_factor
        self.xp_given = xp_given

    @property
    def experience_to_next_level(self) -> int:
        return self.current_level * (2 * self.level_up_base + (self.current_level + 1) * self.level_up_factor) // 2

    @property
    def requires_level_up(self) -> bool:
        return self.current_xp >= self.experience_to_next_level

    def add_xp(self, xp: int) -> None:
        if xp == 0 or self.level_up_base == 0:
            return

        self.current_xp += xp

        self.engine.message_log.add_message(f"You gain {xp} experience points.")

        if self.requires_level_up:
            self.engine.message_log.add_message(
                f"You advance to level {self.current_level + 1}!"
            )

    def increase_level(self) -> None:
        self.current_level += 1

    def increase_max_hp(self, amount: int = 20, log: bool = True) -> None:
        self.parent.fighter.max_hp += amount
        self.parent.fighter.hp += amount

        if log:
            self.engine.message_log.add_message("Your health improves!")

        self.increase_level()

    def increase_max_mp(self, amount: int = 20, log: bool = True) -> None:
        self.parent.fighter.max_mp += amount
        self.parent.fighter.restore_mana(amount)
        if log:
            self.engine.message_log.add_message("Your magic improves!")

        self.increase_level()

    def increase_power(self, amount: int = 1, log: bool = True) -> None:
        self.parent.fighter.base_power += amount
        if log:
            self.engine.message_log.add_message("You feel stronger!")

        self.increase_level()

    def increase_defense(self, amount: int = 1, log: bool = True) -> None:
        self.parent.fighter.base_defense += amount
        if log:
            self.engine.message_log.add_message("Your movements are getting swifter!")

        self.increase_level()

    def auto_level_up(self, amount: int, hp: int, mp: int, pw: int, df: int) -> int:
        values = []
        if hp > 0:
            values.append(lambda: self.increase_max_hp(amount=hp, log=False))
        if mp > 0:
            values.append(lambda: self.increase_max_mp(amount=mp, log=False))
        if pw > 0:
            values.append(lambda: self.increase_power(amount=pw, log=False))
        if df > 0:
            values.append(lambda: self.increase_defense(amount=df, log=False))
        for _ in range(amount):
            random.choice(values)()
            self.xp_given += int(self.xp_given * 0.05)

        return self.current_level
