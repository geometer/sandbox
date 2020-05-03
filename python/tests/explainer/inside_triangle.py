from sandbox import Scene
from sandbox.property import PointInsideAngleProperty

from .base import ExplainerTest

class InsideTriangle1(ExplainerTest):
    def createScene(self):
        scene = Scene()

        A, B, C = scene.nondegenerate_triangle(labels=('A', 'B', 'C')).points
        D = A.segment(B).free_point(label='D')
        E = A.segment(C).free_point(label='E')
        X = D.line_through(C).intersection_point(E.line_through(B), label='X')

        return scene

    def testPointOnLine(self):
        A = self.scene.get('A')
        B = self.scene.get('B')
        C = self.scene.get('C')
        X = self.scene.get('X')
        self.assertIn(PointInsideAngleProperty(X, A.angle(B, C)), self.explainer.context)
        self.assertIn(PointInsideAngleProperty(X, B.angle(C, A)), self.explainer.context)
        self.assertIn(PointInsideAngleProperty(X, C.angle(A, B)), self.explainer.context)

class InsideTriangle2(ExplainerTest):
    def createScene(self):
        scene = Scene()

        A, B, C = scene.nondegenerate_triangle(labels=('A', 'B', 'C')).points
        D = A.segment(B).free_point(label='D')
        E = A.segment(C).free_point(label='E')
        F = B.segment(C).free_point(label='F')
        X = D.line_through(E).intersection_point(A.line_through(F), label='X')

        return scene

    def testPointOnLine(self):
        A = self.scene.get('A')
        B = self.scene.get('B')
        C = self.scene.get('C')
        X = self.scene.get('X')
        self.assertIn(PointInsideAngleProperty(X, A.angle(B, C)), self.explainer.context)
        self.assertIn(PointInsideAngleProperty(X, B.angle(C, A)), self.explainer.context)
        self.assertIn(PointInsideAngleProperty(X, C.angle(A, B)), self.explainer.context)
