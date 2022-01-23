import copy
import random
import time
from typing import TYPE_CHECKING
import math

import entity_factories
from procgen import (
    get_max_value_for_floor,
    max_monsters_by_floor,
    get_entities_at_random,
    enemy_chances
)
from entity_factories import player as user
from entity import Actor

from entity_factories import Factory
from entity import Entity


def gen_floor_monsters(floor_number: int) -> list[Entity]:
    number_of_monsters = random.randint(
        0, get_max_value_for_floor(max_monsters_by_floor, floor_number)
    )
    monsters: list[Factory] = get_entities_at_random(
        enemy_chances, number_of_monsters, floor_number
    )

    return [monster.construct(floor_number) for monster in monsters]


def level_up(player):
    before = copy.deepcopy(player.fighter)
    # player.level.auto_level_up(1, 20, 0, 1, 1)
    level = player.level.current_level % 5
    print("-- Level up: ", end="")
    # if player.fighter.hp != before.hp:
    if level in (3,):
        player.level.increase_max_hp(amount=20, log=False)
        print(f"+xp {player.fighter.max_hp - before.max_hp} ({player.fighter.max_hp})")
    # if player.fighter.mp != before.mp:
    if level in (5,):
        player.level.increase_max_mp(amount=1, log=False)
        print(f"+mp {player.fighter.max_mp - before.max_mp} ({player.fighter.max_mp})")
    # if player.fighter.power != before.power:
    if level in (2, 0):
        player.level.increase_power(amount=1, log=False)
        print(f"+pow {player.fighter.power - before.power} ({player.fighter.power})")
    # if player.fighter.defense != before.defense:
    if level in (1, 4):
        player.level.increase_defense(amount=1, log=False)
        print(f"+def {player.fighter.defense - before.defense} ({player.fighter.defense})")
    print("-- -- new char", player.fighter.max_hp, player.fighter.power, player.fighter.defense)


def main():
    random.seed(time.time())
    floors = 100

    dagger = entity_factories.dagger.construct(0)
    leather_armor = entity_factories.leather_armor.construct(0)

    player = user

    dagger.parent = player.inventory
    leather_armor.parent = player.inventory

    player.inventory.items.append(dagger)
    player.equipment.toggle_equip(dagger, add_message=False)

    player.inventory.items.append(leather_armor)
    player.equipment.toggle_equip(leather_armor, add_message=False)

    print("char", player.fighter.hp, player.fighter.power, player.fighter.defense)
    print()

    cheat_level = -1
    die_level = -1
    lose_level = -1
    heals = 0
    try:
        for floor in range(1, floors + 1):
            amount = min(floor * 15, int(player.fighter.max_hp * 0.5))
            player.fighter.heal(amount)

            cheat = True
            print("------")
            print(f"Floor: {floor}\nLevel: {player.level.current_level}")
            rooms = random.randint(9, 12)
            for room in range(rooms):
                monsters = gen_floor_monsters(floor)

                for monster in monsters:
                    if not isinstance(monster, Actor):
                        continue
                    damage = player.fighter.power - monster.fighter.defense
                    if damage > 0:
                        turns = math.ceil(monster.fighter.hp /
                                          (int(player.fighter.power) - int(monster.fighter.defense)))
                        receive = int(monster.fighter.power) - int(player.fighter.defense)
                        if turns * receive > 0:
                            cheat = False
                        else:
                            continue
                        if receive > player.fighter.max_hp:
                            print("-- !! YOU DIED !! --")
                            print(monster.name, turns, turns * receive)
                            if die_level == -1:
                                die_level = floor
                                raise Exception
                        while turns > 0:
                            if receive >= player.fighter.hp:
                                heals += 1
                                player.fighter.hp += 40
                            else:
                                player.fighter.hp -= receive
                                turns -= 1
                        player.level.add_xp(monster.level.xp_given, log=False)
                    else:
                        print("--", monster.name, "no damage;", monster.fighter.defense)
                        if lose_level == -1:
                            lose_level = floor
                            raise Exception
                        cheat = False

                    if player.level.requires_level_up:
                        level_up(player)
            if cheat:
                print("-- !! CHEATER !! --")
                if cheat_level == -1:
                    cheat_level = floor
            print()
    except:
        pass
    print()
    print(f"{cheat_level=}")
    print(f"{lose_level=}")
    print(f"{die_level=}")
    print(f"{heals=}")


if __name__ == '__main__':
    main()
