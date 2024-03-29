from __future__ import annotations

import math
import os
from itertools import chain
from typing import Optional, Type, TYPE_CHECKING, Callable, Union

import tcod.event

import render_utils
import texts
from actions import (
    Action,
    DirectedActionDispatcher,
    WaitAction,
    PickupAction,
    DropItem,
    TakeStairsAction,
    EquipAction,
    ImpossibleAction,
    PlaceTorchAction,
)
import color
import exceptions
from config import Config
from components_types import ConsumableType
from combat import DamageType, DefenseType

if TYPE_CHECKING:
    from engine import Engine
    from entity import Item, Entity

MOVE_KEYS = {
    # Arrow keys.
    tcod.event.K_UP: (0, -1),
    tcod.event.K_DOWN: (0, 1),
    tcod.event.K_LEFT: (-1, 0),
    tcod.event.K_RIGHT: (1, 0),
    tcod.event.K_HOME: (-1, -1),
    tcod.event.K_END: (-1, 1),
    tcod.event.K_PAGEUP: (1, -1),
    tcod.event.K_PAGEDOWN: (1, 1),
    # Numpad keys.
    tcod.event.K_KP_1: (-1, 1),
    tcod.event.K_KP_2: (0, 1),
    tcod.event.K_KP_3: (1, 1),
    tcod.event.K_KP_4: (-1, 0),
    tcod.event.K_KP_6: (1, 0),
    tcod.event.K_KP_7: (-1, -1),
    tcod.event.K_KP_8: (0, -1),
    tcod.event.K_KP_9: (1, -1),
    # Vi keys.
    tcod.event.K_h: (-1, 0),
    tcod.event.K_j: (0, 1),
    tcod.event.K_k: (0, -1),
    tcod.event.K_l: (1, 0),
    tcod.event.K_y: (-1, -1),
    tcod.event.K_u: (1, -1),
    tcod.event.K_b: (-1, 1),
    tcod.event.K_n: (1, 1),
}

WAIT_KEYS = {
    tcod.event.K_PERIOD,
    tcod.event.K_KP_5,
    tcod.event.K_z,
}

CONFIRM_KEYS = {
    tcod.event.K_RETURN,
    tcod.event.K_KP_ENTER,
}

SLOT_KEYS = set(tcod.event.K_0 + i for i in range(1, 10))

ActionOrHandler = Union[Action, "BaseEventHandler"]
"""An event handler return value which can trigger an action or switch active handlers.

If a handler is returned then it will become the active handler for future events.
If an action is returned it will be attempted and if it's valid then
MainGameEventHandler will become the active handler.
"""


class BaseEventHandler(tcod.event.EventDispatch[ActionOrHandler]):
    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle an event and return the next active event handler."""
        state = self.dispatch(event)
        if isinstance(state, BaseEventHandler):
            return state
        assert not isinstance(state, Action), f"{self!r} can not handle actions."
        return self

    def on_render(self, console: tcod.Console) -> None:
        raise NotImplementedError()

    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        raise SystemExit()


class PopupMessage(BaseEventHandler):
    """Display a popup text window."""

    def __init__(self, parent_handler: BaseEventHandler, text: str):
        self.parent = parent_handler
        self.text = text

    def on_render(self, console: tcod.Console) -> None:
        """Render the parent and dim the result, then print the message on top."""
        self.parent.on_render(console)
        console.tiles_rgb["fg"] //= 8
        console.tiles_rgb["bg"] //= 8

        console.print(
            console.width // 2,
            console.height // 2,
            self.text,
            fg=color.white,
            bg=color.black,
            alignment=tcod.CENTER,
        )

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[BaseEventHandler]:
        """Any key returns to the parent handler."""
        return self.parent


class EventHandler(BaseEventHandler):
    def __init__(self, engine: Engine):
        self.engine = engine

    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle events for input handlers with an engine."""
        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, BaseEventHandler):
            return action_or_state
        if self.handle_action(action_or_state):
            # A valid action was performed.
            if not self.engine.player.is_alive:
                # The player was killed sometime during or after the action.
                return GameOverEventHandler(self.engine)
            elif self.engine.player.level.requires_level_up:
                self.engine.player.fighter.stats.remains += 1
                self.engine.player.level.increase_level()
                return LevelUpEventHandler(self.engine)
            return MainGameEventHandler(self.engine)  # Return to the main handler.
        return self

    def handle_action(self, action: Optional[Action]) -> bool:
        """Handle actions returned from event methods.

        Returns True if the action will advance a turn.
        """
        if action is None:
            return False
        affected = action.entity.apply_effects()

        try:
            action.perform()
        except exceptions.Impossible as exc:
            self.engine.message_log.add_message(exc.args[0], color.impossible)
            return affected  # Skip enemy turn on exceptions.

        self.engine.handle_enemy_turns()

        self.engine.update_fov()
        return True

    def on_render(self, console: tcod.Console) -> None:
        self.engine.render(console)

    def ev_mousemotion(self, event: tcod.event.MouseMotion) -> None:
        if self.engine.game_map.in_bounds(event.tile.x, event.tile.y):
            self.engine.mouse_location = event.tile.x, event.tile.y


