class Config:
    # --- screen
    screen_width = 120
    screen_height = 80

    # --- screen map
    sample_map_x = 0
    sample_map_y = 0
    sample_map_width = screen_width
    sample_map_height = 60

    # --- map
    map_width = sample_map_width * 2
    map_height = sample_map_height * 2

    # --- UI
    bar_width = 20

    names_location_y = sample_map_height + sample_map_y + 1

    data_location_y = names_location_y + 1
    data_left_x = 0
    data_right_x = bar_width + 1
    data_top_y = 0

    log_width = 40
    log_height = screen_height - data_location_y

    overlay_width = screen_width // 2
    overlay_left_x = 0
    overlay_right_x = screen_width // 2
    overlay_border = overlay_width - 1

    # --- level params
    room_max_size = 10
    room_min_size = 6
    max_rooms = 30

    # --- menu
    menu_bg_image = "menu_background.png"

    # --- game params
    fov_radius = 8
    save_name = "savegame.sav"

    @classmethod
    def to_dict(cls) -> dict:
        return {x: y for (x, y) in cls.__dict__.items() if x[:2] != "__" and x != "to_dict"}

    DEBUG = False


if __name__ == '__main__':
    import pprint

    pprint.pp(Config.to_dict())
