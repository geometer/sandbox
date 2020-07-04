import sympy as sp

from .. import Scene
from ..property import AngleValueProperty, IsoscelesTriangleProperty, LengthRatioProperty, ProportionalLengthsProperty, PerpendicularSegmentsProperty, PointsCollinearityProperty
from ..util import Comment

from .abstract import Rule, source_type

@source_type(PerpendicularSegmentsProperty)
class RightAngledTriangleMedianRule(Rule):
    """
    In a right-angled triangle, the median to the hypotenuse is equal to half of the hypotenuse
    """
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
                Comment(
                    'median in right-angled $%{triangle:triangle}$ is equal to half of the hypotenuse',
                    {'triangle': Scene.Triangle(vertex, pt0, pt1)}
                ),
                [prop, col, half0, half1]
            )

@source_type(AngleValueProperty)
class Triangle30_60_90SidesRule(Rule):
    """
    Sides ratios in a right-angled triangle with angles 60º and 30º
    """
    def __init__(self, context):
        super().__init__(context)
        self.processed = {}

    def accepts(self, prop):
        return prop.degree == 90 and prop.angle.vertex

    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0x3:
            return

        original = mask
        vertex = prop.angle.vertex
        triangle = Scene.Triangle(vertex, *prop.angle.endpoints)
        for bit in (1, 2):
            if mask & bit:
                continue
            value = self.context.angle_value_property(triangle.angles[bit])
            if value is None:
                continue
            mask |= bit

            oppo = triangle.sides[bit]
            adj = triangle.sides[3 - bit]
            hypot = triangle.sides[0]
            if value.degree == 30:
                pt0 = triangle.points[bit]
                pt1 = triangle.points[3 - bit]
                oppo_ratio = 2
                adj_ratio = 2 / sp.sqrt(3)
                catheti = (adj, oppo)
                catheti_pattern = 'catheti adjacent and opposite to the $%{degree:deg}$ angle in $%{triangle:triangle}$'
            elif value.degree == 60:
                pt0 = triangle.points[3 - bit]
                pt1 = triangle.points[bit]
                oppo_ratio = 2 / sp.sqrt(3)
                adj_ratio = 2
                catheti = (oppo, adj)
                catheti_pattern = 'catheti opposite and adjacent to the $%{degree:deg}$ angle in $%{triangle:triangle}$'
            else:
                mask = 0x3
                continue
            params = {'deg': value.degree, 'triangle': triangle}
            yield (
                LengthRatioProperty(hypot, oppo, oppo_ratio),
                Comment('hypotenuse and cathetus opposite to the $%{degree:deg}$ angle in $%{triangle:triangle}$', params),
                [prop, value]
            )
            yield (
                LengthRatioProperty(hypot, adj, adj_ratio),
                Comment('hypotenuse and cathetus adjacent to the $%{degree:deg}$ angle in $%{triangle:triangle}$', params),
                [prop, value]
            )
            yield (
                LengthRatioProperty(*catheti, sp.sqrt(3)),
                Comment(catheti_pattern, params),
                [prop, value]
            )

        if mask != original:
            self.processed[prop] = mask

@source_type(IsoscelesTriangleProperty)
class Triangle30_30_120SidesRule(Rule):
    """
    Sides ratios in an isosceles triangle with base angles 30º
    """
    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def accepts(self, prop):
        return prop not in self.processed

    def apply(self, prop):
        value = self.context.angle_value_property(prop.apex.angle(*prop.base.points))
        if value is None:
            return
        self.processed.add(prop)
        if value.degree != 120:
            return
        for pt in prop.base.points:
            yield (
                LengthRatioProperty(prop.base, prop.apex.segment(pt), sp.sqrt(3)),
                Comment(
                    'ratio of leg and base in isosceles $%{triangle:triangle}$ with base angle $%{degree:base}$',
                    {'triangle': prop.triangle, 'base': 30}
                ),
                [prop, value]
            )

@source_type(IsoscelesTriangleProperty)
class Triangle72_72_36SidesRule(Rule):
    """
    Sides ratios in an isosceles triangle with base angles 72º
    """
    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def accepts(self, prop):
        return prop not in self.processed

    def apply(self, prop):
        value = self.context.angle_value_property(prop.apex.angle(*prop.base.points))
        if value is None:
            return
        self.processed.add(prop)
        if value.degree != 36:
            return
        for pt in prop.base.points:
            yield (
                LengthRatioProperty(prop.apex.segment(pt), prop.base, (sp.sqrt(5) + 1) / 2),
                Comment(
                    'ratio of leg and base in isosceles $%{triangle:triangle}$ with base angle $%{degree:base}$',
                    {'triangle': prop.triangle, 'base': 72}
                ),
                [prop, value]
            )

@source_type(IsoscelesTriangleProperty)
class Triangle36_36_108SidesRule(Rule):
    """
    Sides ratios in an isosceles triangle with base angles 36º
    """
    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def accepts(self, prop):
        return prop not in self.processed

    def apply(self, prop):
        value = self.context.angle_value_property(prop.apex.angle(*prop.base.points))
        if value is None:
            return
        self.processed.add(prop)
        if value.degree != 108:
            return
        for pt in prop.base.points:
            yield (
                LengthRatioProperty(prop.base, prop.apex.segment(pt), (sp.sqrt(5) + 1) / 2),
                Comment(
                    'ratio of leg and base in isosceles $%{triangle:triangle}$ with base angle $%{degree:base}$',
                    {'triangle': prop.triangle, 'base': 36}
                ),
                [prop, value]
            )
