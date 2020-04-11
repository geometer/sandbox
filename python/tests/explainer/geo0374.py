# GEO0374 from http://hilbert.mat.uc.pt/TGTP/Problems/listing.php
from sandbox import Scene
from sandbox.property import AngleValueProperty

from .base import ExplainerTest

class GEO0374(ExplainerTest):
    def createScene(self):
        scene = Scene()

        A, B, C = scene.triangle(labels=('A', 'B', 'C'))
        scene.equilateral_constraint((A, B, C))
        D = B.translated_point(A.vector(B), 2, label='D')
        F = scene.perpendicular_foot_point(D, B.line_through(C), label='F')

        return scene

    @property
    def prop(self):
        A = self.scene.get('A')
        C = self.scene.get('C')
        F = self.scene.get('F')
        return AngleValueProperty(A.angle(C, F), 90)

    def test(self):
        self.assertNotIn(self.prop, self.explainer.context)

class GEO0374Advanced(GEO0374):
    def explainer_options(self):
        return {'advanced'}

    def test(self):
        self.assertIn(self.prop, self.explainer.context)

class GEO0374Trigonometric(GEO0374):
    def explainer_options(self):
        return {'trigonometric'}

    def test(self):
        self.assertIn(self.prop, self.explainer.context)
