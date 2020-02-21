from sandbox import Scene, Placement

from .base import PlacementTest

class TestIntersection(PlacementTest):
    def createPlacement(self):
        scene = Scene()

        A = scene.free_point(label='A', x=1, y=1)
        B = scene.free_point(label='B', x=5, y=-3)
        C = scene.free_point(label='C', x=3, y=10)
        D = scene.free_point(label='D', x=4, y=11)
        AB = A.line_through(B)
        CD = C.line_through(D)
        AB.intersection_point(CD, label='E')

        return Placement(scene)

    def test1(self):
        self.assertCoordinates('E', -2.5, 4.5)
