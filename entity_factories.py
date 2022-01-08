from components.ai import HostileEnemy, BaseAI
from components import consumable, equippable
from components.equipment import Equipment
from components.fighter import Fighter
from components.inventory import Inventory
from components.level import Level
from entity import Actor, Item

player = Actor(
    char="@",
    color=(255, 255, 255),
    name="Player",
    ai_cls=BaseAI,
    equipment=Equipment(),
    fighter=Fighter(hp=100, defense=1, power=2, mp=100),
    inventory=Inventory(capacity=26),
    level=Level(level_up_base=200),
)

# ----- Enemies -----

orc = Actor(
    char="o",
    color=(63, 127, 63),
    name="Orc",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=20, defense=0, power=4),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=35),
)
troll = Actor(
    char="T",
    color=(0, 127, 0),
    name="Troll",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=30, defense=2, power=8),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=100),
)

# ----- Items -----

health_potion = Item(
    char="&",
    color=(127, 0, 255),
    name="Health Potion",
    consumable=consumable.HealingConsumable(amount=40),
)
mana_potion = Item(
    char="&",
    color=(0, 0, 255),
    name="Mana Potion",
    consumable=consumable.ManaConsumable(amount=10),
)
healing_book = Item(
    char="$",
    color=(127, 0, 255),
    name="Magic book: health",
    consumable=consumable.Permanent(mp=20, name="healing", consumable=consumable.HealingConsumable(amount=40)),
)
lightning_scroll = Item(
    char="#",
    color=(255, 255, 0),
    name="Lightning Scroll",
    consumable=consumable.LightningDamageConsumable(damage=30, maximum_range=5),
)
fireball_scroll = Item(
    char="#",
    color=(255, 0, 0),
    name="Fireball Scroll",
    consumable=consumable.FireballDamageConsumable(damage=15, radius=3),
)
confusion_scroll = Item(
    char="#",
    color=(207, 63, 255),
    name="Confusion Scroll",
    consumable=consumable.ConfusionConsumable(number_of_turns=10),
)

# ----- Equipment
dagger = Item(
    char="/",
    color=(0, 191, 255),
    name="Dagger",
    equippable=equippable.Weapon(power_bonus=2),
)
sword = Item(
    char="/",
    color=(0, 191, 255),
    name="Sword",
    equippable=equippable.Weapon(power_bonus=4),
)

leather_armor = Item(
    char="[",
    color=(139, 69, 19),
    name="Leather Armor",
    equippable=equippable.Armor(defense_bonus=1),
)

chain_mail = Item(
    char="[",
    color=(139, 69, 19),
    name="Chain Mail",
    equippable=equippable.Armor(defense_bonus=4),
)
