from __future__ import annotations

import copy
from itertools import chain
from typing import TYPE_CHECKING, Any, Union

import color
import components.ai
from combat import Damage
from entity import Actor

if TYPE_CHECKING:
    from .consumable import Consumable


class Effect:
    parent: Union[Consumable, Actor]

    def apply(self, actor: Actor, consume: bool) -> bool:
        raise NotImplementedError

    def describe(self) -> list[str]:
        raise NotImplementedError

    @property
    def copy(self) -> Effect:
        return copy.deepcopy(self)


class HealEffect(Effect):
    def __init__(self, amount):
        self.amount = amount

    def apply(self, actor: Actor, consume: bool) -> bool:
        engine = actor.parent.engine
        amount_recovered = actor.fighter.heal(self.amount)
        if actor == engine.player and consume:
            engine.message_log.add_message(
                f"You consume the {self.parent.name}, and recover {amount_recovered} HP!",
                color.health_recovered,
            )

        return bool(amount_recovered)

    def describe(self) -> list[str]:
        return [f"Heal amount: {self.amount}"]


class RestoreManaEffect(Effect):
    def __init__(self, amount):
        self.amount = amount

    def apply(self, actor: Actor, consume: bool) -> bool:
        engine = actor.parent.engine
        amount_recovered = actor.fighter.restore_mana(self.amount)
        if actor == engine.player and consume:
            engine.message_log.add_message(
                f"You consume the {self.parent.name}, and recover {amount_recovered} MP!",
                color.health_recovered,
            )

        return bool(amount_recovered)

    def describe(self) -> list[str]:
        return [f"Restore mana: {self.amount}"]


class DamageEffect(Effect):
    def __init__(self, damage: Damage):
        self.damage = damage

    def apply(self, actor: Actor, consume: bool) -> bool:
        engine = actor.parent.engine
        value = self.damage.attack(actor.fighter.defense)
        if value <= 0:
            engine.message_log.add_message(
                f"No damage for {actor.name}"
            )
            return False
        if self.parent != actor:
            engine.message_log.add_message(
                f"{self.parent.name} strike {actor.name} with {self.damage.type.name.lower()} damage {value}"
            )
        else:
            engine.message_log.add_message(
                f"{self.parent.name} takes {self.damage.type.name.lower()} damage {value}"
            )
        return actor.fighter.take_damage(value)

    def describe(self) -> list[str]:
        return [f"{self.damage.type.name.title()} damage: {self.damage.value}"]


class AddConfusionEffect(Effect):
    def __init__(self, turns: int):
        self.turns = turns

    def apply(self, actor: Actor, consume: bool) -> bool:
        engine = actor.parent.engine
        if not actor.is_alive:
            return False
        if isinstance(actor.ai, components.ai.ConfusedEnemy):
            actor.ai.turns_remaining += self.turns
        else:
            actor.ai = components.ai.ConfusedEnemy(
                entity=actor, previous_ai=actor.ai, turns_remaining=self.turns,
            )
        engine.message_log.add_message(
            f"The eyes of the {actor.name} look vacant, as it starts to stumble around!",
            color.status_effect_applied,
        )
        return True

    def describe(self) -> list[str]:
        return [f"Confuse turns: {self.turns}"]


class Combine(Effect):
    def __init__(self, effects: list[Effect] = None):
        self.effects = effects or []
        self._parent = None

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, value):
        self._parent = value
        for effect in self.effects:
            effect.parent = value

    def apply(self, actor: Actor, consume: bool) -> bool:
        was = False
        for effect in self.effects:
            was |= effect.apply(actor, True)
        return was

    def describe(self) -> list[str]:
        return list(chain.from_iterable(effect.describe() for effect in self.effects))


class DurableEffect(Effect):
    def __init__(self, turn: int, effect: Effect):
        self.turns = turn
        self.effect = effect
        self._parent = None

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, value):
        self._parent = value
        self.effect.parent = value

    def describe(self) -> list[str]:
        return [
            f"Turns: {self.turns if self.turns > 0 else 'permanent'}",
            *self.effect.describe()
        ]

    def apply(self, actor: Actor, consume: bool) -> bool:
        parent = self.parent
        if not isinstance(parent, Actor):
            return False

        if self.turns == 0:
            parent.effects.remove(self)
            return False

        if self.turns > 0:
            self.turns -= 1
        self.effect.apply(actor, consume)
        return True


class AddEffect(Effect):
    def __init__(self, effect: Effect):
        self.effect = effect

    def apply(self, actor: Actor, consume: bool) -> bool:
        engine = actor.parent.engine
        if actor.is_alive:
            actor.add_effect(self.effect.copy)
            if consume:
                engine.message_log.add_message(
                    f"You consume the {self.parent.name}, effect: {' '.join(self.effect.describe())}",
                    color.health_recovered,
                )

        return actor.is_alive

    def describe(self) -> list[str]:
        return ["Add effect:", *self.effect.describe()]
