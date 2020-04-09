# GEO0324 from http://hilbert.mat.uc.pt/TGTP/Problems/listing.php
from sandbox import Scene
from sandbox.property import PointsCoincidenceProperty

from .base import ExplainerTest

class GEO0324(ExplainerTest):
    def createScene(self):
        scene = Scene()

        A, B, C = scene.triangle(labels=('A', 'B', 'C'))
        A1 = B.segment(C).middle_point(label='A1')
        B1 = A.segment(C).middle_point(label='B1')
        C1 = A.segment(B).middle_point(label='C1')
        D = scene.circumcentre_point((A, B, C), label='D')
        E = scene.orthocentre_point((A1, B1, C1), label='E')

        return scene

    def test(self):
        D = self.scene.get('D')
        E = self.scene.get('E')
        prop = PointsCoincidenceProperty(D, E, coincident=True)
        self.assertIn(prop, self.explainer.context)
