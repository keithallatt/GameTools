from GameSystem.game_system import MenuSysIO, ScrollingMapIO, Game, Render
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

    map_sys = ScrollingMapIO(map_system, (1, 1), (21, 21))

    replace_render = Render.ReplaceFilter(replace_with={
        " ": "_",
        "\u2588": " "
    })

    border_render = Render.Border.from_map_io(map_sys, render_super_layer=replace_render)

    map_sys.set_render(border_render)

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

    Game.start_game_sys([main_title])
