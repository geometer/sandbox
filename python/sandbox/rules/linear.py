import itertools

from sandbox.property import *
from sandbox.util import LazyComment, divide

from .abstract import Rule, SingleSourceRule

class SumAndRatioOfTwoAnglesRule(SingleSourceRule):
    """
    If the sum and the ratio of two angles are known, we can find the values
    """
    property_type = SumOfAnglesProperty

    def apply(self, prop):
        ar = self.context.angle_ratio_property(prop.angles[0], prop.angles[1])
        if ar is None or prop.reason.obsolete and ar.reason.obsolete:
            return
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
    def sources(self):
        return [(s0, s1) for (s0, s1) in itertools.combinations(self.context.list(SumOfAnglesProperty), 2) if s0.degree == s1.degree]

    def apply(self, src):
        sum0, sum1 = src

        for eq0, eq1 in itertools.product(sum0.angles, sum1.angles):
            other0 = next(ang for ang in sum0.angles if ang != eq0)
            other1 = next(ang for ang in sum1.angles if ang != eq1)
            if other0 == other1:
                continue
            if eq0 == eq1:
                if sum0.reason.obsolete and sum1.reason.obsolete:
                    continue
                yield (
                    AngleRatioProperty(other0, other1, 1),
                    LazyComment('%s + %s = %sº = %s + %s', other0, eq0, sum0.degree, other1, eq1),
                    [sum0, sum1]
                )
            else:
                ca = self.context.angle_ratio_property(eq0, eq1)
                if ca is None:
                    continue
                if ca.value != 1:
                    return
                if sum0.reason.obsolete and sum1.reason.obsolete and ca.reason.obsolete:
                    continue
                yield (
                    AngleRatioProperty(other0, other1, 1),
                    LazyComment(
                        '%s + %s = %sº = %s + %s and %s = %s',
                        other0, eq0, sum0.degree, other1, eq1, eq0, eq1
                    ),
                    [sum0, sum1, ca]
                )
