import time
import unittest

from sandbox.explainer import Explainer

class ExplainerTest(unittest.TestCase):
    def explainer_options(self):
        return {}

    def setUp(self):
        self.startTime = time.time()
        self.scene = self.createScene()
        self.explainer = Explainer(self.scene, options=self.explainer_options())
        self.explainer.explain()

    def tearDown(self):
        print('%s took %.3f' % (self.id(), time.time() - self.startTime))
