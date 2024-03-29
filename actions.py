from __future__ import annotations

import random
from typing import Optional, TYPE_CHECKING

import tcod.event

import color
import exceptions
from config import Config
from entity import Torch

if TYPE_CHECKING:
    from engine import Engine
    from entity import Actor, Entity, Item


class Action:
    def __init__(self, entity: Actor) -> None:
        super().__init__()
        self.entity = entity

    @property
    def engine(self) -> Engine:
        """Return the engine this action belongs to."""
        return self.entity.parent.engine

    def perform(self) -> None:
        """Perform this action with the objects needed to determine its scope.

        `self.engine` is the scope this action is being performed in.

        `self.entity` is the object performing the action.

        This method must be overridden by Action subclasses.
        """
        raise NotImplementedError()

    @staticmethod
    def action_name():
        raise NotImplementedError()


class PickupAction(Action):
    """Pickup an item and add it to the inventory, if there is room for it."""

    def __init__(self, entity: Actor):
        super().__init__(entity)

    def perform(self) -> None:
        actor_location_x = self.entity.x
        actor_location_y = self.entity.y
        inventory = self.entity.inventory

        for item in self.engine.game_map.items:
            if actor_location_x == item.x and actor_location_y == item.y:
                if len(inventory.items) >= inventory.capacity:
                    raise exceptions.Impossible("Your inventory is full.")

                self.engine.game_map.entities.remove(item)
                item.parent = self.entity.inventory
                inventory.items.append(item)

                self.engine.message_log.add_message(f"You picked up the {item.name}!")
                return

        raise exceptions.Impossible("There is nothing here to pick up.")

    @staticmethod
    def action_name():
        return "PickupAction"


class ItemAction(Action):
    def __init__(
            self, entity: Actor, item: Item, target_xy: Optional[tuple[int, int]] = None
    ):
        super().__init__(entity)
        self.item = item
        if not target_xy:
            target_xy = entity.x, entity.y
        self.target_xy = target_xy

    @property
    def target_actor(self) -> Optional[Actor]:
        """Return the actor at this action's destination."""
        return self.engine.game_map.get_actor_at_location_abs(*self.target_xy)

    def perform(self) -> None:
        """Invoke the item's ability, this action will be given to provide context."""
        if self.item.consumable:
            self.item.consumable.activate(self)

    @staticmethod
    def action_name():
        return "ItemAction"


class DropItem(ItemAction):
    def perform(self) -> None:
        if self.entity.equipment.item_is_equipped(self.item):
            self.entity.equipment.toggle_equip(self.item)
        self.entity.inventory.drop(self.item)


class EquipAction(Action):
    def __init__(self, entity: Actor, item: Item):
        super().__init__(entity)

        self.item = item

    def perform(self) -> None:
        self.entity.equipment.toggle_equip(self.item)

    @staticmethod
    def action_name():
        return "EquipAction"


class WaitAction(Action):
    def perform(self) -> None:
        pass

    @staticmethod
    def action_name():
        return "WaitAction"


class TakeStairsAction(Action):
    def perform(self) -> None:
        """
        Take the stairs, if any exist at the entity's location.
        """
        if (self.entity.x, self.entity.y) == self.engine.game_map.downstairs_location:
            player = self.engine.player
            amount = min(self.engine.game_world.current_floor * 15, int(player.fighter.max_hp * 0.5))
            if (heal := player.fighter.heal(amount)) > 0:
                self.engine.message_log.add_message(
                    f"You take a moment to rest, and recover your health {int(heal)}.",
                    color.descend,
                )
            else:
                self.engine.message_log.add_message(f"You are full of strength.", color.descend)

            amount = min(self.engine.game_world.current_floor * 20, int(player.fighter.max_mp * 0.5))
            if (restore := player.fighter.restore_mana(amount)) > 0:
                self.engine.message_log.add_message(
                    f"You take a moment to rest, and restore your mana storage {restore}.",
                    color.descend,
                )
            else:
                self.engine.message_log.add_message(f"You are full of magic.", color.descend)

            self.engine.game_world.generate_floor()
            self.engine.message_log.add_message(
                "You descend the staircase.", color.descend
            )
        else:
            raise exceptions.Impossible("There are no stairs here.")

    @staticmethod
    def action_name():
        return "TakeStairsAction"


