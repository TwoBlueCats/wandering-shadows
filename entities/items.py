from combat import Damage, DamageType
from components import consumable, effects
from components_types import ConsumableTarget as Target, ConsumableType
from entities.factory import ItemFactory
from ranged_value import Range


def effect_level_up(effect: effects.Effect, floor: int, base: int):
    match effect:
        case effects.HealEffect(amount=amount):
            effect.amount += (floor - base) * amount // 5 // 10
        case effects.RestoreManaEffect(amount=amount):
            effect.amount += (floor - base) * amount // 5 // 10
        case effects.DurableEffect(effect=next_effect, turns=turns):
            effect.turns += (floor - base) // 5 * turns // 10
            effect_level_up(next_effect, floor, base)
        case effects.Combine(effects=used_effects):
            for next_effect in used_effects:
                effect_level_up(next_effect, floor, base)


def potion_level_up(item, floor, base):
    assert item.consumable is not None
    effect_level_up(item.consumable.effect, floor, base)


health_potion = ItemFactory(
    char="&",
    color=(127, 0, 255),
    name="Health Potion",
    consume=consumable.Potion(target=Target.SELF, effect=effects.HealEffect(40)),
    fit_to_level=potion_level_up,
)
mana_potion = ItemFactory(
    char="&",
    color=(0, 0, 255),
    name="Mana Potion",
    consume=consumable.Potion(target=Target.SELF, effect=effects.RestoreManaEffect(10)),
    fit_to_level=potion_level_up,
)
universal_potion = ItemFactory(
    char="&",
    color=(64, 0, 255),
    name="Universal Potion",
    consume=consumable.Potion(target=Target.SELF, effect=effects.Combine([
        effects.HealEffect(amount=40),
        effects.RestoreManaEffect(amount=20),
    ])),
    fit_to_level=potion_level_up,
    base_floor=6,
)
regeneration_potion = ItemFactory(
    char="&",
    color=(3, 192, 60),
    name="Regeneration Potion",
    consume=consumable.Potion(target=Target.SELF, effect=effects.AddEffect(
        effects.DurableEffect(10, effects.HealEffect(4))
    )),
    fit_to_level=potion_level_up,
)

poison_scroll = ItemFactory(
    char="-",
    color=(128, 30, 70),
    name="Poisoned bolt",
    consume=consumable.Consumable(
        target=Target.NEAREST, range=5,
        effect=effects.AddEffect(
            effects.DurableEffect(5, effects.DamageEffect(Damage(Range(3, 4), DamageType.POISON)))),
    ),
)
lightning_scroll = ItemFactory(
    char="~",
    color=(255, 255, 0),
    name="Lightning Scroll",
    consume=consumable.MagicScroll(
        target=Target.NEAREST, name="Lightning", range=5,
        effect=effects.DamageEffect(Damage(Range(10, 30), DamageType.LIGHTNING)),
    ),
)
fireball_scroll = ItemFactory(
    char="~",
    color=(255, 0, 0),
    name="Fireball Scroll",
    consume=consumable.MagicScroll(
        target=Target.RANGED, name="Fireball", radius=5,
        effect=effects.Combine([
            effects.DamageEffect(Damage(Range(10, 15), DamageType.FIRE)),
            effects.AddConfusionEffect(1),
        ])
    ),
)
firebolt_scroll = ItemFactory(
    char="~",
    color=(255, 0, 0),
    name="Firebolt Scroll",
    consume=consumable.MagicScroll(
        target=Target.RANDOM, name="Firebolt", range=5,
        effect=effects.DamageEffect(Damage(Range(15, 20), DamageType.FIRE)),
    ),
)
confusion_scroll = ItemFactory(
    char="~",
    color=(207, 63, 255),
    name="Confusion Scroll",
    consume=consumable.MagicScroll(
        target=Target.SELECTED, name="Confusion", range=5,
        effect=effects.AddConfusionEffect(10),
    ),
)
healing_book = ItemFactory(
    char="#",
    color=(127, 0, 255),
    name="Magic book: Health",
    consume=consumable.MagicBook(
        target=Target.SELF,
        mp=20,
        name="healing",
        effect=effects.HealEffect(40),
    ),
    fit_to_level=potion_level_up
)
lightning_book = ItemFactory(
    char="#",
    color=(255, 255, 0),
    name="Magic book: Lighting",
    consume=consumable.MagicBook(
        target=Target.NEAREST,
        mp=30,
        name="lightning",
        effect=effects.DamageEffect(Damage(Range(25, 30), DamageType.LIGHTNING)),
        range=4
    ),
)
fireball_book = ItemFactory(
    char="#",
    color=(255, 0, 0),
    name="Magic book: Fireball",
    consume=consumable.MagicBook(
        target=Target.RANGED,
        mp=40,
        name="fireball",
        effect=effects.Combine([
            effects.DamageEffect(Damage(Range(25, 35), DamageType.FIRE)),
            effects.AddConfusionEffect(1),
        ]),
        radius=3
    ),
)
confusion_book = ItemFactory(
    char="#",
    color=(207, 63, 255),
    name="Magic book: Confusion",
    consume=consumable.MagicBook(
        target=Target.SELECTED,
        mp=20,
        name="confusion",
        effect=effects.AddConfusionEffect(5)
    ),
)
