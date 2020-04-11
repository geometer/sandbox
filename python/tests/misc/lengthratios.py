import time
import unittest

from sandbox.property import EqualLengthRatiosProperty, LengthRatioProperty
from sandbox.propertyset import LengthRatioPropertySet

class LengthRatioPropertySetTest(unittest.TestCase):
    def setUp(self):
        self.startTime = time.time()

    def tearDown(self):
        print('%s took %.3f' % (self.id(), time.time() - self.startTime))

    def test1(self):
        ratios = LengthRatioPropertySet()
        ratios.add(EqualLengthRatiosProperty('AB', 'CD', 'EF', 'GH'))
        ratios.add(EqualLengthRatiosProperty('AB', 'CD', 'GH', 'EF'))
        comment, premises = ratios.explanation(('GH', 'EF'), ('EF', 'GH'))
        self.assertEqual(str(comment), '|GH| / |EF| = |AB| / |CD| = |EF| / |GH|')
        self.assertEqual(len(premises), 2)

    def test2(self):
        ratios = LengthRatioPropertySet()
        ratios.add(EqualLengthRatiosProperty('AB', 'CD', 'EF', 'GH'))
        ratios.add(LengthRatioProperty('AB', 'CD', 2))
        comment, premises = ratios.value_explanation(('EF', 'GH'))
        self.assertEqual(str(comment), '|EF| / |GH| = |AB| / |CD| = 2')
        self.assertEqual(len(premises), 2)

    def test3(self):
        ratios = LengthRatioPropertySet()
        ratios.add(EqualLengthRatiosProperty('AB', 'CD', 'EF', 'GH'))
        ratios.add(LengthRatioProperty('AB', 'CD', 1))
        ratios.add(LengthRatioProperty('GH', 'EF', 1))
        comment, premises = ratios.value_explanation(('EF', 'GH'))
        self.assertEqual(str(comment), '|EF| / |GH| = 1')
        self.assertEqual(len(premises), 1)

    def test4(self):
        ratios = LengthRatioPropertySet()
        ratios.add(EqualLengthRatiosProperty('AB', 'CD', 'EF', 'GH'))
        ratios.add(EqualLengthRatiosProperty('CD', 'AB', 'GH', 'EF'))
        ratios.add(EqualLengthRatiosProperty('AB', 'CD', 'GH', 'EF'))
        comment, premises = ratios.explanation(('CD', 'AB'), ('EF', 'GH'))
        self.assertEqual(str(comment), '|CD| / |AB| = |GH| / |EF| = |AB| / |CD| = |EF| / |GH|')
        self.assertEqual(len(premises), 3)

    def test5_1(self):
        ratios = LengthRatioPropertySet()
        ratios.add(EqualLengthRatiosProperty('AB', 'CD', 'EF', 'GH'))
        ratios.add(EqualLengthRatiosProperty('CD', 'AB', 'GH', 'EF'))
        ratios.add(LengthRatioProperty('AB', 'CD', 2))
        comment, premises = ratios.value_explanation(('EF', 'GH'))
        self.assertEqual(str(comment), '|EF| / |GH| = |AB| / |CD| = 2')
        self.assertEqual(len(premises), 2)

    def test5_2(self):
        ratios = LengthRatioPropertySet()
        ratios.add(EqualLengthRatiosProperty('AB', 'CD', 'EF', 'GH'))
        ratios.add(EqualLengthRatiosProperty('CD', 'AB', 'GH', 'EF'))
        ratios.add(LengthRatioProperty('AB', 'CD', 2))
        comment, premises = ratios.value_explanation(('GH', 'EF'))
        self.assertEqual(str(comment), '|GH| / |EF| = |CD| / |AB| = 1/2')
        self.assertEqual(len(premises), 2)

    def test6(self):
        ratios = LengthRatioPropertySet()
        ratios.add(EqualLengthRatiosProperty('AB', 'CD', 'EF', 'GH'))
        ratios.add(EqualLengthRatiosProperty('CD', 'AB', 'GH', 'EF'))
        ratios.add(LengthRatioProperty('AB', 'CD', 1))
        comment, premises = ratios.explanation(('EF', 'GH'), ('GH', 'EF'))

        self.assertEqual(str(comment), '|EF| / |GH| = |AB| / |CD| = 1 = |CD| / |AB| = |GH| / |EF|')
        self.assertEqual(len(premises), 4)
