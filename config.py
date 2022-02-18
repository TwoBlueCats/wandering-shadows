from dataclasses import dataclass


class ScreenConfig:
    width = 120
    height = 80


@dataclass
class MapConfig:
    width: int
    height: int

    room_max_size: int = 10
    room_min_size: int = 6
    max_rooms: int = 30


class Config:
    # --- screen
    screen = ScreenConfig

    # --- screen map
    sample_map_x = 0
    sample_map_y = 0
    sample_map_width = screen.width
    sample_map_height = 60

    # --- minimap
    minimap_y = sample_map_height + sample_map_y + 1
    minimap_y_size = screen.height - minimap_y
    minimap_x_size = int(sample_map_width * (minimap_y_size / sample_map_height))
    print(minimap_x_size, minimap_y_size)
    minimap_x = screen.width - minimap_x_size

    # --- map
    big_map = MapConfig(sample_map_width * 2, sample_map_height * 2, 15, 10, 100)
    little_map = MapConfig(sample_map_width, sample_map_height)
    big_floor = 10

    # --- UI
    bar_width = 20

    names_location_y = sample_map_height + sample_map_y + 1

    data_location_y = names_location_y + 1
    data_left_x = 0
    data_right_x = bar_width + 1
    data_top_y = 0

    log_width = min(minimap_x - data_right_x, 50)
    log_height = screen.height - data_location_y

    overlay_width = screen.width // 2
    overlay_left_x = 0
    overlay_right_x = screen.width // 2
    overlay_border = overlay_width - 1

    # --- menu
    menu_bg_image = "menu_background.png"

    # --- game params
    fov_radius = 8
    torch_radius = 6
    save_name = "savegame.sav"

    @classmethod
    def to_dict(cls) -> dict:
        return {x: y for (x, y) in cls.__dict__.items() if x[:2] != "__" and x != "to_dict"}

    DEBUG = False


if __name__ == '__main__':
    import pprint

    pprint.pp(Config.to_dict())
