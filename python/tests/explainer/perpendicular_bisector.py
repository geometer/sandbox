from sandbox import Scene
from sandbox.property import PointsCollinearityProperty, SameOrOppositeSideProperty

from .base import ExplainerTest

class ThreePointsOnPerpendicularBisectorCollinearity1(ExplainerTest):
    def createScene(self):
        scene = Scene()

        A, B, C = scene.triangle(labels=('A', 'B', 'C'))
        D = scene.free_point(label='D')
        E = scene.free_point(label='E')
        A.segment(C).congruent_constraint(B.segment(C))
        A.segment(D).congruent_constraint(B.segment(D))
        A.segment(E).congruent_constraint(B.segment(E))

        return scene

    def test(self):
        A = self.scene.get('A')
        B = self.scene.get('B')
        C = self.scene.get('C')
        D = self.scene.get('D')
        E = self.scene.get('E')
        prop0 = PointsCollinearityProperty(C, D, E, True)
        prop1 = SameOrOppositeSideProperty(D.segment(E), A, B, False)
        self.assertIn(prop0, self.explainer.context)
        self.assertNotIn(prop1, self.explainer.context)
        self.assertEqual(len(self.explainer.explanation(prop0).reason.all_premises), 6)

class ThreePointsOnPerpendicularBisectorCollinearity2(ExplainerTest):
    def createScene(self):
        scene = Scene()

        A, B, C = scene.triangle(labels=('A', 'B', 'C'))
        D = scene.free_point(label='D')
        E = scene.free_point(label='E')
        A.segment(C).congruent_constraint(B.segment(C))
        A.segment(D).congruent_constraint(B.segment(D))
        A.segment(E).congruent_constraint(B.segment(E))
        D.not_equal_constraint(E)

        return scene

    def test(self):
        A = self.scene.get('A')
        B = self.scene.get('B')
        C = self.scene.get('C')
        D = self.scene.get('D')
        E = self.scene.get('E')
        prop0 = PointsCollinearityProperty(C, D, E, True)
        prop1 = SameOrOppositeSideProperty(D.segment(E), A, B, False)
        self.assertIn(prop0, self.explainer.context)
        self.assertIn(prop1, self.explainer.context)
