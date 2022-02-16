import traceback
import sys

import tcod
import tcod.render
import tcod.sdl.render

import color
from config import Config
import exceptions
import input_handlers
import setup_game


def save_game(handler: input_handlers.BaseEventHandler, filename: str) -> None:
    """If the current event handler has an active Engine then save it."""
    if isinstance(handler, input_handlers.EventHandler):
        handler.engine.save_as(filename)
        print("Game saved.")


def main() -> None:
    tile_set = tcod.tileset.load_tilesheet(
        "fonts/lucida12x12_gs_tc.png", 32, 8, tcod.tileset.CHARMAP_TCOD
    )

    handler: input_handlers.BaseEventHandler = setup_game.MainMenu()

    if "debug" in sys.argv:
        Config.DEBUG = True

    with tcod.context.new_terminal(
            Config.screen.width,
            Config.screen.height,
            tileset=tile_set,
            title="Roguelike by Nightraven",
            vsync=True,
    ) as context:
        root_console = tcod.Console(Config.screen.width, Config.screen.height, order="F")
        if context.sdl_renderer:  # If this context supports SDL rendering.
            # Start by setting the logical size so that window resizing doesn't break anything.
            context.sdl_renderer.logical_size = (
                tile_set.tile_width * root_console.width,
                tile_set.tile_height * root_console.height,
            )
            assert context.sdl_atlas
            # Generate the console renderer and minimap.
            console_render = tcod.render.SDLConsoleRender(context.sdl_atlas)

        try:
            while True:
                root_console.clear()
                handler.on_render(console=root_console)
                if context.sdl_renderer and hasattr(handler, "engine"):
                    engine = getattr(handler, "engine")
                    minimap = context.sdl_renderer.new_texture(
                        engine.game_map.width,
                        engine.game_map.height,
                        format=tcod.lib.SDL_PIXELFORMAT_RGB24,
                        access=tcod.sdl.render.TextureAccess.STREAMING,  # Updated every frame.
                    )
                    # SDL renderer support, upload the sample console background to a minimap texture.
                    minimap.update(engine.game_map.tiles_rgb[:].T["bg"])
                    # Render the root_console normally, this is the drawing step of context.present without presenting.
                    context.sdl_renderer.copy(console_render.render(root_console))
                    # Render the minimap to the screen.
                    context.sdl_renderer.copy(
                        minimap,
                        dest=(
                            Config.minimap_x * tile_set.tile_width,
                            Config.minimap_y * tile_set.tile_height,
                            Config.minimap_x_size * tile_set.tile_width,
                            Config.minimap_y_size * tile_set.tile_height,
                        ),
                    )
                    context.sdl_renderer.present()
                else:  # No SDL renderer, just use plain context rendering.
                    context.present(root_console)

                try:
                    for event in tcod.event.wait():
                        context.convert_event(event)
                        handler = handler.handle_events(event)
                except Exception:  # Handle exceptions in game.
                    traceback.print_exc()  # Print error to stderr.
                    # Then print the error to the message log.
                    if isinstance(handler, input_handlers.EventHandler):
                        handler.engine.message_log.add_message(
                            traceback.format_exc(), color.error
                        )
        except exceptions.QuitWithoutSaving:
            raise
        except SystemExit:  # Save and quit.
            save_game(handler, Config.save_name)
            raise
        except BaseException:  # Save on any other unexpected exception.
            save_game(handler, Config.save_name)
            raise


if __name__ == "__main__":
    main()
