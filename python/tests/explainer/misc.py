from sandbox import Scene
from sandbox.property import *

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

class TwoFootsOfSamePerpendicular(ExplainerTest):
    def createScene(self):
        scene = Scene()

        A = scene.free_point(label='A')
        B = scene.free_point(label='B')
        C = scene.free_point(label='C')
        D = scene.free_point(label='D')
        scene.add_property(AngleValueProperty(C.angle(A, D), 90), None)
        scene.add_property(PerpendicularSegmentsProperty(A.segment(B), C.segment(D)), None)
        scene.add_property(PointsCoincidenceProperty(A, B, False), None)
        scene.add_property(PointsCoincidenceProperty(C, D, False), None)
        scene.add_property(PointsCollinearityProperty(B, C, D, True), None)

        return scene

    def test(self):
        A = self.scene.get('A')
        B = self.scene.get('B')
        C = self.scene.get('C')
        D = self.scene.get('D')

        self.assertIn(FootOfPerpendicularProperty(C, A, C.segment(D)), self.explainer.context)
        self.assertIn(FootOfPerpendicularProperty(B, A, C.segment(D)), self.explainer.context)
        self.assertNotIn(FootOfPerpendicularProperty(A, B, C.segment(D)), self.explainer.context)
        self.assertIn(PointsCoincidenceProperty(B, C, True), self.explainer.context)
        self.assertIn(IntersectionOfLinesProperty(C, A.segment(B), C.segment(D)), self.explainer.context)
        self.assertIn(IntersectionOfLinesProperty(B, A.segment(B), C.segment(D)), self.explainer.context)
        self.assertNotIn(IntersectionOfLinesProperty(A, A.segment(B), C.segment(D)), self.explainer.context)
