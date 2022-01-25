import combat
from components.ai import HostileEnemy, BaseAI
from components import consumable, equippable, effects
from components.equipment import Equipment
from components.fighter import Fighter
from components.inventory import Inventory
from components.level import Level
from entity import Entity, Actor, Item
from components_types import EquipmentType, ConsumableTarget as Target, ConsumableType as Consume
from ranged_value import Range
from combat import Defense, DamageType, Damage


class Factory:
    def construct(self, floor: int) -> Entity:
        raise NotImplementedError()


player = Actor(
    char="@",
    color=(255, 255, 255),
    name="Player",
    ai_cls=BaseAI,
    equipment=Equipment(),
    fighter=Fighter(hp=100, defense=Range(1), power=Range(2), mp=100),
    inventory=Inventory(capacity=26),
    level=Level(level_up_base=200),
)


# ----- Enemies -----

class EnemyFactory(Factory):
    def __init__(self, char: str, color: tuple[int, int, int], name: str, fighter: Fighter, xp: int, base_floor: int):
        self.char = char
        self.color = color
        self.name = name
        self.fighter = fighter
        self.xp = xp
        self.base_level = base_floor

    def construct(self, floor: int) -> Actor:
        enemy = Actor(
            char=self.char,
            color=self.color,
            name=self.name,
            ai_cls=HostileEnemy,
            equipment=Equipment(),
            fighter=self.fighter.copy(),
            inventory=Inventory(capacity=0),
            level=Level(xp_given=self.xp),
            dungeon_level=floor,
        )
        enemy.level.auto_level_up(
            (floor - self.base_level) // 2,
            enemy.fighter.max_hp // 10,
            0,
            Range(1, 2),
            1,
        )
        return enemy


orc = EnemyFactory(
    char="o",
    color=(63, 127, 63),
    name="Orc",
    fighter=Fighter(hp=20, defense=Defense({DamageType.POISON: (Range(10), Range())}), power=Range(3, 4)),
    xp=35,
    base_floor=1,
)
goblin = EnemyFactory(
    char="g",
    color=(63, 127, 63),
    name="Goblin",
    fighter=Fighter(hp=20, defense=Range(1), power=Range(5)),
    xp=60,
    base_floor=3,
)
troll = EnemyFactory(
    char="T",
    color=(0, 127, 0),
    name="Troll",
    fighter=Fighter(hp=30, defense=Range(2), power=Range(7, 9)),
    xp=100,
    base_floor=4
)


# ----- Items -----

class ItemFactory(Factory):
    def __init__(self, char: str, color: tuple[int, int, int], name: str,
                 consume: consumable.Consumable = None,
                 equip: equippable.Equippable = None,
                 base_floor: int = -1):
        self.char = char
        self.color = color
        self.name = name
        self.consume = consume
        self.equip = equip
        self.base_level = base_floor

    def construct(self, floor: int) -> Item:
        item = Item(
            char=self.char,
            color=self.color,
            name=self.name,
            consumable=self.consume.copy() if self.consume is not None else None,
            equippable=self.equip.copy() if self.equip is not None else None,
            dungeon_level=floor,
        )
        if self.base_level != -1:
            pass
        return item


health_potion = ItemFactory(
    char="&",
    color=(127, 0, 255),
    name="Health Potion",
    consume=consumable.Potion(target=Target.SELF, effect=effects.HealEffect(40)),
)
mana_potion = ItemFactory(
    char="&",
    color=(0, 0, 255),
    name="Mana Potion",
    consume=consumable.Potion(target=Target.SELF, effect=effects.RestoreManaEffect(10)),
)
universal_potion = ItemFactory(
    char="&",
    color=(64, 0, 255),
    name="Universal Potion",
    consume=consumable.Potion(target=Target.SELF, effect=effects.Combine([
        effects.HealEffect(amount=40),
        effects.RestoreManaEffect(amount=20),
    ]))
)
regeneration_potion = ItemFactory(
    char="&",
    color=(3, 192, 60),
    name="Regeneration Potion",
    consume=consumable.Potion(target=Target.SELF, effect=effects.AddEffect(
        effects.DurableEffect(10, effects.HealEffect(4))
    ))
)

