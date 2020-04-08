from sandbox import Scene
from sandbox.property import EquilateralTriangleProperty
from sandbox.util import _comment

from .base import ExplainerTest

class NapoleonOutward(ExplainerTest):
    def createScene(self):
        scene = Scene()

        A, B, C = scene.triangle(labels=['A', 'B', 'C'])

        def napoleonic(A, B, C):
            V = A.scene.free_point(label=C.label + '1')
            A.scene.equilateral_constraint((A, B, V), comment=_comment('Given: △ %s %s %s is an equilateral triangle', V, A, B))
            line = A.line_through(B, layer='auxiliary')
            V.opposite_side_constraint(C, line, comment=_comment('Given: %s is outward of △ %s %s %s', V, A, B, C))
            D = scene.incentre_point((A, B, V), label=C.label + '2')

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

        A, B, C = scene.triangle(labels=['A', 'B', 'C'])

        def napoleonic(A, B, C):
            V = A.scene.free_point(label=C.label + '1')
            A.scene.equilateral_constraint((A, B, V), comment=_comment('Given: △ %s %s %s is an equilateral triangle', V, A, B))
            line = A.line_through(B, layer='auxiliary')
            V.same_side_constraint(C, line, comment=_comment('Given: %s is inward of △ %s %s %s', V, A, B, C))
            D = scene.incentre_point((A, B, V), label=C.label + '2')

        napoleonic(A, B, C)
        napoleonic(C, A, B)
        napoleonic(B, C, A)

        return scene

    def testEquilateral(self):
        prop = EquilateralTriangleProperty((self.scene.get('A2'), self.scene.get('B2'), self.scene.get('C2')))
        self.assertNotIn(prop, self.explainer.context)

class NapoleonInwardPlusTrigonometry(NapoleonInward):
    def explainer_options(self):
        return {'trigonometric'}

    def testEquilateral(self):
        prop = EquilateralTriangleProperty((self.scene.get('A2'), self.scene.get('B2'), self.scene.get('C2')))
        self.assertIn(prop, self.explainer.context)

class NapoleonInwardPlusAdvanced(NapoleonInward):
    def explainer_options(self):
        return {'advanced'}

    def testEquilateral(self):
        prop = EquilateralTriangleProperty((self.scene.get('A2'), self.scene.get('B2'), self.scene.get('C2')))
        self.assertIn(prop, self.explainer.context)
