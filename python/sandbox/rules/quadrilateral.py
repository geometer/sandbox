import itertools
import sympy as sp

from ..property import *
from ..util import Comment

from .abstract import Rule, SingleSourceRule

class KnownAnglesToConvexQuadrilateralRule(SingleSourceRule):
    property_type = SameOrOppositeSideProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = {}

    def accepts(self, prop):
        return prop.same

    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0x3:
            return
        original = mask

        for (sp0, sp1), bit in ((prop.segment.points, 0x1), (reversed(prop.segment.points), 0x2)):
            if mask & bit:
                continue
            pt0, pt1 = prop.points
            av0 = self.context.angle_value_property(sp0.angle(sp1, pt0))
            if av0 is None:
                continue
            av1 = self.context.angle_value_property(sp1.angle(sp0, pt1))
            if av1 is None:
                continue
            mask |= bit

            sum_degree = av0.degree + av1.degree
            if sum_degree < 180:
                continue
            params = {
                'angle0': av0.angle,
                'angle1': av1.angle,
                'sum': sum_degree,
                '180': 180,
                'pt0': pt0,
                'pt1': pt1,
                'line': prop.segment
            }
            if sum_degree == 180:
                pattern = '$%{anglemeasure:angle0} + %{anglemeasure:angle1} = %{degree:sum}$, and points $%{point:pt0}$ and $%{point:pt1}$ are on the same side of $%{line:line}$'
            else:
                pattern = '$%{anglemeasure:angle0} + %{anglemeasure:angle1} = %{degree:sum} > %{degree:180}$, and points $%{point:pt0}$ and $%{point:pt1}$ are on the same side of $%{line:line}$'
            yield (
                ConvexQuadrilateralProperty(Scene.Polygon(pt0, sp0, sp1, pt1)),
                Comment(pattern, params),
                [av0, av1, prop]
            )

        if mask != original:
            self.processed[prop] = mask

class PointsToConvexQuadrilateralRule(Rule):
    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def sources(self):
        oppos = [p for p in self.context.list(SameOrOppositeSideProperty) if not p.same]
        for p0, p1 in itertools.combinations(oppos, 2):
            if set(p0.points) == set(p1.segment.points) and set(p1.points) == set(p0.segment.points):
                yield (p0, p1)

    def apply(self, src):
        if src in self.processed:
            return

        prop0, prop1 = src
        self.processed.add(src)
        self.processed.add((prop1, prop0))

        p0 = prop0.points
        p1 = prop0.segment.points
        quad = Scene.Polygon(p0[0], p1[0], p0[1], p1[1])
        yield (
            ConvexQuadrilateralProperty(quad),
            Comment(
                'both diagonals $%{segment:d0}$ and $%{segment:d1}$ divide quadrilateral $%{polygon:quad}$',
                {'d0': prop0.segment, 'd1': prop1.segment, 'quad': quad}
            ),
            [prop0, prop1]
        )

class SumOfAnglesOfConvexQuadrilateralRule(SingleSourceRule):
    property_type = ConvexQuadrilateralProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def accepts(self, prop):
        return prop not in self.processed

    def apply(self, prop):
        self.processed.add(prop)

        yield (
            SumOfAnglesProperty(*prop.quadrilateral.angles, degree=360),
            Comment('sum of angles of convex $%{polygon:quad}$', {'quad': prop.quadrilateral}),
            [prop]
        )

class ConvexQuadrilateralRule(SingleSourceRule):
    property_type = (ConvexQuadrilateralProperty, NondegenerateSquareProperty)

    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def accepts(self, prop):
        return prop not in self.processed

    def apply(self, prop):
        self.processed.add(prop)

        if isinstance(prop, NondegenerateSquareProperty):
            quad = prop.square
            pattern = '$%{polygon:quad}$ is a non-degenerate square'
        else:
            quad = prop.quadrilateral
            pattern = '$%{polygon:quad}$ is a convex quadrilateral'
        points = quad.points * 2
        comment = Comment(pattern, {'quad': quad})
        for i in range(0, 4):
            pts = [points[j] for j in range(i, i + 4)]
            yield (
                SameOrOppositeSideProperty(pts[0].segment(pts[1]), pts[2], pts[3], True),
                comment,
                [prop]
            )
        for i in range(0, 2):
            pts = [points[j] for j in range(i, i + 4)]
            yield (
                SameOrOppositeSideProperty(pts[0].segment(pts[2]), pts[1], pts[3], False),
                comment,
                [prop]
            )

