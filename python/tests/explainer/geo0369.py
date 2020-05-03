# GEO0369 from http://hilbert.mat.uc.pt/TGTP/Problems/listing.php
from sandbox import Scene
from sandbox.property import LengthRatioProperty

from .base import ExplainerTest

class GEO0369(ExplainerTest):
    def createScene(self):
        scene = Scene()

        A, B, C = scene.nondegenerate_triangle(labels=('A', 'B', 'C')).points
        F = B.segment(C).middle_point(label='F')
        D = scene.perpendicular_foot_point(C, A.line_through(B), label='D')
        E = scene.perpendicular_foot_point(B, A.line_through(C), label='E')
        G = scene.perpendicular_foot_point(F, D.line_through(E), label='G')

        return scene

    @property
    def prop(self):
        D = self.scene.get('D')
        E = self.scene.get('E')
        G = self.scene.get('G')
        return LengthRatioProperty(G.segment(D), G.segment(E), 1)

    def test(self):
        self.assertNotIn(self.prop, self.explainer.context)

class GEO0369Advanced(GEO0369):
    def explainer_options(self):
        return {'advanced': True}

    def test(self):
        self.assertIn(self.prop, self.explainer.context)
