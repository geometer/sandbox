# GEO0324 from http://hilbert.mat.uc.pt/TGTP/Problems/listing.php
from sandbox import Scene
from sandbox.property import SimilarTrianglesProperty

from .base import ExplainerTest

class AltitudesAndSimilarityAcuteTest(ExplainerTest):
    def createScene(self):
        scene = Scene()

        A, B, C = scene.triangle(labels=('A', 'B', 'C'))
        altitudeA = scene.altitude((A, B, C), A)
        altitudeB = scene.altitude((A, B, C), B)
        A1 = altitudeA.intersection_point(B.line_through(C), label='A1')
        B1 = altitudeB.intersection_point(A.line_through(C), label='B1')

        C.angle(A, B).is_acute_constraint(comment='Test')

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

        A, B, C = scene.triangle(labels=('A', 'B', 'C'))
        altitudeA = scene.altitude((A, B, C), A)
        altitudeB = scene.altitude((A, B, C), B)
        A1 = altitudeA.intersection_point(B.line_through(C), label='A1')
        B1 = altitudeB.intersection_point(A.line_through(C), label='B1')

        C.angle(A, B).is_obtuse_constraint(comment='Test')

        return scene

    def test(self):
        A = self.scene.get('A')
        B = self.scene.get('B')
        C = self.scene.get('C')
        A1 = self.scene.get('A1')
        B1 = self.scene.get('B1')
        prop = SimilarTrianglesProperty((A, B, C), (A1, B1, C))
        self.assertIn(prop, self.explainer.context)
