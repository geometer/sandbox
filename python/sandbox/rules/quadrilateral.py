import itertools
import sympy as sp

from ..property import *
from ..util import Comment

from .abstract import Rule, Rule, accepts_auto, processed_cache, source_type, source_types

@source_types(SquareProperty, NondegenerateSquareProperty)
@processed_cache(set())
class PointInsideHalfOfSquareRule(Rule):
    def apply(self, prop):
        for triple in itertools.combinations(prop.square.points, 3):
            triangle = Scene.Triangle(*triple)
            for pt in self.context.points_inside_triangle(triangle):
                key = (pt, frozenset(triple))
                if key in self.processed:
                    continue
                self.processed.add(key)
                triangle_prop = self.context[PointInsideTriangleProperty(pt, triangle)]
                yield (
                    PointInsideSquareProperty(pt, prop.square),
                    Comment(
                        '$%{point:pt}$ lies inside $%{triangle:triangle}$ that is part of $%{polygon:square}$',
                        {'pt': pt, 'triangle': triangle, 'square': prop.square}
                    ),
                    [prop, triangle_prop]
                )

@source_type(PointInsideSquareProperty)
@processed_cache(set())
@accepts_auto
class PointInsideSquareRule(Rule):
    def apply(self, prop):
        self.processed.add(prop.property_key)

        comment = Comment(
            '$%{point:pt}$ lies inside square $%{polygon:square}$',
            {'pt': prop.point, 'square': prop.square}
        )
        new_properties = []
        verts = prop.square.points
        for angle in prop.square.angles:
            new_properties.append(PointInsideAngleProperty(prop.point, angle))

        verts2 = verts * 2
        for i in range(0, 4):
            side = verts2[i].segment(verts2[i + 1])
            new_properties.append(LineAndTwoPointsProperty(side, prop.point, verts2[i + 2], True))
            new_properties.append(LineAndTwoPointsProperty(side, prop.point, verts2[i + 3], True))

        cycles = [prop.point.cycle(verts2[i], verts2[i + 1]) for i in range(0, 4)]
        for c0, c1 in itertools.combinations(cycles, 2):
            new_properties.append(SameCyclicOrderProperty(c0, c1))
            new_properties.append(SameCyclicOrderProperty(c0.reversed, c1.reversed))

        for p in new_properties:
            yield (p, comment, [prop])

@source_type(ConvexQuadrilateralProperty)
@processed_cache(set())
@accepts_auto
class IntersectionOfDiagonalsOfConvexQuadrilateralRule(Rule):
    def apply(self, prop):
        quad = prop.quadrilateral
        diagonals = (
            quad.points[0].segment(quad.points[2]),
            quad.points[1].segment(quad.points[3])
        )
        crossing = self.context.intersection(*diagonals)
        if crossing is None:
            return
        self.processed.add(prop.property_key)
        crossing_prop = self.context.intersection_property(crossing, *diagonals)
        comment = Comment(
            '$%{point:crossing}$ in the intersection of diagonals $%{segment:d0}$ and $%{segment:d1}$ of convex $%{polygon:quad}$',
            {'crossing': crossing, 'd0': diagonals[0], 'd1': diagonals[1], 'quad': quad}
        )
        for d in diagonals:
            yield (AngleValueProperty(crossing.angle(*d.points), 180), comment, [crossing_prop, prop])

@source_types(ConvexQuadrilateralProperty, NondegenerateSquareProperty)
@processed_cache(set())
class PointOnSideOfConvexQuadrialteralRule(Rule):
    def apply(self, prop):
        if isinstance(prop, NondegenerateSquareProperty):
            quad = prop.square
            pattern = '$%{point:pt}$ lies on side $%{segment:side}$ of non-degenerate square $%{polygon:quad}$'
        else:
            quad = prop.quadrilateral
            pattern = '$%{point:pt}$ lies on side $%{segment:side}$ of convex $%{polygon:quad}$'
        for side in quad.sides:
            for pt in self.context.points_inside_segment(side):
                key = (prop.property_key, pt)
                if key in self.processed:
                    continue
                self.processed.add(key)
                comment = Comment(pattern, {'pt': pt, 'quad': quad, 'side': side})
                premises = [self.context.angle_value_property(pt.angle(*side.points)), prop]
                for repl in side.points:
                    pts = [pt if p == repl else p for p in quad.points]
                    yield (ConvexQuadrilateralProperty(Scene.Polygon(*pts)), comment, premises)
                for angle in [a for a in quad.angles if a.vertex not in side.points]:
                    yield (PointInsideAngleProperty(pt, angle), comment, premises)
                for v0, v1 in itertools.combinations(quad.points, 2):
                    if v0 in side.points and v1 in side.points:
                        continue
                    yield (PointsCollinearityProperty(pt, v0, v1, False), comment, premises)

