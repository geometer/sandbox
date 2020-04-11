# "Romantics of Geometry" group on Facebook, problem 4594
# https://www.facebook.com/groups/parmenides52/permalink/2784962828284072/

from sandbox import Scene
from sandbox.property import LengthRatioProperty

from .base import ExplainerTest

class RomanticsOfGeometry4594(ExplainerTest):
    def createScene(self):
        scene = Scene()

        A, B, C = scene.triangle(labels=('A', 'B', 'C'))
        scene.perpendicular_constraint((A, B), (A, C), comment='Given: AB ⟂ AC')
        I = scene.incentre_point((A, B, C), label='I')
        J = scene.orthocentre_point((A, B, I), label='J')

        # Additional constructions
        #D = A.line_through(B).intersection_point(I.line_through(J), label='D')
        #E = A.line_through(I).intersection_point(B.line_through(J), label='E')

        return scene

    def testPointOnLine(self):
        A = self.scene.get('A')
        B = self.scene.get('B')
        I = self.scene.get('I')
        J = self.scene.get('J')
        prop = LengthRatioProperty(A.segment(J), B.segment(I), 1)
        self.assertIn(prop, self.explainer.context)
