from __future__ import annotations

import math
from typing import TYPE_CHECKING
import random

from components.fighter import Fighter
from components.params import ActorStats
from entities.factory import EnemyFactory
from ranged_value import Range

if TYPE_CHECKING:
    from entity import Actor


def orc_level_up(enemy: Actor, floor: int, _):
    for level in range(3, floor + math.ceil(floor / 10)):
        match (level + random.randint(-1, 1)) % 3:
            case 0:
                enemy.level.increase_stat("constitution", log=False)
            case 1:
                enemy.level.increase_stat("concentration", log=False)
                if random.random() < 1 / 2:
                    enemy.level.increase_stat("constitution", log=False)
            case 2:
                enemy.level.increase_stat("strength", log=False)


def goblin_level_up(enemy: Actor, floor: int, _):
    for level in range(3, floor + math.ceil(floor / 10)):
        match (level + random.randint(-1, 1)) % 3:
            case 0:
                enemy.level.increase_stat("constitution", log=False)
            case 1:
                enemy.level.increase_stat("concentration", log=False)
                if random.random() < 1 / 2:
                    enemy.level.increase_stat("constitution", log=False)
            case 2:
                enemy.level.increase_stat("strength", log=False)
                enemy.level.increase_stat("strength", log=False)


def troll_level_up(enemy: Actor, floor: int, _):
    for level in range(4, floor + math.ceil(floor / 10)):
        match (level + random.randint(-1, 1)) % 3:
            case 0:
                enemy.level.increase_stat("constitution", log=False)
            case 1:
                if random.random() < 1 / 2:
                    enemy.level.increase_stat("concentration", log=False)
                    enemy.level.increase_stat("concentration", log=False)
                    enemy.level.increase_stat("constitution", log=False)
                else:
                    enemy.level.increase_stat("concentration", log=False)
                    enemy.level.increase_stat("constitution", log=False)

            case 2:
                if random.random() < 1 / 2:
                    enemy.level.increase_stat("strength", log=False)
                    enemy.level.increase_stat("strength", log=False)
                    enemy.level.increase_stat("strength", log=False)
                else:
                    enemy.level.increase_stat("strength", log=False)
                    enemy.level.increase_stat("strength", log=False)


orc = EnemyFactory(
    char="o",
    color=(63, 127, 63),
    name="Orc",
    fighter=Fighter(ActorStats(
        strength=2,
        concentration=0,
        hp_base=0,
        hp_mult=5,
        constitution=4,
    ),
        power=Range(1, 2),
    ),
    xp=35,
    base_floor=1,
    fit_to_level=orc_level_up,
)
goblin = EnemyFactory(
    char="g",
    color=(63, 127, 63),
    name="Goblin",
    fighter=Fighter(ActorStats(
        strength=5,
        concentration=1,
        hp_base=0,
        hp_mult=5,
        constitution=4,
    ),
    ),
    xp=60,
    base_floor=3,
    fit_to_level=goblin_level_up,
)
troll = EnemyFactory(
    char="T",
    color=(0, 127, 0),
    name="Troll",
    fighter=Fighter(ActorStats(
        strength=7,
        concentration=1,
        hp_base=0,
        hp_mult=5,
        constitution=6,
    ),
        power=Range(0, 2),
    ),
    xp=100,
    base_floor=4,
    fit_to_level=troll_level_up,
)
