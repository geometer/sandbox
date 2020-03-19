from sandbox import Scene
from sandbox.property import PointInsideAngleProperty

from .base import ExplainerTest

class InsideTriangle1(ExplainerTest):
    def createScene(self):
        scene = Scene()

        A, B, C = scene.triangle(labels=('A', 'B', 'C'))
        D = A.segment(B).free_point(label='D')
        E = A.segment(C).free_point(label='E')
        X = D.line_through(C).intersection_point(E.line_through(B), label='X')

        return scene

    def testPointOnLine(self):
        A = self.scene.get('A')
        B = self.scene.get('B')
        C = self.scene.get('C')
        X = self.scene.get('X')
        self.assertIsNotNone(self.explainer.context[PointInsideAngleProperty(X, A.angle(B, C))])
        self.assertIsNotNone(self.explainer.context[PointInsideAngleProperty(X, B.angle(C, A))])
        self.assertIsNotNone(self.explainer.context[PointInsideAngleProperty(X, C.angle(A, B))])
