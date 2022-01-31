from __future__ import annotations

import math
from typing import TYPE_CHECKING
import random

from components.fighter import Fighter
from entities.factory import EnemyFactory
from ranged_value import Range

if TYPE_CHECKING:
    from entity import Actor


def orc_level_up(enemy: Actor, floor: int, _):
    base_hp = int(enemy.fighter.max_hp)
    for level in range(3, floor + math.ceil(floor / 10)):
        match (level + random.randint(-1, 1)) % 3:
            case 0:
                enemy.level.increase_max_hp(base_hp // 5, log=False)
            case 1:
                enemy.level.increase_defense(Range(2, 2 + (random.random() > 1 / 4)), log=False)
            case 2:
                enemy.level.increase_power(Range(2, 2 + (random.random() > 1 / 4)), log=False)


def goblin_level_up(enemy: Actor, floor: int, _):
    base_hp = int(enemy.fighter.max_hp)
    for level in range(3, floor + math.ceil(floor / 10)):
        match (level + random.randint(-1, 1)) % 3:
            case 0:
                enemy.level.increase_max_hp(base_hp // 5, log=False)
            case 1:
                enemy.level.increase_defense(Range(2, 2 + (random.random() > 1 / 3)), log=False)
            case 2:
                enemy.level.increase_power(Range(2, 2 + (random.random() > 1 / 3)), log=False)


def troll_level_up(enemy: Actor, floor: int, _):
    base_hp = int(enemy.fighter.max_hp)
    for level in range(4, floor + math.ceil(floor / 10)):
        match (level + random.randint(-1, 1)) % 3:
            case 0:
                enemy.level.increase_max_hp(base_hp // 4, log=False)
            case 1:
                if random.random() < 1 / 2:
                    enemy.level.increase_defense(Range(3, 3 + (random.random() > 1 / 3)), log=False)
                else:
                    enemy.level.increase_defense(Range(2, 2 + (random.random() > 1 / 3)), log=False)
            case 2:
                if random.random() < 1 / 2:
                    enemy.level.increase_power(Range(3, 3 + (random.random() > 1 / 3)), log=False)
                else:
                    enemy.level.increase_power(Range(2, 2 + (random.random() > 1 / 3)), log=False)


orc = EnemyFactory(
    char="o",
    color=(63, 127, 63),
    name="Orc",
    fighter=Fighter(hp=20, defense=Range(), power=Range(3, 4)),
    xp=35,
    base_floor=1,
    fit_to_level=orc_level_up,
)
goblin = EnemyFactory(
    char="g",
    color=(63, 127, 63),
    name="Goblin",
    fighter=Fighter(hp=20, defense=Range(1), power=Range(5)),
    xp=60,
    base_floor=3,
    fit_to_level=goblin_level_up,
)
troll = EnemyFactory(
    char="T",
    color=(0, 127, 0),
    name="Troll",
    fighter=Fighter(hp=30, defense=Range(2), power=Range(7, 9)),
    xp=100,
    base_floor=4,
    fit_to_level=troll_level_up,
)