class AskUserEventHandler(EventHandler):
    """Handles user input for actions which require special input."""

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """By default any key exits this input handler."""
        if event.sym in {  # Ignore modifier keys.
            tcod.event.K_LSHIFT,
            tcod.event.K_RSHIFT,
            tcod.event.K_LCTRL,
            tcod.event.K_RCTRL,
            tcod.event.K_LALT,
            tcod.event.K_RALT,
        }:
            return None
        return self.on_exit()

    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> Optional[ActionOrHandler]:
        """By default, any mouse click exits this input handler."""
        return self.on_exit()

    def on_exit(self) -> Optional[ActionOrHandler]:
        """Called when the user is trying to exit or cancel an action.

        By default this returns to the main event handler.
        """
        return MainGameEventHandler(self.engine)


class CharacterScreenEventHandler(AskUserEventHandler):
    TITLE = "Character Information"

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        x = render_utils.get_render_x_pos(self.engine)
        y = Config.data_top_y
        width = Config.overlay_width

        player = self.engine.player
        messages = [
            f"Level: {player.level.current_level}",
            ""
            f"XP: {player.level.current_xp}",
            f"XP for next Level: {player.level.experience_to_next_level}",
            "",
            f"Attack: {player.fighter.power}",
            "",
            "Defense:",
            *player.fighter.defense.describe(),
            "",
            f"Inventory: {len(player.inventory.items)}/{player.inventory.capacity}",
            "",
            "Base characteristics:",
            *player.fighter.stats.describe(),
        ]
        if player.fighter.stats.remains != 0:
            messages.append("")
            messages.append(f"Points remain: {player.fighter.stats.remains}")
        if player.effects:
            messages.extend(("", "Effects:"))
            messages.extend(chain.from_iterable(effect.describe() for effect in player.effects))

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=len(messages) + 2,
            title=self.TITLE,
            clear=True,
            fg=color.white,
            bg=color.black,
        )

        console.print(
            x=x + 1, y=y + 1, string="\n".join(messages)
        )