class SquareRule(SingleSourceRule):
    property_type = (SquareProperty, NondegenerateSquareProperty)

    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def accepts(self, prop):
        return prop not in self.processed

    def apply(self, prop):
        self.processed.add(prop)

        sq = prop.square
        params = {'square': sq}
        diagonals = [sq.points[0].segment(sq.points[2]), sq.points[1].segment(sq.points[3])]
        for side0, side1 in itertools.combinations(sq.sides, 2):
            yield (
                ProportionalLengthsProperty(side0, side1, 1),
                Comment('sides of square $%{polygon:square}$', params),
                [prop]
            )
        yield (
            ProportionalLengthsProperty(diagonals[0], diagonals[1], 1),
            Comment('diagonals of square $%{polygon:square}$', params),
            [prop]
        )
        for side, diagonal in itertools.product(sq.sides, diagonals):
            yield (
                ProportionalLengthsProperty(diagonal, side, sp.sqrt(2)),
                Comment('diagonal and side of square $%{polygon:square}$', params),
                [prop]
            )

        pts = sq.points * 2
        pattern = 'sides $%{segment:side0}$ and $%{segment:side1}$ of square $%{polygon:square}$'
        for i in range(0, 2):
            side0 = pts[i].vector(pts[i + 1])
            side1 = pts[i + 3].vector(pts[i + 2])
            yield (
                ParallelVectorsProperty(side0, side1),
                Comment(pattern, {'side0': side0, 'side1': side1, 'square': sq}),
                [prop]
            )
        for i in range(0, 4):
            side0 = pts[i + 1].segment(pts[i])
            side1 = pts[i + 1].segment(pts[i + 2])
            yield (
                PerpendicularSegmentsProperty(side0, side1),
                Comment(pattern, {'side0': side0, 'side1': side1, 'square': sq}),
                [prop]
            )

class SquareDegeneracyRule(SingleSourceRule):
    property_type = SquareProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = {}

    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0xF:
            return
        original = mask

        sq = prop.square
        params = {'square': sq}

        for index, side in enumerate(sq.sides):
            bit = 1 << index
            if mask & bit:
                continue
            ne = self.context.coincidence_property(*side.points)
            if ne is None:
                continue
            mask |= bit

            if ne.coincident:
                pattern = 'square $%{polygon:square}$ has zero-length side $%{segment:side}$'
            else:
                pattern = 'square $%{polygon:square}$ has nonzero-length side $%{segment:side}$'
            comment = Comment(pattern, {'square': sq, 'side': side})
            if ne.coincident:
                for other in [s for s in sq.sides if s != side]:
                    yield (
                        PointsCoincidenceProperty(*other.points, ne.coincident),
                        comment,
                        [prop, ne]
                    )
            else:
                yield (
                    NondegenerateSquareProperty(prop.square),
                    comment,
                    [prop, ne]
                )

        if mask != original:
            self.processed[prop] = mask

class NondegenerateSquareRule(SingleSourceRule):
    property_type = NondegenerateSquareProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def accepts(self, prop):
        return prop not in self.processed

    def apply(self, prop):
        self.processed.add(prop)

        sq = prop.square
        pts = sq.points * 2
        params = {'square': sq}
        diagonals = [pts[0].segment(pts[2]), pts[1].segment(pts[3])]

        comment = Comment('vertices of non-degenerate square $%{polygon:square}$', params)
        for pt0, pt1, pt2 in itertools.combinations(sq.points, 3):
            yield (PointsCollinearityProperty(pt0, pt1, pt2, False), comment, [prop])
        for side in sq.sides:
            yield (PointsCoincidenceProperty(*side.points, False), comment, [prop])
        comment = Comment('diagonals of non-degenerate square $%{polygon:square}$', params)
        for diagonal in diagonals:
            yield (PointsCoincidenceProperty(*diagonal.points, False), comment, [prop])
        comment = Comment('angle of non-degenerate square $%{polygon:square}$', params)
        for angle in sq.angles:
            yield (AngleValueProperty(angle, 90), comment, [prop])
        
        pattern = 'parallel sides $%{segment:side0}$ and $%{segment:side1}$ of non-degenerate square $%{polygon:square}$'
        for i in range(0, 2):
            side0 = pts[i].vector(pts[i + 1])
            side1 = pts[i + 3].vector(pts[i + 2])
            yield (
                AngleValueProperty(side0.angle(side1), 0),
                Comment(pattern, {'side0': side0, 'side1': side1, 'square': sq}),
                [prop]
            )
            yield (
                AngleValueProperty(side0.angle(side1.reversed), 180),
                Comment(pattern, {'side0': side0, 'side1': side1.reversed, 'square': sq}),
                [prop]
            )

        pattern = 'angle between side $%{segment:side}$ and diagonal $%{segment:diagonal}$ of non-degenerate square $%{polygon:square}$'
        for i in range(0, 4):
            diagonal = pts[i + 1].vector(pts[i + 3])
            for pt in (pts[i], pts[i + 2]):
                side = pts[i + 1].vector(pt)
                yield (
                    AngleValueProperty(side.angle(diagonal), 45),
                    Comment(pattern, {'side': side, 'diagonal': diagonal, 'square': sq}),
                    [prop]
                )
