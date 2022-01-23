from __future__ import annotations

import random
from typing import Optional, TYPE_CHECKING
from operator import attrgetter
from itertools import chain

import actions
import color
import components.ai
import components.inventory
from components.base_component import BaseComponent
from exceptions import Impossible
from input_handlers import SingleRangedAttackHandler, AreaRangedAttackHandler, ActionOrHandler
from components_types import ConsumableTarget, ConsumableType
from ranged_value import Range

if TYPE_CHECKING:
    from entity import Actor, Item


class Consumable(BaseComponent):
    parent: Item

    def __init__(self, target: ConsumableTarget, consume_type: ConsumableType = ConsumableType.NONE):
        self.targetType = target
        self.consumeType = consume_type
        self._targets: Optional[list[Actor]] = None

    def get_action(self, consumer: Actor) -> Optional[ActionOrHandler]:
        """Try to return the action for this item."""
        match self.targetType:
            case ConsumableTarget.SELF:
                self._targets = [consumer]
                return actions.ItemAction(consumer, self.parent)
            case ConsumableTarget.RANDOM:
                self._targets = self._get_random_target(consumer)
                return actions.ItemAction(consumer, self.parent)
            case ConsumableTarget.NEAREST:
                self._targets = self._get_nearest_target(consumer)
                return actions.ItemAction(consumer, self.parent)
            case ConsumableTarget.SELECTED:
                def callback(xy: tuple[int, int]) -> Optional[ActionOrHandler]:
                    self._targets = self._get_selected_target(consumer, xy)
                    return actions.ItemAction(consumer, self.parent, target_xy=xy)

                self.engine.message_log.add_message(
                    "Select a target location.", color.needs_target
                )
                return SingleRangedAttackHandler(
                    self.engine,
                    callback=callback,
                )
            case ConsumableTarget.RANGED:
                def callback(xy: tuple[int, int]) -> Optional[ActionOrHandler]:
                    self._targets = self._get_ranged_targets(consumer, xy)
                    return actions.ItemAction(consumer, self.parent, target_xy=xy)

                self.engine.message_log.add_message(
                    "Select a target location.", color.needs_target
                )
                return AreaRangedAttackHandler(
                    self.engine,
                    radius=self.radius,
                    callback=callback,
                )
            case _:
                return actions.ImpossibleAction(consumer)

    @property
    def radius(self) -> int:
        return 0

    @property
    def range(self) -> int:
        return 0

    def _get_nearest_target(self, consumer: Actor) -> list[Actor]:
        target = None
        closest_distance = self.range + 1.0

        for actor in self.engine.game_map.actors:
            if actor is not consumer and self.parent.game_map.visible[actor.x, actor.y]:
                distance = consumer.distance(actor.x, actor.y)

                if distance < closest_distance:
                    target = actor
                    closest_distance = distance

        return [target] if target else []

    def _get_random_target(self, consumer: Actor) -> list[Actor]:
        targets: list[Actor] = []

        for actor in self.engine.game_map.actors:
            if actor is not consumer and self.parent.game_map.visible[actor.x, actor.y]:
                distance = consumer.distance(actor.x, actor.y)

                if distance < self.range:
                    targets.append(actor)

        return random.choices(targets) if targets else []

    def _get_selected_target(self, consumer: Actor, xy: tuple[int, int]) -> list[Actor]:
        if not self.engine.game_map.visible[xy]:
            raise Impossible("You cannot target an area that you cannot see.")
        target = self.engine.game_map.get_actor_at_location(*xy)
        return [target] if target else []

    def _get_ranged_targets(self, consumer: Actor, xy: tuple[int, int]) -> list[Actor]:
        targets = []
        for actor in self.engine.game_map.actors:
            if actor.distance(*xy) <= self.radius:
                targets.append(actor)
        return targets

    def activate(self, action: actions.ItemAction) -> None:
        """Invoke this item's ability.

        `action` is the context for this activation.
        """
        raise NotImplementedError()

    def consume(self) -> None:
        """Remove the consumed item from its containing inventory."""
        entity = self.parent
        inventory = entity.parent
        if isinstance(inventory, components.inventory.Inventory) and entity in inventory.items:
            inventory.items.remove(entity)

    def description(self) -> list[str]:
        raise NotImplementedError()


class HealingConsumable(Consumable):
    def __init__(self, target: ConsumableTarget, amount: int, consume_type: ConsumableType = ConsumableType.NONE):
        super().__init__(target, consume_type)
        self.amount = amount

    def activate(self, action: actions.ItemAction) -> None:
        was = False
        for target in self._targets:
            amount_recovered = target.fighter.heal(self.amount)
            if amount_recovered > 0:
                was = True
                if target == self.engine.player:
                    self.engine.message_log.add_message(
                        f"You consume the {self.parent.name}, and recover {amount_recovered} HP!",
                        color.health_recovered,
                    )
        if was:
            self.consume()
        else:
            raise Impossible(f"Targets' health is already full.")

    def description(self) -> list[str]:
        return [f"Heal amount: {self.amount}"]


