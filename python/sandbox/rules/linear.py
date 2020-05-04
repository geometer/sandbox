import itertools

from sandbox.property import *
from sandbox.util import LazyComment, divide

from .abstract import Rule, SingleSourceRule

class SumAndRatioOfTwoAnglesRule(SingleSourceRule):
    """
    If the sum and the ratio of two angles are known, we can find the values
    """
    property_type = SumOfAnglesProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def accepts(self, prop):
        return prop not in self.processed

    def apply(self, prop):
        ar = self.context.angle_ratio_property(prop.angles[0], prop.angles[1])
        if ar is None:
            return
        self.processed.add(prop)
        value1 = divide(prop.degree, 1 + ar.value)
        value0 = prop.degree - value1
        if ar.value == 1:
            comment0 = LazyComment('2 %s = %s + %s = %sº', ar.angle0, ar.angle0, ar.angle1, prop.degree)
            comment1 = LazyComment('2 %s = %s + %s = %sº', ar.angle1, ar.angle1, ar.angle0, prop.degree)
        else:
            comment0 = LazyComment('%s + %s / %s = %s + %s = %sº', ar.angle0, ar.angle0, ar.value, ar.angle0, ar.angle1, prop.degree)
            comment1 = LazyComment('%s + %s %s = %s + %s = %sº', ar.angle1, ar.value, ar.angle1, ar.angle1, ar.angle0, prop.degree)
        yield (AngleValueProperty(ar.angle0, value0), comment0, [prop, ar])
        yield (AngleValueProperty(ar.angle1, value1), comment1, [prop, ar])

class EqualSumsOfAnglesRule(Rule):
    def __init__(self, context):
        super().__init__(context)
        self.processed = {} # prop => bit mask

    def sources(self):
        return [(s0, s1) for (s0, s1) in itertools.combinations(self.context.list(SumOfAnglesProperty), 2) if s0.degree == s1.degree]

    def apply(self, src):
        mask = self.processed.get(src, 0)
        if mask == 0xF:
            return

        sum0, sum1 = src
        original = mask
        for index, (eq0, eq1) in enumerate(itertools.product(sum0.angles, sum1.angles)):
            bit = 1 << index
            if mask & bit:
                continue

            other0 = next(ang for ang in sum0.angles if ang != eq0)
            other1 = next(ang for ang in sum1.angles if ang != eq1)
            if other0 == other1:
                mask |= bit
                mask |= 8 // bit # 0x1 <=> 0x8, 0x2 <=> 0x4
                continue
            if eq0 == eq1:
                mask |= bit
                yield (
                    AngleRatioProperty(other0, other1, 1),
                    LazyComment('%s + %s = %sº = %s + %s', other0, eq0, sum0.degree, other1, eq1),
                    [sum0, sum1]
                )
            else:
                ca = self.context.angle_ratio_property(eq0, eq1)
                if ca is None:
                    continue
                mask |= bit
                if ca.value != 1:
                    mask |= 8 // bit # 0x1 <=> 0x8, 0x2 <=> 0x4
                    continue
                yield (
                    AngleRatioProperty(other0, other1, 1),
                    LazyComment(
                        '%s + %s = %sº = %s + %s and %s',
                        other0, eq0, sum0.degree, other1, eq1, ca
                    ),
                    [sum0, sum1, ca]
                )

        if original != mask:
            self.processed[src] = mask