class ControlScreenEventHandler(AskUserEventHandler):
    TITLE = "Controls"

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        x = Config.overlay_left_x
        y = 0
        width = Config.overlay_width
        height = 10

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title="Movement",
            clear=True,
            fg=color.white,
            bg=color.black,
        )

        for i, (k, t) in enumerate([(tcod.event.K_UP, "UP        or k"),
                                    (tcod.event.K_DOWN, "DOWN      or j"),
                                    (tcod.event.K_LEFT, "LEFT      or h"),
                                    (tcod.event.K_RIGHT, "RIGHT     or l"),
                                    (tcod.event.K_HOME, "HOME      or y"),
                                    (tcod.event.K_END, "END       or b"),
                                    (tcod.event.K_PAGEUP, "PAGE UP   or u"),
                                    (tcod.event.K_PAGEDOWN, "PAGE DOWN or n"),
                                    ]):
            console.print(
                x=x + 1, y=y + i + 1,
                string=f"Key {t} moves {texts.MOVE_DIRECTIONS[MOVE_KEYS[k]]}"
            )

        y += height + 1
        height = 3
        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title="Wait",
            clear=True,
            fg=color.white,
            bg=color.black,
        )
        console.print(
            x=x + 1, y=y + 1,
            string=f"Press key PERIOD or z for {texts.WAIT}"
        )

        y += height + 1
        height = 3
        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title="Confirm selection",
            clear=True,
            fg=color.white,
            bg=color.black,
        )
        console.print(
            x=x + 1, y=y + 1,
            string=f"Press key ENTER for {texts.CONFIRM}"
        )

        x = Config.overlay_right_x
        y = 0
        height = 11
        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title="Inventory",
            clear=True,
            fg=color.white,
            bg=color.black,
        )
        console.print(x=x + 1, y=y + 1, string=f"Press key g to pick up item")
        console.print(x=x + 1, y=y + 2, string=f"Press key i to use inventory items")
        console.print(x=x + 1, y=y + 3, string=f"Press key d to drop inventory items")
        console.print(x=x + 1, y=y + 4, string=f"Press key e to explore inventory items")
        console.print(x=x + 1, y=y + 5, string=f"Press key m to see only magic items")
        console.print(x=x + 1, y=y + 6, string=f"Press key p to see only potions")
        console.print(x=x + 1, y=y + 7, string=f"Press key q to see only equipment")
        console.print(x=x + 1, y=y + 8, string=f"Press key a-z to select inventory item")
        console.print(x=x + 1, y=y + 9, string=f"Press any other key to exit")

        y += height + 1
        height = 5
        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title="Other",
            clear=True,
            fg=color.white,
            bg=color.black,
        )
        console.print(x=x + 1, y=y + 1, string=f"Press key c to show character screen")
        console.print(x=x + 1, y=y + 3, string=f"Press key x to use stats points")
        console.print(x=x + 1, y=y + 2, string=f"Press key s to show this settings")


class LevelUpEventHandler(AskUserEventHandler):
    TITLE = "Level Up"

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        x = render_utils.get_render_x_pos(self.engine)
        y = Config.data_top_y

        console.draw_frame(
            x=x,
            y=y,
            width=Config.overlay_width,
            height=11,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        console.print(x=x + 1, y=y + 1, string="Congratulations! You level up!")
        console.print(x=x + 1, y=y + 2, string="Select an attribute to increase.")

        for index, stat in enumerate(self.engine.player.stats.base_stats_names):
            key = chr(ord("a") + index)
            console.print(
                x=x + 1,
                y=y + 4 + index,
                string=f"{key}) {stat.title()} (from {self.engine.player.fighter.stats.get_stat(stat)})",
            )

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        player = self.engine.player
        key = event.sym
        index = key - tcod.event.K_a

        if 0 <= index <= len(player.fighter.stats.base_stats_names):
            player.level.increase_stat(player.fighter.stats.base_stats_names[index])
        elif event.sym != tcod.event.K_ESCAPE:
            self.engine.message_log.add_message("Invalid entry.", color.invalid)
            return None

        return super().ev_keydown(event)

    def ev_mousebuttondown(
            self, event: tcod.event.MouseButtonDown
    ) -> Optional[ActionOrHandler]:
        """
        Don't allow the player to click to exit the menu, like normal.
        """
        return None


def use_selected_item(handler, item: Item) -> Optional[ActionOrHandler]:
    """Return the action for the selected item."""
    if item is None:
        return ImpossibleAction(handler.engine.player, "No item selected")
    if item.consumable:
        return item.consumable.get_action(handler.engine.player)
    elif item.equippable:
        return EquipAction(handler.engine.player, item)
    else:
        return None


class FilteredActivateHandler(AskUserEventHandler):
    TITLE = "<missing title>"

    def __init__(self, engine: Engine, title: str = None, filter: Callable[[Item], bool] = None):
        super().__init__(engine)
        self._filtered: list[Item] = []
        self.filter = filter
        if title is not None:
            self.TITLE = title
        self.page = 0
        self.line = None

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        x = render_utils.get_render_x_pos(self.engine)
        y = 0
        width = Config.overlay_width

        self._filtered = list(filter(self.filter, self.engine.player.inventory.items))

        height = 5 + len(self._filtered[self.page * 26: (self.page + 1) * 26])
        if height <= 5:
            height = 5

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title=self.TITLE,
            clear=True,
            fg=color.white,
            bg=color.black,
        )

        console.print(x + 1, y + 1, f"Page: {self.page + 1}/{max(1, math.ceil(len(self._filtered) / 26))}")
        if len(self._filtered) > 0:
            render_utils.render_items_list(
                console,
                self._filtered[self.page * 26: (self.page + 1) * 26],
                self.engine.player.equipment,
                x, y + 2,
                line=self.line,
                slots=self.engine.player.inventory.slots,
            )
        else:
            console.print(x + 1, y + 3, "(Empty)")

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        key = event.sym
        index = key - tcod.event.K_a

        if key == tcod.event.K_LEFT:
            self.page = max(0, self.page - 1)
            self.line = None
            return
        if key == tcod.event.K_RIGHT:
            max_page = max(1, math.ceil(len(self._filtered) / 26)) - 1
            self.page = min(max_page, self.page + 1)
            self.line = None
            return
        if key == tcod.event.K_DOWN:
            self.line = self.line if self.line is not None else -1
            self.line = min(len(self._filtered) - self.page * 26 - 1, self.line + 1)
            return
        if key == tcod.event.K_UP:
            self.line = self.line if self.line is not None else min(len(self._filtered) - self.page * 26, 26)
            self.line = max(0, self.line - 1)
            return

        if key in CONFIRM_KEYS:
            if self.line is None:
                self.engine.message_log.add_message("Invalid entry.", color.invalid)
                return None
            return self.on_item_selected(self._filtered[self.line + self.page * 26])

        if key in SLOT_KEYS:
            if self.line is None:
                return
            place = key - tcod.event.K_1
            val = None
            item = self._filtered[self.line + self.page * 26]
            if item in self.engine.player.inventory.slots:
                val = self.engine.player.inventory.slots.index(item)
                self.engine.player.inventory.slots[val] = None
            if place != val:
                self.engine.player.inventory.slots[place] = item

        if 0 <= index <= 26:
            index += self.page * 26
            selected_item: Optional[Item] = None
            if index < len(self._filtered):
                selected_item = self._filtered[index]
            if selected_item is None:
                self.engine.message_log.add_message("Invalid entry.", color.invalid)
                return None
            return self.on_item_selected(selected_item)
        return super().ev_keydown(event)

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        return use_selected_item(self, item)


