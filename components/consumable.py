from __future__ import annotations

import random
from typing import Optional, TYPE_CHECKING
from operator import attrgetter
from itertools import chain

import actions
import color
import components.ai
import components.inventory
from components import effects
from components.base_component import BaseComponent
from exceptions import Impossible
from input_handlers import SingleRangedAttackHandler, AreaRangedAttackHandler, ActionOrHandler
from components_types import ConsumableTarget, ConsumableType
from ranged_value import Range

if TYPE_CHECKING:
    from entity import Actor, Item


class Consumable(BaseComponent):
    parent: Item

    def __init__(self, target: ConsumableTarget, consume_type: ConsumableType = ConsumableType.NONE,
                 effect: Optional[effects.Effect] = None, range: int = 0, radius: int = 0):
        self.targetType = target
        self.consumeType = consume_type
        self._targets: Optional[list[Actor]] = None
        self.effect = effect
        if self.effect is not None:
            self.effect.parent = self

        self._range = range
        self._radius = radius

    @property
    def range(self) -> int:
        return self._range

    @property
    def radius(self) -> int:
        return self._radius

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
        target = self.engine.game_map.get_actor_at_location_abs(*xy)
        return [target] if target else []

    def _get_ranged_targets(self, consumer: Actor, xy: tuple[int, int]) -> list[Actor]:
        targets = []
        for actor in self.engine.game_map.actors:
            if actor.distance(*xy) <= self.radius:
                targets.append(actor)
        return targets

    def activate(self, action: actions.ItemAction) -> None:
        was = False
        for target in self._targets:
            if self.effect is not None:
                was |= self.effect.apply(target, True)
        if was:
            self.consume()
        else:
            raise Impossible(f"{self.name} does not affect")

    def consume(self) -> None:
        """Remove the consumed item from its containing inventory."""
        entity = self.parent
        inventory = entity.parent
        if isinstance(inventory, components.inventory.Inventory) and entity in inventory.items:
            inventory.items.remove(entity)

    def description(self) -> list[str]:
        return self.effect.describe()

    @property
    def name(self) -> str:
        return self.parent.name


class Combine(Consumable):
    def __init__(self, consumables: list[Consumable], consume_type: ConsumableType = ConsumableType.NONE):
        target = max(consumables, key=attrgetter("targetType"))
        super().__init__(target.targetType, consume_type, effects.Combine([consume.effect for consume in consumables]))
        self._radius = getattr(target, "radius", 0)
        self._range = getattr(target, "range", 0)
        self.consumables = consumables

        self._parent = None
        self._consumer = None

        if any(type(consume).get_action != Consumable.get_action for consume in consumables):
            raise Impossible("BAD")

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


class MagicScroll(Consumable):
    def __init__(self, target: ConsumableTarget, name: str, effect: effects.Effect,
                 range: int = 0, radius: int = 0):
        super().__init__(target, ConsumableType.SCROLL, effect)
        self._name = name

        self._range = range
        self._radius = radius

    def description(self) -> list[str]:
        return self.effect.describe()


class MagicBook(Consumable):
    def __init__(self, target: ConsumableTarget, name: str, effect: effects.Effect, mp: int,
                 range: int = 0, radius: int = 0):
        super().__init__(target, ConsumableType.BOOK, effect)
        self._name = name
        self.mp = mp

        self._range = range
        self._radius = radius

        self._consumer: Optional[Actor] = None

    def description(self) -> list[str]:
        data = [f"Mana usage: {self.mp}"]
        data.extend(self.effect.describe())
        return data

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
            f"You use {self.mp} MP and cast {self._name} spell",
            color.mp_use
        )
        self._consumer = consumer
        return super().get_action(consumer)


class Potion(Consumable):
    def __init__(self, target: ConsumableTarget, effect: effects.Effect):
        super().__init__(target, ConsumableType.POTION, effect)
        self.effect = effect
        self.effect.parent = self

    def description(self) -> list[str]:
        return self.effect.describe()
