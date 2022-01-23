from components.ai import HostileEnemy, BaseAI
from components import consumable, equippable
from components.equipment import Equipment
from components.fighter import Fighter
from components.inventory import Inventory
from components.level import Level
from entity import Entity, Actor, Item
from components_types import EquipmentType, ConsumableTarget as Target, ConsumableType as Consume
from ranged_value import Range


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
    fighter=Fighter(hp=20, defense=Range(0), power=Range(3, 4)),
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
    consume=consumable.HealingConsumable(target=Target.SELF, consume_type=Consume.POTION, amount=40),
)
mana_potion = ItemFactory(
    char="&",
    color=(0, 0, 255),
    name="Mana Potion",
    consume=consumable.ManaConsumable(target=Target.SELF, amount=10, consume_type=Consume.POTION),
)
universal_potion = ItemFactory(
    char="&",
    color=(64, 0, 255),
    name="Universal Potion",
    consume=consumable.Combine(consume_type=Consume.POTION, consumables=[
        consumable.HealingConsumable(target=Target.SELF, amount=40),
        consumable.ManaConsumable(target=Target.SELF, amount=20)
    ])
)

lightning_scroll = ItemFactory(
    char="~",
    color=(255, 255, 0),
    name="Lightning Scroll",
    consume=consumable.LightningDamageConsumable(target=Target.NEAREST, consume_type=Consume.SCROLL,
                                                 damage=Range(10, 30), maximum_range=5),
)
fireball_scroll = ItemFactory(
    char="~",
    color=(255, 0, 0),
    name="Fireball Scroll",
    consume=consumable.FireballDamageConsumable(target=Target.RANGED, consume_type=Consume.SCROLL, damage=Range(10, 15),
                                                radius=3),
)
confusion_scroll = ItemFactory(
    char="~",
    color=(207, 63, 255),
    name="Confusion Scroll",
    consume=consumable.ConfusionConsumable(target=Target.SELECTED, consume_type=Consume.SCROLL, number_of_turns=10),
)

healing_book = ItemFactory(
    char="#",
    color=(127, 0, 255),
    name="Magic book: Health",
    consume=consumable.MagicBook(
        mp=20,
        name="healing",
        consumable=consumable.HealingConsumable(target=Target.SELF, amount=40),
    ),
)
lightning_book = ItemFactory(
    char="#",
    color=(255, 255, 0),
    name="Magic book: Lighting",
    consume=consumable.MagicBook(
        mp=30,
        name="lightning",
        consumable=consumable.LightningDamageConsumable(target=Target.NEAREST, damage=Range(20, 35), maximum_range=4),
    ),
)
fireball_book = ItemFactory(
    char="#",
    color=(255, 0, 0),
    name="Magic book: Fireball",
    consume=consumable.MagicBook(
        mp=40,
        name="fireball",
        consumable=consumable.FireballDamageConsumable(target=Target.RANGED, damage=Range(25, 35), radius=3),
    ),
)
confusion_book = ItemFactory(
    char="#",
    color=(207, 63, 255),
    name="Magic book: Confusion",
    consume=consumable.MagicBook(
        mp=20,
        name="confusion",
        consumable=consumable.ConfusionConsumable(target=Target.SELECTED, number_of_turns=5),
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
