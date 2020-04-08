from sandbox.property import *
from sandbox.util import _comment

from .basic import SingleSourceRule

class RightAngledTriangleMedianRule(SingleSourceRule):
    """
    In a right-angled triangle, the median to the hypotenuse is equal to half of the hypotenuse
    """
    property_type = PerpendicularVectorsProperty

    def apply(self, prop, context):
        vertex = next((pt for pt in prop.vector0.points if pt in prop.vector1.points), None)
        if vertex is None:
            return
        pt0 = next(pt for pt in prop.vector0.points if pt != vertex)
        pt1 = next(pt for pt in prop.vector1.points if pt != vertex)
        hypot = pt0.segment(pt1)
        for col in [p for p in context.list(PointsCollinearityProperty, [hypot]) if p.collinear]:
            med = next(pt for pt in col.points if pt not in hypot.points)
            half0, value = context.lengths_ratio_property_and_value(hypot, med.segment(hypot.points[0]))
            if value != 2:
                continue
            half1, value = context.lengths_ratio_property_and_value(hypot, med.segment(hypot.points[1]))
            if value != 2:
                continue
            yield (
                LengthRatioProperty(hypot, med.segment(vertex), 2),
                _comment('Median in right-angled △ %s %s %s is equal to half of the hypotenuse', vertex, pt0, pt1),
                [prop, col, half0, half1]
            )
