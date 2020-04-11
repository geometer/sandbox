# "Romantics of Geometry" group on Facebook, problem 4578
# https://www.facebook.com/groups/parmenides52/permalink/2779763428804012/

from sandbox import Scene
from sandbox.property import AngleValueProperty

from .base import ExplainerTest

class RomanticsOfGeometry4578(ExplainerTest):
    def createScene(self):
        scene = Scene()

        A, B, C = scene.triangle(labels=('A', 'B', 'C'))
        D = scene.orthocentre_point((A, B, C), label='D')
        D.inside_triangle_constraint(A, B, C)
        #H = A.line_through(D).intersection_point(B.line_through(C), label='H')
        #G = C.line_through(D).intersection_point(A.line_through(B), label='G')
        A.segment(B).congruent_constraint(C.segment(D), comment='Given: |AB| = |CD|')

        return scene

    def testPointOnLine(self):
        prop = AngleValueProperty(self.scene.get('C').angle(self.scene.get('A'), self.scene.get('B')), 45)
        self.assertIn(prop, self.explainer.context)
