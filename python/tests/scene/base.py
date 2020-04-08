import time
import unittest

class SceneTest(unittest.TestCase):
    def setUp(self):
        self.startTime = time.time()
        self.scene = self.createScene()

    def tearDown(self):
        print('%s took %.3f' % (self.id(), time.time() - self.startTime))
