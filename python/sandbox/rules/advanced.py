import sympy as sp

from .. import Scene
from ..property import AngleValueProperty, IsoscelesTriangleProperty, LengthRatioProperty, ProportionalLengthsProperty, PerpendicularSegmentsProperty, PointsCollinearityProperty
from ..util import LazyComment

from .abstract import SingleSourceRule

class RightAngledTriangleMedianRule(SingleSourceRule):
    """
    In a right-angled triangle, the median to the hypotenuse is equal to half of the hypotenuse
    """
    property_type = PerpendicularSegmentsProperty

    def apply(self, prop):
        vertex = next((pt for pt in prop.segments[0].points if pt in prop.segments[1].points), None)
        if vertex is None:
            return
        pt0 = next(pt for pt in prop.segments[0].points if pt != vertex)
        pt1 = next(pt for pt in prop.segments[1].points if pt != vertex)
        hypot = pt0.segment(pt1)
        for med in self.context.collinear_points(hypot):
            col = self.context.collinearity_property(med, *hypot.points)
            half0, value = self.context.length_ratio_property_and_value(hypot, med.segment(hypot.points[0]), True)
            if value != 2:
                continue
            half1, value = self.context.length_ratio_property_and_value(hypot, med.segment(hypot.points[1]), True)
            if value != 2:
                continue
            yield (
                ProportionalLengthsProperty(hypot, med.segment(vertex), 2),
                LazyComment('Median in right-angled %s is equal to half of the hypotenuse', Scene.Triangle(vertex, pt0, pt1)),
                [prop, col, half0, half1]
            )

class Triangle30_60_90SidesRule(SingleSourceRule):
    """
    Sides ratios in a right-angled triangle with angles 60º and 30º
    """
    property_type = AngleValueProperty

    def accepts(self, prop):
        return prop.degree == 90 and prop.angle.vertex

    def apply(self, prop):
        vertex = prop.angle.vertex
        pt0 = prop.angle.vectors[0].end
        pt1 = prop.angle.vectors[1].end
        value = self.context.angle_value_property(pt0.angle(vertex, pt1))
        if value is None or value.degree not in (30, 60) or prop.reason.obsolete and value.reason.obsolete:
            return
        hypot = pt0.segment(pt1)
        long_leg = vertex.segment(pt0 if value.degree == 30 else pt1)
        short_leg = vertex.segment(pt1 if value.degree == 30 else pt0)
        yield (
            LengthRatioProperty(hypot, short_leg, 2),
            LazyComment('Hypotenuse and cathetus opposite the 30º angle'),
            [prop, value]
        )
        yield (
            LengthRatioProperty(hypot, long_leg, 2 / sp.sqrt(3)),
            LazyComment('Hypotenuse and cathetus opposite the 60º angle'),
            [prop, value]
        )
        yield (
            LengthRatioProperty(long_leg, short_leg, sp.sqrt(3)),
            LazyComment('Catheti opposite 60º and 30º angles'),
            [prop, value]
        )

class Triangle30_30_120SidesRule(SingleSourceRule):
    """
    Sides ratios in an isosceles triangle with base angles 30º
    """
    property_type = IsoscelesTriangleProperty

    def apply(self, prop):
        value = self.context.angle_value_property(prop.apex.angle(*prop.base.points))
        if value is None or value.degree != 120 or prop.reason.obsolete and value.reason.obsolete:
            return
        for pt in prop.base.points:
            yield (
                LengthRatioProperty(prop.base, prop.apex.segment(pt), sp.sqrt(3)),
                LazyComment('Ratio of base and leg in isosceles %s with base angle = 30º', prop.triangle),
                [prop, value]
            )
