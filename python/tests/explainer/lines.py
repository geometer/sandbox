from sandbox import Scene
from sandbox.property import PointsCollinearityProperty, PointOnLineProperty, SameOrOppositeSideProperty
from sandbox.propertyset import ContradictionError

from .base import ExplainerTest

class LinesTest1(ExplainerTest):
    def createScene(self):
        scene = Scene()

        A = scene.free_point(label='A')
        B = scene.free_point(label='B')
        B.not_equal_constraint(A)
        C = scene.free_point(label='C')
        D = scene.free_point(label='D')
        C.collinear_constraint(A, B)
        D.collinear_constraint(A, B)

        return scene

    def test(self):
        A = self.scene.get('A')
        C = self.scene.get('C')
        D = self.scene.get('D')
        prop = PointsCollinearityProperty(A, C, D, True)
        self.assertIn(prop, self.explainer.context)

class LinesTest2(ExplainerTest):
    def createScene(self):
        scene = Scene()

        A = scene.free_point(label='A')
        B = scene.free_point(label='B')
        B.not_equal_constraint(A)
        C = scene.free_point(label='C')
        D = scene.free_point(label='D')
        C.collinear_constraint(A, B)
        D.collinear_constraint(A, B)
        E = scene.free_point(label='E')
        E.not_collinear_constraint(C, D)
        F = scene.free_point(label='F')
        F.collinear_constraint(C, D)

        return scene

    def test(self):
        A = self.scene.get('A')
        B = self.scene.get('B')
        C = self.scene.get('C')
        D = self.scene.get('D')
        E = self.scene.get('E')
        F = self.scene.get('F')
        props = (
            PointOnLineProperty(A.segment(B), E, False),
            PointOnLineProperty(A.segment(B), F, True),
            PointOnLineProperty(C.segment(D), E, False),
            PointOnLineProperty(C.segment(D), F, True),
            PointsCollinearityProperty(A, C, D, True),
            PointsCollinearityProperty(B, D, F, True),
            PointsCollinearityProperty(A, B, E, False),
        )
        for prop in props:
            self.assertIn(prop, self.explainer.context)

    def test_neg(self):
        A = self.scene.get('A')
        B = self.scene.get('B')
        C = self.scene.get('C')
        D = self.scene.get('D')
        E = self.scene.get('E')
        F = self.scene.get('F')
        props = (
            PointOnLineProperty(A.segment(C), B, False),
        )
        for prop in props:
            self.assertNotIn(prop, self.explainer.context)

    def test_exc(self):
        A = self.scene.get('A')
        B = self.scene.get('B')
        C = self.scene.get('C')
        D = self.scene.get('D')
        E = self.scene.get('E')
        F = self.scene.get('F')
        props = (
            PointOnLineProperty(A.segment(B), E, True),
            PointOnLineProperty(A.segment(B), F, False),
            PointsCollinearityProperty(A, B, E, True),
        )
        for prop in props:
            def call():
                return self.explainer.context[prop]
            self.assertRaises(ContradictionError, call)

class LinesTest3(ExplainerTest):
    def createScene(self):
        scene = Scene()

        X = scene.free_point(label='X')
        A = scene.free_point(label='A')
        B = scene.free_point(label='B')
        X.not_equal_constraint(A)
        B.not_equal_constraint(A)
        C = scene.free_point(label='C')
        D = scene.free_point(label='D')
        X.collinear_constraint(A, B)
        C.collinear_constraint(A, B)
        B.not_equal_constraint(C)
        D.collinear_constraint(A, X)

        return scene

    def test(self):
        B = self.scene.get('B')
        C = self.scene.get('C')
        D = self.scene.get('D')
        prop = PointsCollinearityProperty(B, C, D, True)
        self.assertIn(prop, self.explainer.context)

class LineSidesTest(ExplainerTest):
    def createScene(self):
        scene = Scene()

        A = scene.free_point(label='A')
        B = scene.free_point(label='B')
        C = scene.free_point(label='C')
        D = scene.free_point(label='D')
        E = scene.free_point(label='E')
        F = scene.free_point(label='F')
        A.not_equal_constraint(B)
        A.not_equal_constraint(C)
        A.collinear_constraint(B, C)
        E.opposite_side_constraint(D, A.line_through(B))
        F.same_side_constraint(D, A.line_through(B))

        return scene

    def test(self):
        A = self.scene.get('A')
        B = self.scene.get('B')
        C = self.scene.get('C')
        D = self.scene.get('D')
        E = self.scene.get('E')
        F = self.scene.get('F')

        props = (
            SameOrOppositeSideProperty(A.segment(B), D, E, False),
            SameOrOppositeSideProperty(A.segment(C), D, E, False),
            SameOrOppositeSideProperty(A.segment(B), D, F, True),
            SameOrOppositeSideProperty(A.segment(C), D, F, True),
            SameOrOppositeSideProperty(A.segment(B), F, E, False),
            SameOrOppositeSideProperty(A.segment(C), F, E, False),
        )
        for prop in props:
            self.assertIn(prop, self.explainer.context)
