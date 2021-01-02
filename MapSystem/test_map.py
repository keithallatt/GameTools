from unittest import TestCase
# need MapSystem.map since suite outside inventory system folder
from MapSystem.map import Map, MazeSystem, MapException


class MapTest(TestCase):
    """ MapSystem module test cases """
    def test_map_copy(self):
        """ Test if copying map works using draw_sub_map """
        for s in range(2, 6):
            for k in range(100):
                map_outer = Map(20, 20)
                map_inner = MazeSystem(s, s)

                Map.draw_sub_map(map_outer, map_inner, 0, 0)

                for i in range(map_outer.width):
                    for j in range(map_outer.height):
                        if i < map_inner.width and j < map_inner.height:
                            self.assertEqual(map_outer.map[i][j], map_inner.map[i][j])

    def test_map_exception(self):
        """ Ensure exception raised for obviously wrong commands """
        # test setting to non-existent color key
        example_map = Map(5, 5)
        with self.assertRaises(MapException) as context:
            example_map.set_map_char_block(character="ObviouslyWrong")

        self.assertTrue('Character key non-existent' in
                        context.exception.msg)



