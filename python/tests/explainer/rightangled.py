from sandbox import Scene
from sandbox.property import LengthRatioProperty

from .base import ExplainerTest

class RightAngledTriangleMedian(ExplainerTest):
    def createScene(self):
        scene = Scene()

        A, B, C = scene.triangle(labels=('A', 'B', 'C'))
        A.segment(C).perpendicular_constraint(B.segment(C), comment='Given: AC ⟂ BC')
        D = A.segment(B).middle_point(label='D')

        return scene

    @property
    def prop(self):
        A = self.scene.get('A')
        C = self.scene.get('C')
        D = self.scene.get('D')
        return LengthRatioProperty(D.segment(A), D.segment(C), 1)

    def test(self):
        self.assertNotIn(self.prop, self.explainer.context)

class RightAngledTriangleMedianAdvanced(RightAngledTriangleMedian):
    def explainer_options(self):
        return {'advanced': True}

    def test(self):
        self.assertIn(self.prop, self.explainer.context)
