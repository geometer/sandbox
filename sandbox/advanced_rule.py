from .property import *
from .rule import Rule
from .util import _comment

class RightAngledTriangleMedianRule(Rule):
    """
    In a right-angled triangle, the median to the hypotenuse is equal to half of the hypotenuse
    """
    def sources(self, context):
        return [p for p in context.nondegenerate_angle_value_properties() if p.angle.vertex and p.degree == 90]

    def apply(self, prop, context):
        hypot = prop.angle.vector0.end.segment(prop.angle.vector1.end)
        for col in [p for p in context.list(PointsCollinearityProperty, [hypot]) if p.collinear]:
            pt = next(pt for pt in col.points if pt not in hypot.points)
            half0, value = context.lengths_ratio_property_and_value(hypot, pt.segment(hypot.points[0]))
            if value != 2:
                continue
            half1, value = context.lengths_ratio_property_and_value(hypot, pt.segment(hypot.points[1]))
            if value != 2:
                continue
            yield (
                LengthRatioProperty(hypot, pt.segment(prop.angle.vertex), 2),
                _comment('Median in right-angled △ %s %s %s is equal to half of the hypotenuse', *prop.angle.points),
                [prop, col, half0, half1]
            )
