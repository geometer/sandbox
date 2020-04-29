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
        if self.context.angle_value_property(prop.angle0) or self.context.angle_value_property(prop.angle1):
            return
        ar = self.context.angle_ratio_property(prop.angle0, prop.angle1)
        if ar is None or prop.reason.obsolete and ar.reason.obsolete:
            return
        value1 = divide(prop.degree, 1 + ar.value)
        value0 = prop.degree - value1
        if ar.value == 1:
            comment0 = LazyComment('%s + %s = %s + %s = %sº', ar.angle0, ar.angle0, ar.angle0, ar.angle1, prop.degree)
            comment1 = LazyComment('%s + %s = %s + %s = %sº', ar.angle1, ar.angle1, ar.angle1, ar.angle0, prop.degree)
        else:
            comment0 = LazyComment('%s + %s / %s = %s + %s = %sº', ar.angle0, ar.angle0, ar.value, ar.angle0, ar.angle1, prop.degree)
            comment1 = LazyComment('%s + %s %s = %s + %s = %sº', ar.angle1, ar.value, ar.angle1, ar.angle1, ar.angle0, prop.degree)
        yield (AngleValueProperty(ar.angle0, value0), comment0, [prop, ar])
        yield (AngleValueProperty(ar.angle1, value1), comment1, [prop, ar])
