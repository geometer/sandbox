from .property import AngleValueProperty, SumOfAnglesProperty
from .util import _comment, divide

class SumOfAnglesRule:
    property_type = SumOfAnglesProperty

    def __init__(self, context):
        self.context = context

    def apply(self, prop):
        ar = self.context.angles_ratio_property(prop.angle0, prop.angle1)
        if ar is None or prop.reason.obsolete and ar.reason.obsolete:
            return
        value1 = divide(prop.degree, 1 + ar.value)
        value0 = prop.degree - value1
        if ar.value == 1:
            comment0 = _comment('%s + %s = %s', ar.angle0, ar.angle0, prop.degree),
            comment1 = _comment('%s + %s = %s', ar.angle1, ar.angle1, prop.degree),
        else:
            comment0 = _comment('%s + %s / %s = %s', ar.angle0, ar.angle0, ar.value, prop.degree),
            comment1 = _comment('%s + %s %s = %s', ar.angle1, ar.value, ar.angle1, prop.degree),
        yield (AngleValueProperty(ar.angle0, value0), comment0, [prop, ar])
        yield (AngleValueProperty(ar.angle1, value1), comment1, [prop, ar])
