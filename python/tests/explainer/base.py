import time
import unittest

from sandbox.explainer import Explainer
from sandbox.propertyset import PropertySet

class ExplainerTest(unittest.TestCase):
    def extra_rules(self):
        return {}

    def context_points(self, scene):
        return scene.points(max_layer='user')

    def setUp(self):
        self.startTime = time.time()
        self.scene = self.createScene()
        self.explainer = Explainer(self.scene, context=PropertySet(self.context_points(self.scene)), extra_rules=self.extra_rules())
        self.explainer.explain()

    def tearDown(self):
        print('%s took %.3f' % (self.id(), time.time() - self.startTime))
