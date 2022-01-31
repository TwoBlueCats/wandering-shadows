import random

from combat import Defense, DamageType
from components import equippable
from components_types import EquipmentType
from entities.factory import ItemFactory
from ranged_value import Range


def sword_level_up(item, floor, base):
    limit = (floor - base)
    item.equippable.power_bonus += random.randint(1, limit)


def def_level_up(item, floor, base):
    limit = (floor - base) // 3
    item.equippable.defense_bonus += random.randint(1, limit)


dagger = ItemFactory(
    char="/",
    color=(0, 191, 255),
    name="Dagger",
    equip=equippable.Weapon(power_bonus=Range(1)),
)
sword = ItemFactory(
    char="/",
    color=(0, 191, 255),
    name="Sword",
    equip=equippable.Weapon(power_bonus=Range(2, 3)),
    base_floor=4,
    fit_to_level=sword_level_up
)

leather_armor = ItemFactory(
    char="[",
    color=(139, 69, 19),
    name="Leather Armor",
    equip=equippable.Armor(defense_bonus=Range(1)),
)
chain_mail = ItemFactory(
    char="[",
    color=(139, 69, 19),
    name="Chain Mail",
    equip=equippable.Equippable(equipment_type=EquipmentType.ARMOR, defense_bonus=Range(4), power_bonus=Range(-1)),
)
helmet = ItemFactory(
    char="^",
    color=(139, 69, 19),
    name="Helmet",
    equip=equippable.Equippable(equipment_type=EquipmentType.HELMET, defense_bonus=Range(2)),
    fit_to_level=def_level_up,
    base_floor=10
)
shield = ItemFactory(
    char=")",
    color=(139, 69, 19),
    name="Shield",
    equip=equippable.Equippable(equipment_type=EquipmentType.SHIELD, defense_bonus=Range(2, 4)),
    fit_to_level=def_level_up,
    base_floor=10
)

red_necklace = ItemFactory(
    char=",",
    color=(139, 20, 20),
    name="Red necklace",
    equip=equippable.Equippable(equipment_type=EquipmentType.NECKLACE,
                                defense_bonus=Defense({DamageType.FIRE: (Range(10), Range(0))})),
)
