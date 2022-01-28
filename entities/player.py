from components.ai import BaseAI
from components.equipment import Equipment
from components.fighter import Fighter
from components.inventory import Inventory
from components.level import Level
from entity import Actor
from ranged_value import Range

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