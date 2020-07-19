from sandbox import Scene
from sandbox.property import SameOrOppositeSideProperty

from .base import ExplainerTest

class SameSide(ExplainerTest):
    def createScene(self):
        scene = Scene()

        A, B, C = scene.nondegenerate_triangle(labels=['A', 'B', 'C']).points
        D = scene.free_point(label='D')
        A.angle(B, D).value_constraint(0)

        return scene

    def test(self):
        A = self.scene.get('A')
        B = self.scene.get('B')
        C = self.scene.get('C')
        D = self.scene.get('D')
        prop = SameOrOppositeSideProperty(A.segment(C), B, D, True)
        self.assertIn(prop, self.explainer.context)

class ThreeSegmentPoints(ExplainerTest):
    def createScene(self):
        scene = Scene()

        A, B, C = scene.nondegenerate_triangle(labels=['A', 'B', 'C']).points
        D = scene.free_point(label='D')
        A.angle(B, D).value_constraint(180)

        return scene

    def test(self):
        A = self.scene.get('A')
        B = self.scene.get('B')
        C = self.scene.get('C')
        D = self.scene.get('D')

        self.assertIn(SameOrOppositeSideProperty(A.segment(C), B, D, False), self.explainer.context)
        self.assertIn(SameOrOppositeSideProperty(B.segment(C), A, D, True), self.explainer.context)
        self.assertIn(SameOrOppositeSideProperty(D.segment(C), B, A, True), self.explainer.context)
