from sandbox import Scene
from sandbox.property import EquilateralTriangleProperty
from sandbox.util import LazyComment

from .base import ExplainerTest

class NapoleonOutward(ExplainerTest):
    def createScene(self):
        scene = Scene()

        triangle = scene.nondegenerate_triangle(labels=['A', 'B', 'C'])
        A, B, C = triangle.points

        def napoleonic(A, B, C):
            circleAB = A.circle_through(B, layer='invisible')
            circleBA = B.circle_through(A, layer='invisible')
            V = circleAB.intersection_point(circleBA, label=C.label + '1')
            equilateral = Scene.Triangle((A, B, V))
            A.scene.equilateral_constraint(equilateral, comment=LazyComment('Given: %s is equilateral', equilateral))
            line = A.line_through(B, layer='auxiliary')
            V.opposite_side_constraint(C, line, comment=LazyComment('Given: %s is outward of %s', V, triangle))
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
            circleAB = A.circle_through(B, layer='invisible')
            circleBA = B.circle_through(A, layer='invisible')
            V = circleAB.intersection_point(circleBA, label=C.label + '1')
            equilateral = Scene.Triangle((A, B, V))
            A.scene.equilateral_constraint(equilateral, comment=LazyComment('Given: %s is equilateral', equilateral))
            line = A.line_through(B, layer='auxiliary')
            V.same_side_constraint(C, line, comment=LazyComment('Given: %s is inward of %s', V, triangle))
            D = scene.incentre_point(equilateral, label=C.label + '2')

        napoleonic(A, B, C)
        napoleonic(C, A, B)
        napoleonic(B, C, A)

        return scene

    def testEquilateral(self):
        prop = EquilateralTriangleProperty((self.scene.get('A2'), self.scene.get('B2'), self.scene.get('C2')))
        self.assertNotIn(prop, self.explainer.context)

class NapoleonInwardPlusTrigonometry(NapoleonInward):
    def explainer_options(self):
        return {'trigonometric': True}

    def testEquilateral(self):
        prop = EquilateralTriangleProperty((self.scene.get('A2'), self.scene.get('B2'), self.scene.get('C2')))
        self.assertIn(prop, self.explainer.context)

class NapoleonInwardPlusAdvanced(NapoleonInward):
    def explainer_options(self):
        return {'advanced': True}

    def testEquilateral(self):
        prop = EquilateralTriangleProperty((self.scene.get('A2'), self.scene.get('B2'), self.scene.get('C2')))
        self.assertIn(prop, self.explainer.context)
