from unittest import TestCase
# need MapSystem.map since suite outside inventory system folder
from MapSystem.map import Map, MazeSystem, BlankSystem, MapException

class MapTest(TestCase):
    def test_map_copy(self):
        for s in range(2, 6):
            for k in range(100):
                map_outer = BlankSystem(20, 20)
                map_inner = MazeSystem(s, s)

                BlankSystem.draw_sub_map(map_outer, map_inner, 0, 0)

                for i in range(map_outer.width):
                    for j in range(map_outer.height):
                        if i < map_inner.width and j < map_inner.height:
                            self.assertEqual(map_outer.map[i][j], map_inner.map[i][j])



