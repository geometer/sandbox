# "Romantics of Geometry" group on Facebook, problem 4594
# https://www.facebook.com/groups/parmenides52/permalink/2784962828284072/

from sandbox import Scene
from sandbox.property import LengthRatioProperty

from .base import ExplainerTest

class RomanticsOfGeometry4594(ExplainerTest):
    def createScene(self):
        scene = Scene()

        triangle = scene.nondegenerate_triangle(labels=('A', 'B', 'C'))
        A, B, C = triangle.points
        A.segment(B).perpendicular_constraint(A.segment(C), comment='Given: AB ⟂ AC')
        I = scene.incentre_point(triangle, label='I')
        J = scene.orthocentre_point(Scene.Triangle((A, B, I)), label='J')

        return scene

    def testPointOnLine(self):
        A = self.scene.get('A')
        B = self.scene.get('B')
        I = self.scene.get('I')
        J = self.scene.get('J')
        prop = LengthRatioProperty(A.segment(J), B.segment(I), 1)
        self.assertNotIn(prop, self.explainer.context)

class RomanticsOfGeometry4594Constructions(ExplainerTest):
    def createScene(self):
        scene = Scene()

        triangle = scene.nondegenerate_triangle(labels=('A', 'B', 'C'))
        A, B, C = triangle.points
        A.segment(B).perpendicular_constraint(A.segment(C), comment='Given: AB ⟂ AC')
        I = scene.incentre_point(triangle, label='I')
        J = scene.orthocentre_point(Scene.Triangle((A, B, I)), label='J')

        # Additional constructions
        D = A.line_through(B).intersection_point(I.line_through(J), label='D')
        E = A.line_through(I).intersection_point(B.line_through(J), label='E')

        return scene

    def testPointOnLine(self):
        A = self.scene.get('A')
        B = self.scene.get('B')
        I = self.scene.get('I')
        J = self.scene.get('J')
        prop = LengthRatioProperty(A.segment(J), B.segment(I), 1)
        self.assertIn(prop, self.explainer.context)

class RomanticsOfGeometry4594Auxiliary(ExplainerTest):
    def createScene(self):
        scene = Scene()

        triangle = scene.nondegenerate_triangle(labels=('A', 'B', 'C'))
        A, B, C = triangle.points
        A.segment(B).perpendicular_constraint(A.segment(C), comment='Given: AB ⟂ AC')
        I = scene.incentre_point(triangle, label='I')
        J = scene.orthocentre_point(Scene.Triangle((A, B, I)), label='J')

        return scene

    def explainer_options(self):
        return {'max_layer': 'auxiliary'}

    def testPointOnLine(self):
        A = self.scene.get('A')
        B = self.scene.get('B')
        I = self.scene.get('I')
        J = self.scene.get('J')
        prop = LengthRatioProperty(A.segment(J), B.segment(I), 1)
        self.assertIn(prop, self.explainer.context)
