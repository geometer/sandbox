from sandbox import Scene
from sandbox.property import *

from .base import ExplainerTest

class Collinearity(ExplainerTest):
    def createScene(self):
        scene = Scene()

        A = scene.free_point(label='A')
        B = scene.free_point(label='B')
        l = A.line_through(B, label='l')
        C = l.free_point(label='C')

        return scene

    def test(self):
        A = self.scene.get('A')
        B = self.scene.get('B')
        C = self.scene.get('C')
        self.assertIn(PointsCollinearityProperty(A, B, C, True), self.explainer.context)

class PointOnLine(ExplainerTest):
    def createScene(self):
        scene = Scene()

        A = scene.free_point(label='A')
        B = scene.free_point(label='B')
        C = scene.free_point(label='C')
        D = scene.free_point(label='D')
        E = scene.free_point(label='E')
        l = A.line_through(B, label='l')
        scene.add_property(PointsCollinearityProperty(A, B, C, True), None)
        scene.add_property(PointsCollinearityProperty(A, B, D, False), None)

        return scene

    def test(self):
        A = self.scene.get('A')
        B = self.scene.get('B')
        C = self.scene.get('C')
        D = self.scene.get('D')
        E = self.scene.get('E')
        l = self.scene.get('l')
        self.assertIn(LinesCoincidenceProperty(A.segment(B), l, True), self.explainer.context)
        self.assertIn(LinesCoincidenceProperty(A.segment(D), l, False), self.explainer.context)
        self.assertIn(PointOnLineProperty(A, l, True), self.explainer.context)
        self.assertIn(PointOnLineProperty(B, l, True), self.explainer.context)
        self.assertIn(PointOnLineProperty(C, A.segment(B), True), self.explainer.context)
        self.assertIn(PointOnLineProperty(C, l, True), self.explainer.context)
        self.assertIn(PointOnLineProperty(D, A.segment(B), False), self.explainer.context)
        self.assertIn(PointOnLineProperty(D, l, False), self.explainer.context)
        self.assertNotIn(PointOnLineProperty(E, l, True), self.explainer.context)

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

class TwoPointsOnTwoDifferentLines(ExplainerTest):
    def createScene(self):
        scene = Scene()

        A = scene.free_point(label='A')
        B = scene.free_point(label='B')
        C = scene.free_point(label='C')
        D = scene.free_point(label='D')
        scene.add_property(PointsCollinearityProperty(A, B, C, True), None)
        scene.add_property(PointsCollinearityProperty(A, B, D, True), None)
        scene.add_property(PointsCollinearityProperty(B, C, D, False), None)

        return scene

    def test(self):
        A = self.scene.get('A')
        B = self.scene.get('B')

        self.assertIn(PointsCoincidenceProperty(A, B, True), self.explainer.context)

class TwoPointsOnThreeDifferentLines(ExplainerTest):
    def createScene(self):
        scene = Scene()

        A = scene.free_point(label='A')
        B = scene.free_point(label='B')
        C = scene.free_point(label='C')
        D = scene.free_point(label='D')
        E = scene.free_point(label='E')
        scene.add_property(PointsCollinearityProperty(A, B, C, True), None)
        scene.add_property(PointsCollinearityProperty(A, B, D, True), None)
        scene.add_property(PointsCollinearityProperty(A, B, E, True), None)
        scene.add_property(PointsCollinearityProperty(C, D, E, False), None)

        return scene

    def test(self):
        A = self.scene.get('A')
        B = self.scene.get('B')

        self.assertIn(PointsCoincidenceProperty(A, B, True), self.explainer.context)