class InventoryActivateHandler(FilteredActivateHandler):
    """Handle using an inventory item."""

    TITLE = "Select an item to use"

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        """Return the action for the selected item."""
        if item.consumable:
            # Return the action for the selected item.
            return item.consumable.get_action(self.engine.player)
        elif item.equippable:
            return EquipAction(self.engine.player, item)
        else:
            return None


class InventoryDropHandler(FilteredActivateHandler):
    """Handle dropping an inventory item."""

    TITLE = "Select an item to drop"

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        """Drop this item."""
        return DropItem(self.engine.player, item)


class InventoryExploreHandler(FilteredActivateHandler):
    TITLE = "Select item to explore"

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        return EntityDescriptionHandler(self.engine, item, previous=InventoryExploreHandler)


class EntityDescriptionHandler(AskUserEventHandler):
    TITLE = "Entity characters"

    def __init__(self, engine: Engine, entity: Entity, previous: Optional[Type[EventHandler]] = None):
        super().__init__(engine)
        self.entity = entity
        self.previous = previous

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        x = render_utils.get_render_x_pos(self.engine)
        y = Config.data_top_y
        width = Config.overlay_width

        messages = self.entity.description()

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=len(messages) + 2,  # top & bottom borders
            title=self.TITLE,
            clear=True,
            fg=color.white,
            bg=color.black,
        )

        console.print(
            x=x + 1, y=y + 1, string="\n".join(messages)
        )

    def on_exit(self) -> Optional[ActionOrHandler]:
        if self.previous:
            return self.previous(self.engine)
        return MainGameEventHandler(self.engine)