class ManaConsumable(Consumable):
    def __init__(self, target: ConsumableTarget, amount: int, consume_type: ConsumableType = ConsumableType.NONE):
        super().__init__(target, consume_type)
        self.amount = amount

    def activate(self, action: actions.ItemAction) -> None:
        was = False
        for target in self._targets:
            amount_recovered = target.fighter.restore_mana(self.amount)
            if amount_recovered > 0:
                was = True
                if target == self.engine.player:
                    self.engine.message_log.add_message(
                        f"You consume the {self.parent.name}, and recover {amount_recovered} MP!",
                        color.health_recovered,
                    )
        if was:
            self.consume()
        else:
            raise Impossible(f"Targets' mana is already full.")

    def description(self) -> list[str]:
        return [f"Mana restore: {self.amount}"]


class LightningDamageConsumable(Consumable):
    def __init__(self, target: ConsumableTarget, damage: Range, maximum_range: int,
                 consume_type: ConsumableType = ConsumableType.NONE):
        super().__init__(target, consume_type)
        self.damage = damage
        self.maximum_range = maximum_range

    @property
    def range(self) -> int:
        return self.maximum_range

    def activate(self, action: actions.ItemAction) -> None:
        for target in self._targets:
            damage = int(self.damage)
            target.fighter.take_damage(damage)
            self.engine.message_log.add_message(
                f"A lighting bolt strikes the {target.name} with a loud thunder, for {damage} damage!"
            )

        if len(self._targets) > 0:
            self.consume()
        else:
            raise Impossible("No enemy is close enough to strike.")

    def description(self) -> list[str]:
        return [f"Power: {self.damage}",
                f"Range: {self.maximum_range}"]


class FireballDamageConsumable(Consumable):
    def __init__(self, target: ConsumableTarget, damage: Range, radius: int,
                 consume_type: ConsumableType = ConsumableType.NONE):
        super().__init__(target, consume_type)
        self.damage = damage
        self._radius = radius

    @property
    def radius(self) -> int:
        return self._radius

    def activate(self, action: actions.ItemAction) -> None:
        if not self.engine.game_map.visible[action.target_xy]:
            raise Impossible("You cannot target an area that you cannot see.")

        for target in self._targets:
            damage = int(self.damage)
            target.fighter.take_damage(damage)
            self.engine.message_log.add_message(
                f"The {target.name} is engulfed in a fiery explosion, taking {damage} damage!"
            )

        if len(self._targets) > 0:
            self.consume()
        else:
            raise Impossible("No enemy in range.")

    def description(self) -> list[str]:
        return [f"Power: {self.damage}",
                f"Radius: {self.radius}"]


class ConfusionConsumable(Consumable):
    def __init__(self, target: ConsumableTarget, number_of_turns: int,
                 consume_type: ConsumableType = ConsumableType.NONE):
        super().__init__(target, consume_type)
        self.number_of_turns = number_of_turns

    def activate(self, action: actions.ItemAction) -> None:
        if not self.engine.game_map.visible[action.target_xy]:
            raise Impossible("You cannot target an area that you cannot see.")

        was = False
        for target in self._targets:
            if target is action.entity:
                continue
            was = True
            target.ai = components.ai.ConfusedEnemy(
                entity=target, previous_ai=target.ai, turns_remaining=self.number_of_turns,
            )
            self.engine.message_log.add_message(
                f"The eyes of the {target.name} look vacant, as it starts to stumble around!",
                color.status_effect_applied,
            )

        if was:
            self.consume()
        else:
            raise Impossible("No enemy is close enough to confuse.")

    def description(self) -> list[str]:
        return [f"Turns: {self.number_of_turns}"]


class MagicBook(Consumable):
    def __init__(self, mp: int, name: str, consumable: Consumable):
        super().__init__(consumable.targetType, ConsumableType.BOOK)
        self.mp = mp
        self.name = name
        self.consumable = consumable

        self.consumable.consume = self.consume
        self._parent = None
        self._consumer = None

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, value: Item) -> None:
        self._parent = value
        self.consumable.parent = value

    def consume(self) -> None:
        self._consumer.fighter.use_mana(self.mp)

    def get_action(self, consumer: Actor) -> Optional[ActionOrHandler]:
        if consumer.fighter.mp < self.mp:
            self.engine.message_log.add_message(
                f"Not enough mana to use this book, you need {self.mp} MP",
                color.mp_use
            )
            return None
        self.engine.message_log.add_message(
            f"You use {self.mp} MP and cast {self.name} spell",
            color.mp_use
        )
        self._consumer = consumer
        return self.consumable.get_action(consumer)

    def activate(self, action: actions.ItemAction) -> None:
        self.consumable.activate(action)

    def description(self) -> list[str]:
        data = [f"Mana usage: {self.mp}"]
        data.extend(self.consumable.description())
        return data


class Combine(Consumable):
    def __init__(self, consumables: list[Consumable], consume_type: ConsumableType = ConsumableType.NONE):
        target = max(consumables, key=attrgetter("targetType")).targetType
        super().__init__(target, consume_type)
        self.consumables = consumables

        self._parent = None
        self._consumer = None

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, value: Item) -> None:
        self._parent = value
        for consume in self.consumables:
            consume.parent = value

    def activate(self, action: actions.ItemAction) -> None:
        was = False
        for consume in self.consumables:
            consume._targets = self._targets
            try:
                consume.activate(action)
            except Impossible:
                pass
            else:
                was = True
        if not was:
            raise Impossible("No target or no effects")

    def description(self) -> list[str]:
        return list(chain.from_iterable(consume.description() for consume in self.consumables))
