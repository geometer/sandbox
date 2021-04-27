from sandbox import Scene
from sandbox.property import EquilateralTriangleProperty
from sandbox.util import Comment

from .base import ExplainerTest

class NapoleonOutward(ExplainerTest):
    def createScene(self):
        scene = Scene()

        triangle = scene.nondegenerate_triangle(labels=['A', 'B', 'C'])
        A, B, C = triangle.points

        def napoleonic(A, B, C):
            equilateral = scene.equilateral_triangle(A, B, C.label + '1')
            _, _, V = equilateral.points
            comment = Comment('$%{triangle:equilateral}$ is facing away from $%{triangle:triangle}$', {'equilateral': equilateral, 'triangle': triangle})
            V.opposite_side_constraint(C, A.segment(B), comment=comment)
            D = scene.incentre_point(equilateral, label=C.label + '2')

        napoleonic(A, B, C)
        napoleonic(C, A, B)
        napoleonic(B, C, A)

        return scene

    def testEquilateral(self):
        prop = EquilateralTriangleProperty((self.scene.get('A2'), self.scene.get('B2'), self.scene.get('C2')))
        self.assertIn(prop, self.explainer.context)

class NapoleonInward(ExplainerTest):
    def createScene(self):
        scene = Scene()

        triangle = scene.nondegenerate_triangle(labels=['A', 'B', 'C'])
        A, B, C = triangle.points

        def napoleonic(A, B, C):
            equilateral = scene.equilateral_triangle(A, B, C.label + '1')
            _, _, V = equilateral.points
            comment = Comment('$%{triangle:equilateral}$ is facing into $%{triangle:triangle}$', {'equilateral': equilateral, 'triangle': triangle})
            V.same_side_constraint(C, A.segment(B), comment=comment)
            D = scene.incentre_point(equilateral, label=C.label + '2')

        napoleonic(A, B, C)
        napoleonic(C, A, B)
        napoleonic(B, C, A)

        return scene

    def testEquilateral(self):
        prop = EquilateralTriangleProperty((self.scene.get('A2'), self.scene.get('B2'), self.scene.get('C2')))
        self.assertIn(prop, self.explainer.context)

class NapoleonInwardPlusTrigonometry(NapoleonInward):
    def extra_rules(self):
        return {'trigonometric'}

    def testEquilateral(self):
        prop = EquilateralTriangleProperty((self.scene.get('A2'), self.scene.get('B2'), self.scene.get('C2')))
        self.assertIn(prop, self.explainer.context)

class NapoleonInwardPlusAdvanced(NapoleonInward):
    def extra_rules(self):
        return {'advanced'}

    def testEquilateral(self):
        prop = EquilateralTriangleProperty((self.scene.get('A2'), self.scene.get('B2'), self.scene.get('C2')))
        self.assertIn(prop, self.explainer.context)