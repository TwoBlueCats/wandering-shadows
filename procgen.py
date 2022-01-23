from __future__ import annotations

import random
from typing import Iterator, TYPE_CHECKING

import tcod

import entity_factories
from game_map import GameMap
import tile_types

if TYPE_CHECKING:
    from engine import Engine
    from entity_factories import Factory

max_items_by_floor = [
    (1, 1),
    (4, 2),
]

max_monsters_by_floor = [
    (1, 2),
    (4, 3),
    (6, 5),
]

item_chances: dict[int, list[tuple[Factory, int]]] = {
    0: [
        (entity_factories.health_potion, 35),
        (entity_factories.mana_potion, 10),
        (entity_factories.healing_book, 1),
    ],
    2: [
        (entity_factories.confusion_scroll, 10),
        (entity_factories.healing_book, 10),
    ],
    4: [
        (entity_factories.lightning_scroll, 25),
        (entity_factories.sword, 15),
        (entity_factories.healing_book, 20),
        (entity_factories.confusion_book, 20),
    ],
    6: [
        (entity_factories.mana_potion, 35),
        (entity_factories.fireball_scroll, 25),
        (entity_factories.chain_mail, 15),
        (entity_factories.lightning_book, 10),
        (entity_factories.universal_potion, 30),
    ],
    8: [
        (entity_factories.fireball_book, 10),
        (entity_factories.helmet, 10),
    ],
    10: [
        (entity_factories.shield, 10),
        (entity_factories.health_potion, 10),
    ],
}

enemy_chances: dict[int, list[tuple[Factory, int]]] = {
    0: [(entity_factories.orc, 80), (entity_factories.goblin, 20)],
    3: [(entity_factories.troll, 5), (entity_factories.goblin, 40)],
    5: [(entity_factories.troll, 30), (entity_factories.goblin, 80)],
    7: [(entity_factories.troll, 60)],
}


def get_max_value_for_floor(max_value_by_floor: list[tuple[int, int]], floor: int) -> int:
    current_value = 0

    for floor_minimum, value in max_value_by_floor:
        if floor_minimum > floor:
            break
        else:
            current_value = value
    return current_value


def get_entities_at_random(
        weighted_chances_by_floor: dict[int, list[tuple[Factory, int]]],
        number_of_entities: int,
        floor: int,
) -> list[Factory]:
    entity_weighted_chances = {}

    for key, values in weighted_chances_by_floor.items():
        if key > floor:
            continue
        else:
            for value in values:
                entity = value[0]
                weighted_chance = value[1]

                entity_weighted_chances[entity] = weighted_chance

    entities = list(entity_weighted_chances.keys())
    entity_weighted_chance_values = list(entity_weighted_chances.values())

    chosen_entities = random.choices(
        entities, weights=entity_weighted_chance_values, k=number_of_entities
    )

    return chosen_entities


class RectangularRoom:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height

    @property
    def center(self) -> tuple[int, int]:
        center_x = int((self.x1 + self.x2) / 2)
        center_y = int((self.y1 + self.y2) / 2)

        return center_x, center_y

    @property
    def inner(self) -> tuple[slice, slice]:
        """Return the inner area of this room as a 2D array index."""
        return slice(self.x1 + 1, self.x2), slice(self.y1 + 1, self.y2)

    def intersects(self, other: RectangularRoom) -> bool:
        """Return True if this room overlaps with another RectangularRoom."""
        return (
                self.x1 <= other.x2
                and self.x2 >= other.x1
                and self.y1 <= other.y2
                and self.y2 >= other.y1
        )


def tunnel_between(
        start: tuple[int, int], end: tuple[int, int]
) -> Iterator[tuple[int, int]]:
    """Return an L-shaped tunnel between these two points."""
    x1, y1 = start
    x2, y2 = end
    if random.random() < 0.5:  # 50% chance.
        # Move horizontally, then vertically.
        corner_x, corner_y = x2, y1
    else:
        # Move vertically, then horizontally.
        corner_x, corner_y = x1, y2

    # Generate the coordinates for this tunnel.
    for x, y in tcod.los.bresenham((x1, y1), (corner_x, corner_y)).tolist():
        yield x, y
    for x, y in tcod.los.bresenham((corner_x, corner_y), (x2, y2)).tolist():
        yield x, y


def place_entities(room: RectangularRoom, dungeon: GameMap, floor_number: int) -> None:
    number_of_monsters = random.randint(
        0, get_max_value_for_floor(max_monsters_by_floor, floor_number)
    )
    number_of_items = random.randint(
        0, get_max_value_for_floor(max_items_by_floor, floor_number)
    )

    monsters: list[Factory] = get_entities_at_random(
        enemy_chances, number_of_monsters, floor_number
    )
    items: list[Factory] = get_entities_at_random(
        item_chances, number_of_items, floor_number
    )

    for factory in monsters + items:
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)

        if not any(entity_.x == x and entity_.y == y for entity_ in dungeon.entities):
            entity = factory.construct(floor_number)
            entity.place(x, y, dungeon)


def generate_dungeon(
        max_rooms: int,
        room_min_size: int,
        room_max_size: int,
        map_width: int,
        map_height: int,
        engine: Engine,
) -> GameMap:
    """Generate a new dungeon map."""
    player = engine.player
    dungeon = GameMap(engine, map_width, map_height, entities=[player])

    rooms: list[RectangularRoom] = []

    for r in range(max_rooms):
        room_width = random.randint(room_min_size, room_max_size)
        room_height = random.randint(room_min_size, room_max_size)

        x = random.randint(0, dungeon.width - room_width - 1)
        y = random.randint(0, dungeon.height - room_height - 1)

        # "RectangularRoom" class makes rectangles easier to work with
        new_room = RectangularRoom(x, y, room_width, room_height)

        # Run through the other rooms and see if they intersect with this one.
        if any(new_room.intersects(other_room) for other_room in rooms):
            continue  # This room intersects, so go to the next attempt.
        # If there are no intersections then the room is valid.

        # Dig out this rooms inner area.
        dungeon.tiles[new_room.inner] = tile_types.floor

        if len(rooms) == 0:
            # The first room, where the player starts.
            player.place(*new_room.center, dungeon)
        else:  # All rooms after the first.
            # Dig out a tunnel between this room and the previous one.
            for x, y in tunnel_between(rooms[-1].center, new_room.center):
                dungeon.tiles[x, y] = tile_types.floor

        place_entities(new_room, dungeon, engine.game_world.current_floor)

        # Finally, append the new room to the list.
        rooms.append(new_room)

    farthest = player.position
    for room in rooms:
        if player.distance(*room.center) > player.distance(*farthest):
            farthest = room.center

    dungeon.tiles[farthest] = tile_types.down_stairs
    dungeon.downstairs_location = farthest

    return dungeon
