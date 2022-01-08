class Config:
    # --- screen
    screen_width = 80
    screen_height = 50

    # --- map
    map_width = screen_width
    map_height = 43

    # --- UI
    bar_width = 20

    names_location_y = map_height + 1

    data_location_y = names_location_y + 1
    data_left_x = 0
    data_right_x = bar_width + 1
    data_top_y = 0

    log_width = 40
    log_height = screen_height - data_location_y

    overlay_width = 35
    overlay_left_x = 0
    overlay_right_x = screen_width // 2
    overlay_border = 30

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


if __name__ == '__main__':
    import pprint

    pprint.pp(Config.to_dict())