class ActionWithDirection(Action):
    def __init__(self, entity: Actor, dx: int, dy: int, modifier: tcod.event.Modifier = tcod.event.Modifier.NONE):
        super().__init__(entity)

        self.dx = dx
        self.dy = dy
        self.modifier = modifier

    @property
    def dest_xy(self) -> tuple[int, int]:
        """Returns this actions destination."""
        return self.entity.x + self.dx, self.entity.y + self.dy

    @property
    def blocking_entity(self) -> Optional[Entity]:
        """Return the blocking entity at this action's destination."""
        return self.engine.game_map.get_blocking_entity_at_location(*self.dest_xy)

    def perform(self) -> None:
        raise NotImplementedError()

    @staticmethod
    def action_name():
        raise NotImplementedError()

    @property
    def target_actor(self) -> Optional[Actor]:
        """Return the actor at this actions destination."""
        return self.engine.game_map.get_actor_at_location_abs(*self.dest_xy)


class MeleeAction(ActionWithDirection):
    def perform(self) -> None:
        target = self.target_actor
        if target is None:
            raise exceptions.Impossible("Nothing to attack.")
        power = self.entity.fighter.power
        if self.modifier:
            power *= self.entity.params.forced_attack_mult
        damage = target.fighter.defense.decrease(power)

        attack_desc = f"{self.entity.name.capitalize()} attacks {target.name}"
        if self.entity is self.engine.player:
            attack_color = color.player_atk
        else:
            attack_color = color.enemy_atk

        if damage > 0:
            real = target.fighter.take_damage(damage)
            self.engine.message_log.add_message(
                f"{attack_desc} for {round(real)} hit points.", attack_color
            )
        else:
            self.engine.message_log.add_message(
                f"{attack_desc} but does no damage.", attack_color
            )
        if self.modifier & self.modifier.CTRL:  # forced melee attack
            self.entity.fighter.ep -= self.entity.params.forced_attack_energy

    @staticmethod
    def action_name():
        return "MeleeAction"


class MovementAction(ActionWithDirection):
    def perform(self) -> None:
        dest_x, dest_y = self.dest_xy

        if not self.engine.game_map.in_bounds(dest_x, dest_y):
            raise exceptions.Impossible("That way is blocked.")
        if not self.engine.game_map.tiles["walkable"][dest_x, dest_y]:
            raise exceptions.Impossible("That way is blocked.")
        if self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y):
            raise exceptions.Impossible("That way is blocked.")

        self.entity.move(self.dx, self.dy)
        if self.modifier & self.modifier.SHIFT:  # forced move
            self.entity.fighter.ep -= self.entity.params.forced_move_energy

    @staticmethod
    def action_name():
        return "MovementAction"


class DirectedActionDispatcher(ActionWithDirection):
    def perform(self) -> None:
        if self.modifier & self.modifier.SHIFT:  # forced move
            dest = (self.entity.x + self.dx * 2, self.entity.y + self.dy * 2)
            if (self.entity.fighter.ep >= self.entity.params.forced_move_energy
                    and not self.engine.game_map.get_actor_at_location_abs(*dest)):
                return MovementAction(self.entity, self.dx * 2, self.dy * 2, self.modifier).perform()
            else:
                return MovementAction(self.entity, self.dx, self.dy).perform()
        if (self.entity.fighter.ep >= self.entity.params.forced_move_energy
                and self.modifier & self.modifier.CTRL):  # forced melee attack
            return MeleeAction(self.entity, self.dx, self.dy, self.modifier).perform()
        # base move/melee attack
        if self.target_actor:
            return MeleeAction(self.entity, self.dx, self.dy).perform()
        else:
            return MovementAction(self.entity, self.dx, self.dy).perform()

    @staticmethod
    def action_name():
        return "DirectedActionDispatcher"


class ImpossibleAction(Action):
    def __init__(self, entity: Actor, text: str = "It is impossible actions"):
        super().__init__(entity)
        self.text = text

    def perform(self) -> None:
        raise exceptions.Impossible(self.text)

    @staticmethod
    def action_name():
        return "ImpossibleAction"


class PlaceTorchAction(Action):
    def perform(self) -> None:
        for entity in self.engine.game_map.get_entities_at_location(*self.entity.position):
            if isinstance(entity, Torch):
                self.engine.game_map.entities.remove(entity)
                return
        torch = Torch(r=Config.torch_radius)
        torch.place(self.entity.x, self.entity.y, self.engine.game_map)

    @staticmethod
    def action_name():
        return "PlaceTorch"
