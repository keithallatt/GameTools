from unittest import TestCase
# need MapSystem.map since suite outside inventory system folder
from MapSystem.map import Map, MazeSystem, BlankSystem, MapException
import MapSystem.map as map_sys


class MapTest(TestCase):
    """ MapSystem module test cases """
    def test_map_copy(self):
        """ Test if copying map works using draw_sub_map """
        for s in range(2, 6):
            for k in range(100):
                map_outer = BlankSystem(20, 20)
                map_inner = MazeSystem(s, s)

                BlankSystem.draw_sub_map(map_outer, map_inner, 0, 0)

                for i in range(map_outer.width):
                    for j in range(map_outer.height):
                        if i < map_inner.width and j < map_inner.height:
                            self.assertEqual(map_outer.map[i][j], map_inner.map[i][j])

    def test_map_exception(self):
        """ Ensure exception raised for obviously wrong commands """
        # test setting to non-existent color key
        with self.assertRaises(MapException) as context:
            map_sys.set_map_char_block(character="ObviouslyWrong")

        self.assertTrue('Color key non-existent' in
                        context.exception.msg)