class SelectIndexHandler(AskUserEventHandler):
    """Handles asking the user for an index on the map."""

    def __init__(self, engine: Engine):
        """Sets the cursor to the player when this handler is constructed."""
        super().__init__(engine)
        player = self.engine.player
        engine.mouse_location = engine.game_map.get_location_rel(player.x, player.y)

    def on_render(self, console: tcod.Console) -> None:
        """Highlight the tile under the cursor."""
        super().on_render(console)
        x, y = self.engine.mouse_location
        console.tiles_rgb["bg"][x + Config.sample_map_x, y + Config.sample_map_y] = color.white
        console.tiles_rgb["fg"][x + Config.sample_map_x, y + Config.sample_map_y] = color.black

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """Check for key movement or confirmation keys."""
        key = event.sym
        if key in MOVE_KEYS:
            modifier = 1  # Holding modifier keys will speed up key movement.
            if event.mod & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT):
                modifier *= 5
            if event.mod & (tcod.event.KMOD_LCTRL | tcod.event.KMOD_RCTRL):
                modifier *= 10
            if event.mod & (tcod.event.KMOD_LALT | tcod.event.KMOD_RALT):
                modifier *= 20

            x, y = self.engine.mouse_location
            dx, dy = MOVE_KEYS[key]
            x += dx * modifier
            y += dy * modifier
            # Clamp the cursor index to the map size.
            x = max(Config.sample_map_x, min(x, Config.sample_map_x + Config.sample_map_width - 1))
            y = max(Config.sample_map_y, min(y, Config.sample_map_y + Config.sample_map_height - 1))
            self.engine.mouse_location = x, y
            return None
        elif key in CONFIRM_KEYS:
            return self.on_index_selected(*self.engine.mouse_location)
        return super().ev_keydown(event)

    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> Optional[ActionOrHandler]:
        """Left click confirms a selection."""
        if self.engine.game_map.in_bounds(*event.tile):
            if event.button == 1:
                return self.on_index_selected(*event.tile)
        return super().ev_mousebuttondown(event)

    def on_index_selected(self, x: int, y: int) -> Optional[ActionOrHandler]:
        """Called when an index is selected."""
        raise NotImplementedError()


class LookHandler(SelectIndexHandler):
    """Lets the player look around using the keyboard."""

    def on_index_selected(self, x: int, y: int) -> Optional[ActionOrHandler]:
        """Return to main handler."""
        game_map = self.engine.game_map
        entity = list(game_map.get_entities_at_location(*game_map.get_location_abs(x, y)))
        if len(entity) > 0:
            return EntityDescriptionHandler(self.engine, entity[0], LookHandler)
        return MainGameEventHandler(self.engine)


class SingleRangedAttackHandler(SelectIndexHandler):
    """Handles targeting a single enemy. Only the enemy selected will be affected."""

    def __init__(self, engine: Engine, callback: Callable[[tuple[int, int]], Optional[ActionOrHandler]]):
        super().__init__(engine)

        self.callback = callback

    def on_index_selected(self, x: int, y: int) -> Optional[ActionOrHandler]:
        return self.callback((x, y))


class AreaRangedAttackHandler(SelectIndexHandler):
    """Handles targeting an area within a given radius. Any entity within the area will be affected."""

    def __init__(
            self,
            engine: Engine,
            radius: int,
            callback: Callable[[tuple[int, int]], Optional[ActionOrHandler]],
    ):
        super().__init__(engine)

        self.radius = radius
        self.callback = callback

    def on_render(self, console: tcod.Console) -> None:
        """Highlight the tile under the cursor."""
        super().on_render(console)

        x, y = self.engine.mouse_location

        # Draw a rectangle around the targeted area, so the player can see the affected tiles.
        console.draw_frame(
            x=x - self.radius - 1,
            y=y - self.radius - 1,
            width=self.radius * 2 + 3,
            height=self.radius * 2 + 3,
            fg=color.red,
            clear=False,
        )

    def on_index_selected(self, x: int, y: int) -> Optional[ActionOrHandler]:
        return self.callback((x, y))


