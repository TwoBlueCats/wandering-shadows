from components.ai import BaseAI
from components.equipment import Equipment
from components.fighter import Fighter
from components.inventory import Inventory
from components.level import Level
from components.params import ActorStats
from entity import Actor
from ranged_value import Range
from combat import Defense, DefenseType, DamageType

player = Actor(
    char="@",
    color=(255, 255, 255),
    name="Player",
    ai_cls=BaseAI,
    equipment=Equipment(),
    fighter=Fighter(ActorStats(
        hp_base=80,
        mp_base=80,
        ep_base=80
    ),
        power=Range(1)),
    inventory=Inventory(capacity=26),
    level=Level(level_up_base=200),
)
# hp=100, defense=Defense({DamageType.PHYSICAL: (Range(0), Range(1))}), power=Range(2), mp=100
