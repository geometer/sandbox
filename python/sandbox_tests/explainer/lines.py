from sandbox import Scene
from sandbox.property import *
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
            PointOnLineProperty(E, A.segment(B), False),
            PointOnLineProperty(F, A.segment(B), True),
            PointOnLineProperty(E, C.segment(D), False),
            PointOnLineProperty(F, C.segment(D), True),
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
            PointOnLineProperty(B, A.segment(C), False),
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
            PointOnLineProperty(E, A.segment(B), True),
            PointOnLineProperty(F, A.segment(B), False),
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
        E.opposite_side_constraint(D, A.segment(B))
        F.same_side_constraint(D, A.segment(B))

        return scene

    def test(self):
        A = self.scene.get('A')
        B = self.scene.get('B')
        C = self.scene.get('C')
        D = self.scene.get('D')
        E = self.scene.get('E')
        F = self.scene.get('F')

        props = (
            LineAndTwoPointsProperty(A.segment(B), D, E, False),
            LineAndTwoPointsProperty(A.segment(C), D, E, False),
            LineAndTwoPointsProperty(A.segment(B), D, F, True),
            LineAndTwoPointsProperty(A.segment(C), D, F, True),
            LineAndTwoPointsProperty(A.segment(B), F, E, False),
            LineAndTwoPointsProperty(A.segment(C), F, E, False),
        )
        for prop in props:
            self.assertIn(prop, self.explainer.context)