class MainGameEventHandler(EventHandler):
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        action: Optional[Action] = None

        key = event.sym
        modifier = event.mod

        player = self.engine.player

        if key == tcod.event.K_PERIOD and modifier & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT):
            return TakeStairsAction(player)

        if key in MOVE_KEYS:
            dx, dy = MOVE_KEYS[key]
            action = DirectedActionDispatcher(player, dx, dy, modifier)
        elif key in SLOT_KEYS:
            return use_selected_item(self, self.engine.player.inventory.slots[key - tcod.event.K_1])
        elif key in WAIT_KEYS:
            action = WaitAction(player)
        elif key == tcod.event.K_ESCAPE:
            raise SystemExit()
        elif key == tcod.event.K_v:
            return HistoryViewer(self.engine)
        elif key == tcod.event.K_g:
            action = PickupAction(player)
        elif key == tcod.event.K_i:
            return InventoryActivateHandler(self.engine)
        elif key == tcod.event.K_d:
            return InventoryDropHandler(self.engine)
        elif key == tcod.event.K_SLASH:
            return LookHandler(self.engine)
        elif key == tcod.event.K_c:
            return CharacterScreenEventHandler(self.engine)
        elif key == tcod.event.K_s:
            return ControlScreenEventHandler(self.engine)
        elif key == tcod.event.K_e:
            return InventoryExploreHandler(self.engine)
        elif key == tcod.event.K_m:
            def filter(item: Item) -> bool:
                if item.consumable is None:
                    return False
                return item.consumable.consumeType in (ConsumableType.BOOK | ConsumableType.SCROLL)

            return FilteredActivateHandler(self.engine, "Magic items list", filter)
        elif key == tcod.event.K_p:
            def filter(item: Item) -> bool:
                if item.consumable is None:
                    return False
                return item.consumable.consumeType in ConsumableType.POTION

            return FilteredActivateHandler(self.engine, "Potion list", filter)
        elif key == tcod.event.K_q:
            def filter(item: Item) -> bool:
                return item.equippable is not None

            return FilteredActivateHandler(self.engine, "Equipment items list", filter)
        elif key == tcod.event.K_x:
            if self.engine.player.fighter.stats.remains > 0:
                return LevelUpEventHandler(self.engine)
            else:
                self.engine.message_log.add_message("No points to use.", color.invalid)
                return
        elif key == tcod.event.K_t:
            return PlaceTorchAction(player)

        # No valid key was pressed
        return action


class GameOverEventHandler(EventHandler):
    def on_quit(self) -> None:
        """Handle exiting out of a finished game."""
        if os.path.exists(Config.save_name):
            os.remove(Config.save_name)  # Deletes the active save file.
        raise exceptions.QuitWithoutSaving()  # Avoid saving a finished game.

    def ev_quit(self, event: tcod.event.Quit) -> None:
        self.on_quit()

    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        if event.sym == tcod.event.K_ESCAPE:
            self.on_quit()


CURSOR_Y_KEYS = {
    tcod.event.K_UP: -1,
    tcod.event.K_DOWN: 1,
    tcod.event.K_PAGEUP: -10,
    tcod.event.K_PAGEDOWN: 10,
}


class HistoryViewer(EventHandler):
    """Print the history on a larger window which can be navigated."""

    def __init__(self, engine: Engine):
        super().__init__(engine)
        self.log_length = len(engine.message_log.messages)
        self.cursor = self.log_length - 1

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)  # Draw the main state as the background.

        log_console = tcod.Console(console.width - 6, console.height - 6)

        # Draw a frame with a custom banner title.
        log_console.draw_frame(0, 0, log_console.width, log_console.height)
        log_console.print_box(
            0, 0, log_console.width, 1, "┤Message history├", alignment=tcod.CENTER
        )

        # Render the message log using the cursor parameter.
        self.engine.message_log.render_messages(
            log_console,
            1,
            1,
            log_console.width - 2,
            log_console.height - 2,
            self.engine.message_log.messages[: self.cursor + 1],
        )
        log_console.blit(console, 3, 3)

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[MainGameEventHandler]:
        # Fancy conditional movement to make it feel right.
        if event.sym in CURSOR_Y_KEYS:
            adjust = CURSOR_Y_KEYS[event.sym]
            if adjust < 0 and self.cursor == 0:
                # Only move from the top to the bottom when you're on the edge.
                self.cursor = self.log_length - 1
            elif adjust > 0 and self.cursor == self.log_length - 1:
                # Same with bottom to top movement.
                self.cursor = 0
            else:
                # Otherwise, move while staying clamped to the bounds of the history log.
                self.cursor = max(0, min(self.cursor + adjust, self.log_length - 1))
        elif event.sym == tcod.event.K_HOME:
            self.cursor = 0  # Move directly to the top message.
        elif event.sym == tcod.event.K_END:
            self.cursor = self.log_length - 1  # Move directly to the last message.
        else:  # Any other key moves back to the main game state.
            return MainGameEventHandler(self.engine)
