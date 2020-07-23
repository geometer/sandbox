import time
import unittest

from sandbox.explainer import Explainer

class ExplainerTest(unittest.TestCase):
    def extra_rules(self):
        return {}

    def setUp(self):
        self.startTime = time.time()
        self.scene = self.createScene()
        self.explainer = Explainer(self.scene, extra_rules=self.extra_rules())
        self.explainer.explain()

    def tearDown(self):
        print('%s took %.3f' % (self.id(), time.time() - self.startTime))
