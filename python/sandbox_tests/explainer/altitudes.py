from sandbox import Scene
from sandbox.property import PerpendicularSegmentsProperty, SimilarTrianglesProperty

from .base import ExplainerTest

class AltitudesAndSimilarityAcuteTest(ExplainerTest):
    def createScene(self):
        scene = Scene()

        triangle = scene.nondegenerate_triangle(labels=('A', 'B', 'C'))
        A, B, C = triangle.points
        altitudeA = scene.altitude(triangle, A)
        altitudeB = scene.altitude(triangle, B)
        A1 = altitudeA.intersection_point(B.line_through(C), label='A1')
        B1 = altitudeB.intersection_point(A.line_through(C), label='B1')

        C.angle(A, B).is_acute_constraint()

        return scene

    def test(self):
        A = self.scene.get('A')
        B = self.scene.get('B')
        C = self.scene.get('C')
        A1 = self.scene.get('A1')
        B1 = self.scene.get('B1')
        prop = SimilarTrianglesProperty((A, B, C), (A1, B1, C))
        self.assertIn(prop, self.explainer.context)

class AltitudesAndSimilarityObtuseTest(ExplainerTest):
    def createScene(self):
        scene = Scene()

        triangle = scene.nondegenerate_triangle(labels=('A', 'B', 'C'))
        A, B, C = triangle.points
        altitudeA = scene.altitude(triangle, A)
        altitudeB = scene.altitude(triangle, B)
        A1 = altitudeA.intersection_point(B.line_through(C), label='A1')
        B1 = altitudeB.intersection_point(A.line_through(C), label='B1')

        C.angle(A, B).is_obtuse_constraint()

        return scene

    def test(self):
        A = self.scene.get('A')
        B = self.scene.get('B')
        C = self.scene.get('C')
        A1 = self.scene.get('A1')
        B1 = self.scene.get('B1')
        prop = SimilarTrianglesProperty((A, B, C), (A1, B1, C))
        self.assertIn(prop, self.explainer.context)

class OrthocentreTest(ExplainerTest):
    def createScene(self):
        scene = Scene()

        triangle = scene.nondegenerate_triangle(labels=('A', 'B', 'C'))
        A, B, C = triangle.points
        altitudeA = scene.altitude(triangle, A)
        altitudeB = scene.altitude(triangle, B)
        X = altitudeA.intersection_point(altitudeB, label='X')

        return scene

    def test(self):
        A = self.scene.get('A')
        B = self.scene.get('B')
        C = self.scene.get('C')
        X = self.scene.get('X')
        prop = PerpendicularSegmentsProperty(A.segment(B), C.segment(X))
        self.assertNotIn(prop, self.explainer.context)

class OrthocentreAdvancedTest(ExplainerTest):
    def extra_rules(self):
        return {'advanced'}

    def createScene(self):
        scene = Scene()

        triangle = scene.nondegenerate_triangle(labels=('A', 'B', 'C'))
        A, B, C = triangle.points
        altitudeA = scene.altitude(triangle, A)
        altitudeB = scene.altitude(triangle, B)
        X = altitudeA.intersection_point(altitudeB, label='X')

        return scene

    def test(self):
        A = self.scene.get('A')
        B = self.scene.get('B')
        C = self.scene.get('C')
        X = self.scene.get('X')
        prop = PerpendicularSegmentsProperty(A.segment(B), C.segment(X))
        self.assertIn(prop, self.explainer.context)
