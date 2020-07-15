import time
import unittest

from sandbox import Scene
from sandbox.property import EqualLengthRatiosProperty, LengthRatioProperty
from sandbox.propertyset import LengthRatioPropertySet
from sandbox.rules.abstract import PredefinedPropertyRule

class FakeReason:
    def __init__(self):
        self.cost = 1
        self.premises = []
        self.all_premises = {}
        self.rule = PredefinedPropertyRule.instance()
        self.generation = 0
        self.obsolete = False

    def reset_premises(self):
        pass

def add_ratio(ratios, prop):
    prop.reason = FakeReason()
    ratios.add(prop)

class LengthRatioPropertySetTest(unittest.TestCase):
    def setUp(self):
        scene = Scene()
        A = scene.free_point(label='A')
        B = scene.free_point(label='B')
        C = scene.free_point(label='C')
        D = scene.free_point(label='D')
        E = scene.free_point(label='E')
        F = scene.free_point(label='F')
        G = scene.free_point(label='G')
        H = scene.free_point(label='H')
        self.AB = A.segment(B)
        self.CD = C.segment(D)
        self.EF = E.segment(F)
        self.GH = G.segment(H)
        self.startTime = time.time()

    def tearDown(self):
        print('%s took %.3f' % (self.id(), time.time() - self.startTime))

    def test1(self):
        ratios = LengthRatioPropertySet()
        add_ratio(ratios, EqualLengthRatiosProperty(self.AB, self.CD, self.EF, self.GH))
        add_ratio(ratios, EqualLengthRatiosProperty(self.AB, self.CD, self.GH, self.EF))
        prop = ratios.equality_property((self.GH, self.EF), (self.EF, self.GH))
        self.assertEqual(str(prop.reason.comment), '|G H| / |E F| = |A B| / |C D| = |E F| / |G H|')
        self.assertEqual(len(prop.reason.premises), 2)

    def test2(self):
        ratios = LengthRatioPropertySet()
        add_ratio(ratios, EqualLengthRatiosProperty(self.AB, self.CD, self.EF, self.GH))
        add_ratio(ratios, LengthRatioProperty(self.AB, self.CD, 2))
        comment, premises = ratios.value_explanation((self.EF, self.GH))
        self.assertEqual(str(comment), '|E F| / |G H| = |A B| / |C D| = 2')
        self.assertEqual(len(premises), 2)

    def test3(self):
        ratios = LengthRatioPropertySet()
        add_ratio(ratios, EqualLengthRatiosProperty(self.AB, self.CD, self.EF, self.GH))
        add_ratio(ratios, LengthRatioProperty(self.AB, self.CD, 1))
        add_ratio(ratios, LengthRatioProperty(self.GH, self.EF, 1))
        comment, premises = ratios.value_explanation((self.EF, self.GH))
        self.assertEqual(str(comment), '|E F| / |G H| = 1')
        self.assertEqual(len(premises), 1)

    def test4(self):
        ratios = LengthRatioPropertySet()
        add_ratio(ratios, EqualLengthRatiosProperty(self.AB, self.CD, self.EF, self.GH))
        add_ratio(ratios, EqualLengthRatiosProperty(self.CD, self.AB, self.GH, self.EF))
        add_ratio(ratios, EqualLengthRatiosProperty(self.AB, self.CD, self.GH, self.EF))
        prop = ratios.equality_property((self.CD, self.AB), (self.EF, self.GH))
        self.assertEqual(str(prop.reason.comment), '|C D| / |A B| = |G H| / |E F| = |A B| / |C D| = |E F| / |G H|')
        self.assertEqual(len(prop.reason.premises), 3)

    def test5_1(self):
        ratios = LengthRatioPropertySet()
        add_ratio(ratios, EqualLengthRatiosProperty(self.AB, self.CD, self.EF, self.GH))
        add_ratio(ratios, EqualLengthRatiosProperty(self.CD, self.AB, self.GH, self.EF))
        add_ratio(ratios, LengthRatioProperty(self.AB, self.CD, 2))
        comment, premises = ratios.value_explanation((self.EF, self.GH))
        self.assertEqual(str(comment), '|E F| / |G H| = |A B| / |C D| = 2')
        self.assertEqual(len(premises), 2)

    def test5_2(self):
        ratios = LengthRatioPropertySet()
        add_ratio(ratios, EqualLengthRatiosProperty(self.AB, self.CD, self.EF, self.GH))
        add_ratio(ratios, EqualLengthRatiosProperty(self.CD, self.AB, self.GH, self.EF))
        add_ratio(ratios, LengthRatioProperty(self.AB, self.CD, 2))
        comment, premises = ratios.value_explanation((self.GH, self.EF))
        self.assertEqual(str(comment), '|G H| / |E F| = |C D| / |A B| = 1/2')
        self.assertEqual(len(premises), 2)

    def test6(self):
        ratios = LengthRatioPropertySet()
        add_ratio(ratios, EqualLengthRatiosProperty(self.AB, self.CD, self.EF, self.GH))
        add_ratio(ratios, EqualLengthRatiosProperty(self.CD, self.AB, self.GH, self.EF))
        add_ratio(ratios, LengthRatioProperty(self.AB, self.CD, 1))
        prop = ratios.equality_property((self.EF, self.GH), (self.GH, self.EF))

        self.assertEqual(str(prop.reason.comment), '|E F| / |G H| = |A B| / |C D| = 1 = |C D| / |A B| = |G H| / |E F|')
        self.assertEqual(len(prop.reason.premises), 3)