class TwoAcuteAnglesWithCommonSide(ExplainerTest):
    def createScene(self):
        scene = Scene()

        A = scene.free_point(label='A')
        B = scene.free_point(label='B')
        C = scene.free_point(label='C')
        D = scene.free_point(label='D')
        scene.add_property(PointsCoincidenceProperty(A, B, False), None)
        scene.add_property(PointsCoincidenceProperty(A, C, False), None)
        scene.add_property(PointsCoincidenceProperty(A, D, False), None)
        scene.add_property(AngleKindProperty(A.angle(B, C), AngleKindProperty.Kind.acute), None)
        scene.add_property(AngleKindProperty(A.angle(B, D), AngleKindProperty.Kind.acute), None)
        scene.add_property(PointsCollinearityProperty(A, C, D, True), None)

        return scene

    def test(self):
        A = self.scene.get('A')
        C = self.scene.get('C')
        D = self.scene.get('D')

        self.assertIn(AngleValueProperty(A.angle(C, D), 0), self.explainer.context)

class TwoObtuseAnglesWithCommonSide(ExplainerTest):
    def createScene(self):
        scene = Scene()

        A = scene.free_point(label='A')
        B = scene.free_point(label='B')
        C = scene.free_point(label='C')
        D = scene.free_point(label='D')
        scene.add_property(PointsCoincidenceProperty(A, B, False), None)
        scene.add_property(PointsCoincidenceProperty(A, C, False), None)
        scene.add_property(PointsCoincidenceProperty(A, D, False), None)
        scene.add_property(AngleKindProperty(A.angle(B, C), AngleKindProperty.Kind.obtuse), None)
        scene.add_property(AngleKindProperty(A.angle(B, D), AngleKindProperty.Kind.obtuse), None)
        scene.add_property(PointsCollinearityProperty(A, C, D, True), None)

        return scene

    def test(self):
        A = self.scene.get('A')
        C = self.scene.get('C')
        D = self.scene.get('D')

        self.assertIn(AngleValueProperty(A.angle(C, D), 0), self.explainer.context)

class AcuteAndObtuseAnglesWithCommonSide(ExplainerTest):
    def createScene(self):
        scene = Scene()

        A = scene.free_point(label='A')
        B = scene.free_point(label='B')
        C = scene.free_point(label='C')
        D = scene.free_point(label='D')
        scene.add_property(PointsCoincidenceProperty(A, B, False), None)
        scene.add_property(PointsCoincidenceProperty(A, C, False), None)
        scene.add_property(PointsCoincidenceProperty(A, D, False), None)
        scene.add_property(AngleKindProperty(A.angle(B, C), AngleKindProperty.Kind.acute), None)
        scene.add_property(AngleKindProperty(A.angle(B, D), AngleKindProperty.Kind.obtuse), None)
        scene.add_property(PointsCollinearityProperty(A, C, D, True), None)

        return scene

    def test(self):
        A = self.scene.get('A')
        C = self.scene.get('C')
        D = self.scene.get('D')

        self.assertIn(AngleValueProperty(A.angle(C, D), 180), self.explainer.context)

class TwoRightAnglesWithCommonSide(ExplainerTest):
    def createScene(self):
        scene = Scene()

        A = scene.free_point(label='A')
        B = scene.free_point(label='B')
        C = scene.free_point(label='C')
        D = scene.free_point(label='D')
        scene.add_property(PointsCoincidenceProperty(A, B, False), None)
        scene.add_property(PointsCoincidenceProperty(A, C, False), None)
        scene.add_property(PointsCoincidenceProperty(A, D, False), None)
        scene.add_property(AngleKindProperty(A.angle(B, C), AngleKindProperty.Kind.right), None)
        scene.add_property(AngleKindProperty(A.angle(B, D), AngleKindProperty.Kind.right), None)
        scene.add_property(PointsCollinearityProperty(A, C, D, True), None)

        return scene

    def test(self):
        A = self.scene.get('A')
        C = self.scene.get('C')
        D = self.scene.get('D')

        self.assertNotIn(AngleValueProperty(A.angle(C, D), 0), self.explainer.context)
        self.assertNotIn(AngleValueProperty(A.angle(C, D), 180), self.explainer.context)
