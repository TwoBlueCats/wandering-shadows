from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity


class Action:
    def perform(self, engine: Engine, entity: Entity, **kwargs) -> None:
        """Perform this action with the objects needed to determine its scope.

        `engine` is the scope this action is being performed in.

        `entity` is the object performing the action.

        This method must be overridden by Action subclasses.
        """
        raise NotImplementedError()

    @staticmethod
    def name():
        raise NotImplementedError()


class EscapeAction(Action):
    def perform(self, engine: Engine, entity: Entity, **kwargs) -> None:
        raise SystemExit()

    @staticmethod
    def name():
        return "EscapeAction"


class ActionWithDirection(Action):
    def __init__(self, dx: int, dy: int):
        super().__init__()

        self.dx = dx
        self.dy = dy

    def perform(self, engine: Engine, entity: Entity, **kwargs) -> None:
        raise NotImplementedError()

    @staticmethod
    def name():
        raise NotImplementedError()


class MeleeAction(ActionWithDirection):
    def perform(self, engine: Engine, entity: Entity, **kwargs) -> None:
        dest_x = entity.x + self.dx
        dest_y = entity.y + self.dy
        target = kwargs.get("target", engine.game_map.get_blocking_entity_at_location(dest_x, dest_y))
        if target is None:
            return  # No entity to attack.

        print(f"You kick the {target.name}, much to its annoyance!")

    @staticmethod
    def name():
        return "MeleeAction"


class MovementAction(ActionWithDirection):
    def perform(self, engine: Engine, entity: Entity, **kwargs) -> None:
        dest_x = entity.x + self.dx
        dest_y = entity.y + self.dy

        if not engine.game_map.in_bounds(dest_x, dest_y):
            return  # Destination is out of bounds.
        if not engine.game_map.tiles["walkable"][dest_x, dest_y]:
            return  # Destination is blocked by a tile.
        if engine.game_map.get_blocking_entity_at_location(dest_x, dest_y):
            return  # Destination is blocked by an entity.

        entity.move(self.dx, self.dy)

    @staticmethod
    def name():
        return "MovementAction"


class DirectedActionDispatcher(ActionWithDirection):
    def perform(self, engine: Engine, entity: Entity, **kwargs) -> None:
        dest_x = entity.x + self.dx
        dest_y = entity.y + self.dy

        if (target := engine.game_map.get_blocking_entity_at_location(dest_x, dest_y)) and target is not None:
            return MeleeAction(self.dx, self.dy).perform(engine, entity, target=target)
        else:
            return MovementAction(self.dx, self.dy).perform(engine, entity)

    @staticmethod
    def name():
        return "DirectedActionDispatcher"
