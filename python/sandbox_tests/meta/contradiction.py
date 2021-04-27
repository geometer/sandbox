import time
import unittest

from sandbox import Scene
from sandbox.explainer import Explainer
from sandbox.propertyset import ContradictionError

class ContradictionTest(unittest.TestCase):
    def setUp(self):
        self.startTime = time.time()

    def tearDown(self):
        print('%s took %.3f' % (self.id(), time.time() - self.startTime))

    def testTwoObtuseAngles(self):
        scene = Scene()

        A, B, C = scene.nondegenerate_triangle(labels=('A', 'B', 'C')).points
        A.angle(B, C).is_obtuse_constraint()
        B.angle(A, C).is_obtuse_constraint()

        explainer = Explainer(scene)
        self.assertRaises(ContradictionError, explainer.explain)
