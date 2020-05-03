# GEO0324 from http://hilbert.mat.uc.pt/TGTP/Problems/listing.php
from sandbox import Scene
from sandbox.property import PointsCoincidenceProperty

from .base import ExplainerTest

class GEO0324(ExplainerTest):
    def createScene(self):
        scene = Scene()

        triangle = scene.nondegenerate_triangle(labels=('A', 'B', 'C'))
        triangle2 = Scene.Triangle(*[side.middle_point() for side in triangle.sides])
        D = scene.circumcentre_point(triangle, label='D')
        E = scene.orthocentre_point(triangle2, label='E')

        return scene

    def test(self):
        D = self.scene.get('D')
        E = self.scene.get('E')
        prop = PointsCoincidenceProperty(D, E, coincident=True)
        self.assertIn(prop, self.explainer.context)
