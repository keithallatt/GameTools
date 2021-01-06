from GameSystem.game_system import MenuSysIO, ScrollingMapIO, start_game_sys, Render
from MapSystem.map import MazeSystem

if __name__ == "__main__":
    main_title = MenuSysIO(title="Start",
                           option_choices=["Start (s)", "Quit (q)"],
                           font_size=12)
    pause_title = MenuSysIO(title="Pause",
                            option_choices=["Continue (c)", "Return to menu (r)", "Quit (q)"],
                            font_size=10)

    map_system = MazeSystem(41, 41)
    map_system.declare_map_char_block("PORTAL", "[]", walkable=True)

    width, height = 21, 21

    map_sys = ScrollingMapIO(map_system, (1, 1), (width, height))
    map_sys.render = Render.Border.from_map_io(map_sys)

    main_title.link_sys_change(
        [], lambda x: x.chosen and x.chosen_option.startswith("Quit"),
        key_binding='q'
    )
    main_title.link_sys_change(
        [map_sys], lambda x: x.chosen and x.chosen_option.startswith("Start"),
        key_binding='s'
    )

    pause_title.link_sys_change(
        [map_sys], lambda x: x.chosen and x.chosen_option.startswith("Continue"),
        key_binding='c'
    )
    pause_title.link_sys_change(
        [main_title], lambda x: x.chosen and x.chosen_option.startswith("Return to menu"),
        key_binding='r'
    )
    pause_title.link_sys_change(
        [], lambda x: x.chosen and x.chosen_option.startswith("Quit"),
        key_binding='q'
    )
    map_sys.link_sys_change(
        [pause_title], lambda x: False, transient=True,
        key_binding='p'
    )

    map_sys.link_relocation((-2, -2), (1, 1))

    start_game_sys([main_title])
