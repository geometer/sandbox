import time
import unittest

from sandbox.explainer import Explainer

class ExplainerTest(unittest.TestCase):
    def setUp(self):
        self.startTime = time.time()
        self.scene = self.createScene()
        self.explainer = Explainer(self.scene)
        self.explainer.explain()

    def tearDown(self):
        print('%s took %.3f' % (self.id(), time.time() - self.startTime))