poison_scroll = ItemFactory(
    char="~",
    color=(128, 30, 70),
    name="Poison Scroll",
    consume=consumable.MagicScroll(
        target=Target.NEAREST, name="Poison", range=5,
        effect=effects.AddEffect(
            effects.DurableEffect(5, effects.DamageEffect(Damage(Range(2, 3), DamageType.POISON)))),
    ),
)
lightning_scroll = ItemFactory(
    char="~",
    color=(255, 255, 0),
    name="Lightning Scroll",
    consume=consumable.MagicScroll(
        target=Target.NEAREST, name="Lightning", range=5,
        effect=effects.DamageEffect(Damage(Range(10, 30), DamageType.LIGHTNING)),
    ),
)
fireball_scroll = ItemFactory(
    char="~",
    color=(255, 0, 0),
    name="Fireball Scroll",
    consume=consumable.MagicScroll(
        target=Target.RANGED, name="Fireball", radius=5,
        effect=effects.Combine([
            effects.DamageEffect(Damage(Range(10, 15), DamageType.FIRE)),
            effects.AddConfusionEffect(1),
        ])
    ),
)
firebolt_scroll = ItemFactory(
    char="~",
    color=(255, 0, 0),
    name="Firebolt Scroll",
    consume=consumable.MagicScroll(
        target=Target.RANDOM, name="Firebolt", range=5,
        effect=effects.DamageEffect(Damage(Range(15, 20), DamageType.FIRE)),
    ),
)
confusion_scroll = ItemFactory(
    char="~",
    color=(207, 63, 255),
    name="Confusion Scroll",
    consume=consumable.MagicScroll(
        target=Target.RANDOM, name="Confusion", range=5,
        effect=effects.AddConfusionEffect(10),
    ),
)

healing_book = ItemFactory(
    char="#",
    color=(127, 0, 255),
    name="Magic book: Health",
    consume=consumable.MagicBook(
        target=Target.SELF,
        mp=20,
        name="healing",
        effect=effects.HealEffect(40),
    ),
)
lightning_book = ItemFactory(
    char="#",
    color=(255, 255, 0),
    name="Magic book: Lighting",
    consume=consumable.MagicBook(
        target=Target.NEAREST,
        mp=30,
        name="lightning",
        effect=effects.DamageEffect(Damage(Range(25, 30), DamageType.LIGHTNING)),
        range=4
    ),
)
fireball_book = ItemFactory(
    char="#",
    color=(255, 0, 0),
    name="Magic book: Fireball",
    consume=consumable.MagicBook(
        target=Target.RANGED,
        mp=40,
        name="fireball",
        effect=effects.Combine([
            effects.DamageEffect(Damage(Range(25, 35), DamageType.FIRE)),
            effects.AddConfusionEffect(1),
        ]),
        radius=3
    ),
)
confusion_book = ItemFactory(
    char="#",
    color=(207, 63, 255),
    name="Magic book: Confusion",
    consume=consumable.MagicBook(
        target=Target.SELECTED,
        mp=20,
        name="confusion",
        effect=effects.AddConfusionEffect(5)
    ),
)

# ----- Equipment
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
)

shield = ItemFactory(
    char=")",
    color=(139, 69, 19),
    name="Shield",
    equip=equippable.Equippable(equipment_type=EquipmentType.SHIELD, defense_bonus=Range(2, 4)),
)
red_necklace = ItemFactory(
    char=",",
    color=(139, 20, 20),
    name="Red necklace",
    equip=equippable.Equippable(equipment_type=EquipmentType.NECKLACE,
                                defense_bonus=Defense({DamageType.FIRE: (Range(10), Range(0))})),
)
