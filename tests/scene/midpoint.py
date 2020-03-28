from sandbox import Scene
from .base import SceneTest

class MidpointTest1(SceneTest):
    def createScene(self):
        scene = Scene()

        A = scene.free_point(label='A')
        B = scene.free_point(label='B')
        A.segment(B).middle_point(label='C')
        A.line_through(B, label='AB')

        return scene

    def testPointOnLine(self):
        assert self.scene.get('C') in self.scene.get('AB')

class MidpointTest2(SceneTest):
    def createScene(self):
        scene = Scene()

        A = scene.free_point(label='A')
        B = scene.free_point(label='B')
        A.line_through(B, label='AB')
        A.segment(B).middle_point(label='C')

        return scene

    def testPointOnLine(self):
        assert self.scene.get('C') in self.scene.get('AB')
