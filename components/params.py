from dataclasses import dataclass

from ranged_value import Range
from combat import Defense, DamageType


@dataclass
class FighterParams:
    power: Range
    defense: Defense

    max_hp: int
    max_mp: int
    max_ep: int

    mana_regen_percent: float = 0.5
    mana_regen_turns: int = 10

    energy_regen_percent: float = 1
    energy_regen_turns: int = 10

    forced_move_energy: int = 15
    forced_attack_energy: int = 15
    forced_attack_mult: float = 1.5


@dataclass
class ActorStats:
    """
    Contain actor's base stats for fighter's parameters
    """
    strength: int = 1
    dexterity: int = 1
    constitution: int = 1
    intelligence: int = 1
    concentration: int = 1
    vitality: int = 1

    remains: int = 0
    used: int = 0

    hp_mult: int = 20
    mp_mult: int = 20
    ep_mult: int = 20

    hp_base: int = 0
    mp_base: int = 0
    ep_base: int = 0

    base_stats_names = ["strength", "dexterity", "constitution", "intelligence", "concentration", "vitality"]

    @property
    def params(self) -> FighterParams:
        return FighterParams(
            power=Range(self.strength, int(self.strength * 1.1)),
            defense=Defense(
                {
                    DamageType.PHYSICAL: (Range(self.dexterity), Range(self.concentration + self.constitution // 5))
                }
            ),

            max_hp=self.hp_mult * self.constitution + self.hp_base,
            max_mp=self.mp_mult * self.intelligence + self.mp_base,
            max_ep=self.ep_mult * self.vitality + self.ep_base,

            mana_regen_percent=self.intelligence / 2 + self.vitality // 5,
            energy_regen_percent=self.vitality / 2,
        )

    def describe(self) -> list[str]:
        return [f"{stat.title()}: {getattr(self, stat)}" for stat in self.base_stats_names]

    def increase_stat(self, stat: str):
        if stat not in self.base_stats_names:
            return
        setattr(self, stat, getattr(self, stat) + 1)

    def get_stat(self, stat):
        return getattr(self, stat)


"""
Fighter & params:
power = strength
defense = dexterity %, constitution/concentration ?
hp = constitution, vitality
mp = intelligence, vitality/concentration ?
ep = vitality/concentration ?

mana_percent = intelligence, vitality
mana_turns = intelligence, concentration

energy_percent = vitality
energy_turns = vitality

forced_move = dexterity, concentration
forced_attack = dexterity, concentration
forced_attack_mult = strength, dexterity
"""