@source_type(LineAndTwoPointsProperty)
@processed_cache(set())
class KnownAnglesToConvexQuadrilateralRule(Rule):
    def accepts(self, prop):
        return prop.same_side

    def apply(self, prop):
        pt0, pt1 = prop.points
        pt_set = frozenset(prop.points)
        for segment in self.context.line_for_key(prop.line_key).segments:
            ltp_prop = prop if segment == prop.line_key else None
            for sp0, sp1 in (segment.points, reversed(segment.points)):
                key = (pt_set, sp0, sp1)
                if key in self.processed:
                    continue

                av0 = self.context.angle_value_property(sp0.angle(sp1, pt0))
                if av0 is None:
                    continue
                av1 = self.context.angle_value_property(sp1.angle(sp0, pt1))
                if av1 is None:
                    continue
                self.processed.add(key)

                if ltp_prop is None:
                    ltp_prop = self.context.line_and_two_points_property(segment, pt0, pt1)

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
                    'line': segment
                }
                if sum_degree == 180:
                    pattern = '$%{anglemeasure:angle0} + %{anglemeasure:angle1} = %{degree:sum}$, and points $%{point:pt0}$ and $%{point:pt1}$ are on the same side of $%{line:line}$'
                else:
                    pattern = '$%{anglemeasure:angle0} + %{anglemeasure:angle1} = %{degree:sum} > %{degree:180}$, and points $%{point:pt0}$ and $%{point:pt1}$ are on the same side of $%{line:line}$'
                yield (
                    ConvexQuadrilateralProperty(Scene.Polygon(pt0, sp0, sp1, pt1)),
                    Comment(pattern, params),
                    [av0, av1, ltp_prop]
                )

@source_type(LineAndTwoPointsProperty)
@processed_cache(set())
class PointsToConvexQuadrilateralRule(Rule):
    def accepts(self, prop):
        return not prop.same_side

    def apply(self, prop):
        alt_segment = prop.points[0].segment(prop.points[1])
        for segment in self.context.line_for_key(prop.line_key).segments:
            key = frozenset((segment, alt_segment))
            if key in self.processed:
                continue
            ltp = self.context.line_and_two_points(alt_segment, *segment.points)
            if ltp is None:
                continue
            self.processed.add(key)
            if ltp:
                continue
            prop0 = prop if segment == prop.line_key else self.context.line_and_two_points_property(segment, *prop.points)
            prop1 = self.context.line_and_two_points_property(alt_segment, *segment.points)

            quad = Scene.Polygon(segment.points[0], prop.points[0], segment.points[1], prop.points[1])
            yield (
                ConvexQuadrilateralProperty(quad),
                Comment(
                    'both diagonals $%{segment:d0}$ and $%{segment:d1}$ divide quadrilateral $%{polygon:quad}$',
                    {'d0': segment, 'd1': alt_segment, 'quad': quad}
                ),
                [prop0, prop1]
            )

@source_type(ConvexQuadrilateralProperty)
@processed_cache(set())
@accepts_auto
class SumOfAnglesOfConvexQuadrilateralRule(Rule):
    def apply(self, prop):
        self.processed.add(prop.property_key)

        yield (
            SumOfAnglesProperty(*prop.quadrilateral.angles, degree=360),
            Comment('sum of angles of convex $%{polygon:quad}$', {'quad': prop.quadrilateral}),
            [prop]
        )

@source_types(ConvexQuadrilateralProperty, NondegenerateSquareProperty)
@processed_cache(set())
@accepts_auto
class ConvexQuadrilateralRule(Rule):
    def apply(self, prop):
        self.processed.add(prop.property_key)

        if isinstance(prop, NondegenerateSquareProperty):
            quad = prop.square
            pattern = '$%{polygon:quad}$ is a non-degenerate square'
        else:
            quad = prop.quadrilateral
            pattern = '$%{polygon:quad}$ is a convex quadrilateral'

        new_properties = []
        for pt0, pt1 in itertools.combinations(quad.points, 2):
            new_properties.append(PointsCoincidenceProperty(pt0, pt1, False))

        points = quad.points * 2
        for i in range(0, 4):
            pts = [points[j] for j in range(i, i + 4)]
            new_properties.append(
                PointsCollinearityProperty(*pts[:3], False)
            )
            new_properties.append(
                LineAndTwoPointsProperty(pts[0].segment(pts[1]), pts[2], pts[3], True)
            )
            new_properties.append(
                PointInsideAngleProperty(pts[0], pts[2].angle(pts[1], pts[3]))
            )
        for i in range(0, 2):
            pts = [points[j] for j in range(i, i + 4)]
            new_properties.append(
                LineAndTwoPointsProperty(pts[0].segment(pts[2]), pts[1], pts[3], False)
            )

        comment = Comment(pattern, {'quad': quad})
        for p in new_properties:
            yield (p, comment, [prop])

@source_types(SquareProperty, NondegenerateSquareProperty)
@processed_cache(set())
@accepts_auto
class SquareRule(Rule):
    def apply(self, prop):
        self.processed.add(prop.property_key)

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

@source_type(SquareProperty)
@processed_cache({})
class SquareDegeneracyRule(Rule):
    def apply(self, prop):
        mask = self.processed.get(prop.property_key, 0)
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
            self.processed[prop.property_key] = mask

@source_type(NondegenerateSquareProperty)
@processed_cache(set())
@accepts_auto
class NondegenerateSquareRule(Rule):
    def apply(self, prop):
        self.processed.add(prop.property_key)

        sq = prop.square
        pts = sq.points * 2
        params = {'square': sq}

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
