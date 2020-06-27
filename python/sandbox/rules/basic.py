import itertools

from ..property import *
from ..scene import Scene
from ..util import LazyComment, Comment, divide, common_endpoint, other_point

from .abstract import Rule, SingleSourceRule

class PointInsideAngleAndPointOnSideRule(SingleSourceRule):
    property_type = PointInsideAngleProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def apply(self, prop):
        for vec in prop.angle.vectors:
            for pt in self.context.collinear_points(vec.as_segment):
                key = (prop, pt)
                if key in self.processed:
                    continue
                self.processed.add(key)
                yield (
                    PointsCoincidenceProperty(prop.point, pt, False),
                    Comment(
                        '$%{point:inside}$ lies inside $%{angle:angle}$, $%{point:pt}$ is on $%{line:side}$',
                        {'inside': prop.point, 'angle': prop.angle, 'pt': pt, 'side': vec}
                    ),
                    [prop, self.context.collinearity_property(*vec.points, pt)]
                )

class AngleTypeAndPerpendicularRule(SingleSourceRule):
    property_type = AngleKindProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def accepts(self, prop):
        return prop.angle.vertex and prop.kind != AngleKindProperty.Kind.right

    def apply(self, prop):
        angle = prop.angle
        if prop.kind == AngleKindProperty.Kind.acute:
            pattern = '$%{point:foot}$ is the foot of perpendicular from point $%{point:pt}$ on side of acute $%{angle:angle}$ to another side'
        else:
            pattern = '$%{point:foot}$ is the foot of perpendicular from point $%{point:pt}$ on side of obtuse $%{angle:angle}$ to extension of another side'
        for vec0, vec1 in (angle.vectors, reversed(angle.vectors)):
            key = (prop, vec0.end)
            if key in self.processed:
                continue
            foot, premises = self.context.foot_of_perpendicular(vec0.end, vec1.as_segment)
            if foot is None:
                continue
            self.processed.add(key)
            comment = Comment(pattern, {'foot': foot, 'pt': vec0.end, 'angle': angle})
            new_props = [
                PointsCollinearityProperty(vec0.end, foot, angle.vertex, False),
                PointsCoincidenceProperty(foot, angle.vertex, False),
            ]
            if foot != vec1.end:
                if prop.kind == AngleKindProperty.Kind.acute:
                    new_props.append(AngleValueProperty(angle.vertex.angle(foot, vec1.end), 0))
                else:
                    new_props.append(AngleValueProperty(angle.vertex.angle(foot, vec1.end), 180))
            for p in new_props:
                yield (p, comment, [prop] + premises)

class PointInsideAngleConfigurationRule(SingleSourceRule):
    property_type = PointInsideAngleProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def accepts(self, prop):
        return prop not in self.processed

    def apply(self, prop):
        self.processed.add(prop)

        for endpoint in prop.angle.endpoints:
            yield (
                PointsCollinearityProperty(prop.point, prop.angle.vertex, endpoint, False),
                Comment(
                    '$%{point:vertex}$ is the vertex of $%{angle:angle}$, $%{point:on_side}$ lies on a side, and $%{point:inside}$ lies inside',
                    {'vertex': prop.angle.vertex, 'angle': prop.angle, 'on_side': endpoint, 'inside': prop.point}
                ),
                [prop]
            )

        yield (
            SameOrOppositeSideProperty(prop.angle.vertex.segment(prop.point), *prop.angle.endpoints, False),
            Comment(
                'ray $%{ray:ray}$ inside $%{angle:angle}$ separates points $%{point:pt0}$ and $%{point:pt1}$ lying on different sides of the angle',
                {'ray': prop.angle.vertex.vector(prop.point), 'angle': prop.angle, 'pt0': prop.angle.endpoints[0], 'pt1': prop.angle.endpoints[1]}
            ),
            [prop]
        )
        pattern = '$%{ray:side}$ is a side of $%{angle:angle}$, $%{point:other}$ lies on the other side, and $%{point:inside}$ lies inside the angle'
        yield (
            SameOrOppositeSideProperty(prop.angle.vectors[0].as_segment, prop.point, prop.angle.vectors[1].end, True),
            Comment(
                pattern,
                {'side': prop.angle.vectors[0], 'angle': prop.angle, 'other': prop.angle.vectors[1].end, 'inside': prop.point}
            ),
            [prop]
        )
        yield (
            SameOrOppositeSideProperty(prop.angle.vectors[1].as_segment, prop.point, prop.angle.vectors[0].end, True),
            Comment(
                pattern,
                {'side': prop.angle.vectors[1], 'angle': prop.angle, 'other': prop.angle.vectors[0].end, 'inside': prop.point}
            ),
            [prop]
        )

class SegmentWithEndpointsOnAngleSidesRule(SingleSourceRule):
    property_type = PointInsideAngleProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def accepts(self, prop):
        return prop not in self.processed

    def apply(self, prop):
        A = prop.angle.vertex
        B = prop.angle.vectors[0].end
        C = prop.angle.vectors[1].end
        D = prop.point
        AD = A.segment(D)
        BC = B.segment(C)
        X, reasons = self.context.intersection_of_lines(AD, BC)
        if X is None:
            return
        self.processed.add(prop)
        if X in (A, B, C, D):
            return

        comment = Comment(
            '$%{point:X}$ is the intersection of ray $%{ray:ray}$ and segment $%{segment:segment}$',
            {'X': X, 'ray': A.vector(D), 'segment': B.segment(C)}
        )
        yield (AngleValueProperty(A.angle(D, X), 0), comment, [prop] + reasons)
        yield (AngleValueProperty(B.angle(C, X), 0), comment, [prop] + reasons)
        yield (AngleValueProperty(C.angle(B, X), 0), comment, [prop] + reasons)
        yield (AngleValueProperty(X.angle(B, C), 180), comment, [prop] + reasons)

class SumOfAngles180DegreeRule(Rule):
    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def sources(self):
        return [p for p in self.context.list(SumOfTwoAnglesProperty) if p.angles[0].vertex is not None and p.angles[0].vertex == p.angles[1].vertex and p.degree == 180 and p not in self.processed]

    def apply(self, prop):
        common = next((pt for pt in prop.angles[0].endpoints if pt in prop.angles[1].endpoints), None)
        if common is None:
            self.processed.add(prop)
            return
        pt0 = next(pt for pt in prop.angles[0].endpoints if pt != common)
        pt1 = next(pt for pt in prop.angles[1].endpoints if pt != common)
        oppo = self.context.two_points_relative_to_line_property(prop.angles[0].vertex.segment(common), pt0, pt1)
        if oppo is None:
            return
        self.processed.add(prop)
        if oppo.same:
            return
        yield (
            AngleValueProperty(prop.angles[0].vertex.angle(pt0, pt1), 180),
            LazyComment('%s + %s', prop.angles[0], prop.angles[1]),
            [prop, oppo]
        )

class ProportionalLengthsToLengthsRatioRule(SingleSourceRule):
    property_type = ProportionalLengthsProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = {}

    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0x3:
            return

        original = mask
        for segment, bit in ((prop.segment0, 1), (prop.segment1, 2)):
            if mask & bit:
                continue
            ne = self.context.coincidence_property(*segment.points)
            if ne is None:
                continue
            mask |= bit
            if ne.coincident:
                continue
            yield (
                LengthRatioProperty(prop.segment0, prop.segment1, prop.value),
                prop.reason.comment,
                [prop, ne]
            )

        if mask != original:
            self.processed[prop] = mask

class LengthRatiosWithCommonDenominatorRule(Rule):
    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def sources(self):
        return self.context.equal_length_ratios_with_common_denominator()

    def apply(self, src):
        key = frozenset(src)
        if key in self.processed:
            return
        self.processed.add(key)

        ratio0, ratio1 = src
        ratio_prop = self.context.equal_length_ratios_property(*ratio0, *ratio1)
        yield (
            ProportionalLengthsProperty(ratio0[0], ratio1[0], 1),
            ratio_prop.reason.comment,
            ratio_prop.reason.premises
        )

class LengthRatioTransitivityRule(Rule):
    """
    For three segments seg0, seg1, and seg2, from
        |seg0| = A |seg1|, and
        |seg1| = B |seg2|
    we conclude that |seg0| = A B |seg2|
    """
    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def sources(self):
        return itertools.combinations(self.context.length_ratio_properties(allow_zeroes=True), 2)

    def apply(self, src):
        key = frozenset(src)
        if key in self.processed:
            return
        self.processed.add(key)

        lr0, lr1 = src

        def _cs(coef):
            return '' if coef == 1 else ('%s ' % coef)

        def comment(seg0, seg1, seg2, coef1, coef2):
            if coef1 == 1:
                if coef2 == 1:
                    pattern = '$|%{segment:seg0}| = |%{segment:seg1}| = |%{segment:seg2}|$'
                else:
                    pattern = '$|%{segment:seg0}| = |%{segment:seg1}| = %{multiplier:coef2}|%{segment:seg2}|$'
            else:
                if coef2 == 1:
                    pattern = '$|%{segment:seg0}| = %{multiplier:coef1}|%{segment:seg1}| = |%{segment:seg2}|$'
                else:
                    pattern = '$|%{segment:seg0}| = %{multiplier:coef1}|%{segment:seg1}| = %{multiplier:coef2}|%{segment:seg2}|$'
            return Comment(pattern, {'seg0': seg0, 'seg1': seg1, 'seg2': seg2, 'coef1': coef1, 'coef2': coef2})

        if lr0.segment0 == lr1.segment0:
            coef = divide(lr1.value, lr0.value)
            yield (
                ProportionalLengthsProperty(lr0.segment1, lr1.segment1, coef),
                comment(lr0.segment1, lr0.segment0, lr1.segment1, divide(1, lr0.value), coef),
                [lr0, lr1]
            )
        elif lr0.segment0 == lr1.segment1:
            coef = lr1.value * lr0.value
            yield (
                ProportionalLengthsProperty(lr1.segment0, lr0.segment1, coef),
                comment(lr1.segment0, lr0.segment0, lr0.segment1, lr1.value, coef),
                [lr1, lr0]
            )
        elif lr0.segment1 == lr1.segment0:
            coef = lr1.value * lr0.value
            yield (
                ProportionalLengthsProperty(lr0.segment0, lr1.segment1, coef),
                comment(lr0.segment0, lr0.segment1, lr1.segment1, lr0.value, coef),
                [lr0, lr1]
            )
        elif lr0.segment1 == lr1.segment1:
            coef = divide(lr0.value, lr1.value)
            yield (
                ProportionalLengthsProperty(lr0.segment0, lr1.segment0, coef),
                comment(lr0.segment0, lr0.segment1, lr1.segment0, lr0.value, coef),
                [lr0, lr1]
            )

class CoincidenceTransitivityRule(Rule):
    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def sources(self):
        #TODO: use self.context.non_coincident_points()
        return itertools.combinations(self.context.list(PointsCoincidenceProperty), 2)

    def apply(self, src):
        key = frozenset(src)
        if key in self.processed:
            return
        self.processed.add(key)

        co0, co1 = src
        if not co0.coincident and not co1.coincident:
            return
        common = next((pt for pt in co0.points if pt in co1.points), None)
        if common is None:
            return
        pt0 = next(pt for pt in co0.points if pt != common)
        pt1 = next(pt for pt in co1.points if pt != common)
        yield (
            PointsCoincidenceProperty(pt0, pt1, co0.coincident and co1.coincident),
            LazyComment('%s %s %s %s %s', pt0, '=' if co0.coincident else '!=', common, '=' if co1.coincident else '!=', pt1),
            [co0, co1]
        )

class TwoPointsBelongsToTwoLinesRule(SingleSourceRule):
    """
    If two points both belong to two different lines,
    the points are coincident
    """
    property_type = PointsCollinearityProperty

    def accepts(self, prop):
        return prop.collinear

    def apply(self, cl0):
        triangle = Scene.Triangle(*cl0.points)
        sides = triangle.sides
        for side, pt0 in [(sides[i], triangle.points[i]) for i in range(0, 3)]:
            third_points = [pt0]
            for pt1 in self.context.collinear_points(side):
                if pt1 == pt0:
                    continue
                third_points.append(pt1)

                for ncl_pt in side.points:
                    ncl = self.context.collinearity_property(pt0, pt1, ncl_pt)
                    if ncl:
                        break
                else:
                    continue
                if ncl.collinear:
                    continue
                cl1 = self.context.collinearity_property(*side.points, pt1)
                if cl0.reason.obsolete and cl1.reason.obsolete and ncl.reason.obsolete:
                    continue
                yield (
                    PointsCoincidenceProperty(*side.points, True),
                    Comment(
                        '$%{point:pt0}$ and $%{point:pt1}$ belong to two different lines $%{line:line0}$ and $%{line:line1}$',
                        {'pt0': side.points[0], 'pt1': side.points[1], 'line0': pt0.segment(ncl_pt), 'line1': pt1.segment(ncl_pt)}
                    ),
                    [cl0, cl1, ncl]
                )
                break
            else:
                for triple in itertools.combinations(third_points, 3):
                    ncl = self.context.collinearity_property(*triple)
                    if ncl and not ncl.collinear:
                        cls = [self.context.collinearity_property(*side.points, pt) for pt in triple]
                        lines = [pt.segment(side.points[0]) for pt in triple]
                        yield (
                            PointsCoincidenceProperty(*side.points, True),
                            LazyComment('%s and %s belong to three lines %s, %s, and %s, at least two of them are different', *side.points, *lines),
                            cls + [ncl]
                        )
                        break

class AngleInTriangleWithTwoKnownAnglesRule(Rule):
    def __init__(self, context):
        super().__init__(context)
        self.processed = {}

    def sources(self):
        return [p for p in self.context.angle_value_properties() if p.angle.vertex and p.degree not in (0, 180)];

    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0x3:
            return

        angle0 = prop.angle
        triangle = Scene.Triangle(angle0.vertex, *angle0.endpoints)
        others = triangle.angles[1:]
        original = mask
        for (angle1, angle2), bit in ((others, 1), (reversed(others), 2)):
            if mask & bit:
                continue
            av = self.context.angle_value_property(angle1)
            if av is None:
                continue
            mask |= bit
            yield (
                AngleValueProperty(angle2, 180 - prop.degree - av.degree),
                Comment(
                    'third angle in $%{triangle:triangle}$ with $%{anglemeasure:angle0} = %{degree:degree0}$ and $%{anglemeasure:angle1} = %{degree:degree1}$',
                    {
                        'triangle': triangle,
                        'angle0': angle0,
                        'angle1': angle1,
                        'degree0': prop.degree,
                        'degree1': av.degree
                    }
                ),
                [prop, av]
            )
        if mask != original:
            self.processed[prop] = mask

class SumOfTwoAnglesInTriangleRule(Rule):
    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def sources(self):
        return [p for p in self.context.angle_value_properties() if p.angle.vertex and p.degree not in (0, 180)];

    def apply(self, prop):
        if prop in self.processed:
            return
        self.processed.add(prop)

        angle0 = prop.angle
        triangle = Scene.Triangle(angle0.vertex, *angle0.endpoints)
        angle1 = triangle.angles[1]
        angle2 = triangle.angles[2]

        if prop.degree == 90:
            pattern = 'sum of acute angles of right-angled $%{triangle:triangle}$'
        else:
            pattern = 'sum of two angles of $%{triangle:triangle}$, the third $%{anglemeasure:angle} = %{degree:degree}$'
        yield (
            SumOfTwoAnglesProperty(angle1, angle2, 180 - prop.degree),
            Comment(pattern, {'triangle': triangle, 'angle': angle0, 'degree': prop.degree}),
            [prop]
        )

class SumOfThreeAnglesInTriangleRule(Rule):
    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def sources(self):
        for pt in self.context.points:
            for pair in itertools.combinations(self.context.non_coincident_points(pt), 2):
                yield (pt, *pair)

    def apply(self, src):
        key = frozenset(src)
        if key in self.processed:
            return

        pt0, pt1, pt2 = src
        ne2 = self.context.coincidence_property(pt1, pt2)
        if ne2 is None:
            return
        self.processed.add(key)
        if ne2.coincident:
            return
        ne0 = self.context.coincidence_property(pt0, pt1)
        ne1 = self.context.coincidence_property(pt0, pt2)
        triangle = Scene.Triangle(pt0, pt1, pt2)
        yield (
            SumOfThreeAnglesProperty(*triangle.angles, 180),
            Comment('three angles of $%{triangle:triangle}$', {'triangle': triangle}),
            [ne0, ne1, ne2]
        )

class SumOfThreeAnglesOnLineRule(Rule):
    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def sources(self):
        avs = self.context.angle_value_properties_for_degree(0, lambda angle: angle.vertex)
        for av0, av1 in itertools.combinations(avs, 2):
            if av0.angle.point_set == av1.angle.point_set:
                yield (av0, av1)

    def apply(self, src):
        key = frozenset(src)
        if key in self.processed:
            return
        self.processed.add(key)

        av0, av1 = src
        third = next(pt for pt in av0.angle.point_set if pt not in (av0.angle.vertex, av1.angle.vertex))
        angle = third.angle(av0.angle.vertex, av1.angle.vertex)
        yield (
            AngleValueProperty(angle, 180),
            Comment(
                '$%{point:pt0}$ and $%{point:pt1}$ are on the same side of $%{point:pt2}$, $%{point:pt2}$ and $%{point:pt1}$ are on the same side of $%{point:pt0}$',
                {'pt1': third, 'pt0': av0.angle.vertex, 'pt2': av1.angle.vertex}
            ),
            [av0, av1]
        )

class SumOfThreeAnglesOnLineRule2(Rule):
    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def sources(self):
        return self.context.angle_value_properties_for_degree(
            180, lambda angle: angle.vertex and angle not in self.processed
        )

    def apply(self, prop):
        self.processed.add(prop.angle)

        for vec0, vec1 in (prop.angle.vectors, reversed(prop.angle.vectors)):
            yield (
                AngleValueProperty(vec0.end.angle(vec0.start, vec1.end), 0),
                Comment(
                    '$%{point:pt0}$ lies between $%{point:pt1}$ and $%{point:pt2}$',
                    {'pt0': vec0.start, 'pt1': vec0.end, 'pt2': vec1.end}
                ),
                [prop]
            )

class LengthRatioRule(SingleSourceRule):
    property_type = ProportionalLengthsProperty

    def apply(self, prop):
        seg0 = prop.segment0
        seg1 = prop.segment1

        ne0 = self.context.not_equal_property(*seg0.points)
        ne1 = self.context.not_equal_property(*seg1.points)
        pattern = 'otherwise, $%{point:pt0} = %{point:pt1}$'
        if ne0 is not None and ne1 is None:
            if prop.reason.obsolete and ne0.reason.obsolete:
                return
            yield (
                PointsCoincidenceProperty(*seg1.points, False),
                Comment(pattern, {'pt0': seg0.points[0], 'pt1': seg0.points[1]}),
                [prop, ne0]
            )
        elif ne1 is not None and ne0 is None:
            if prop.reason.obsolete and ne1.reason.obsolete:
                return
            yield (
                PointsCoincidenceProperty(*seg0.points, False),
                Comment(pattern, {'pt0': seg1.points[0], 'pt1': seg1.points[1]}),
                [prop, ne1]
            )
        elif ne0 is None and ne1 is None:
            common = next((pt for pt in seg0.points if pt in seg1.points), None)
            if common is None:
                return
            pt0 = next(pt for pt in seg0.points if pt != common)
            pt1 = next(pt for pt in seg1.points if pt != common)
            ne = self.context.not_equal_property(pt0, pt1)
            if ne is None or prop.reason.obsolete and ne.reason.obsolete:
                return
            pattern = 'otherwise, $%{point:pt0} = %{point:pt1} = %{point:pt2}$'
            yield (
                PointsCoincidenceProperty(*seg0.points, False),
                Comment(pattern, {'pt0': ne.points[0], 'pt1': common, 'pt2': ne.points[1]}),
                [prop, ne]
            )
            yield (
                PointsCoincidenceProperty(*seg1.points, False),
                Comment(pattern, {'pt0': ne.points[1], 'pt1': common, 'pt2': ne.points[0]}),
                [prop, ne]
            )

class ParallelVectorsRule(SingleSourceRule):
    property_type = ParallelVectorsProperty

    def apply(self, para):
        vec0 = para.vectors[0]
        vec1 = para.vectors[1]
        ne0 = self.context.not_equal_property(*vec0.points)
        ne1 = self.context.not_equal_property(*vec1.points)
        if ne0 is None or ne1 is None:
            return
        if para.reason.obsolete and ne0.reason.obsolete and ne1.reason.obsolete:
            return
        for prop in AngleValueProperty.generate(vec0, vec1, 0):
            yield (
                prop,
                Comment(
                    'non-zero parallel vectors $%{vector:vec0}$ and $%{vector:vec1}$',
                    {'vec0': vec0, 'vec1': vec1}
                ),
                [para, ne0, ne1]
            )

class PerpendicularSegmentsRule(SingleSourceRule):
    property_type = PerpendicularSegmentsProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def accepts(self, prop):
        return prop not in self.processed

    def apply(self, pv):
        seg0 = pv.segments[0]
        seg1 = pv.segments[1]
        ne0 = self.context.coincidence_property(*seg0.points)
        ne1 = self.context.coincidence_property(*seg1.points)
        if ne0 is None or ne1 is None:
            return
        self.processed.add(pv)
        if ne0.coincident or ne1.coincident:
            return
        vec0 = seg0.points[0].vector(seg0.points[1])
        vec1 = seg1.points[0].vector(seg1.points[1])
        for prop in AngleValueProperty.generate(vec0, vec1, 90):
            yield (
                prop,
                Comment(
                    'non-zero perpendicular segments $%{segment:seg0}$ and $%{segment:seg1}$',
                    {'seg0': seg0, 'seg1': seg1}
                ),
                [pv, ne0, ne1]
            )

class Degree90ToPerpendicularSegmentsRule(Rule):
    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def sources(self):
        return self.context.angle_value_properties_for_degree(
            90, lambda angle: angle not in self.processed
        )

    def apply(self, prop):
        self.processed.add(prop.angle)

        yield (
            PerpendicularSegmentsProperty(prop.angle.vectors[0].as_segment, prop.angle.vectors[1].as_segment),
            prop.reason.comment,
            prop.reason.premises
        )

class Degree90ToPerpendicularSegmentsRule2(Rule):
    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def sources(self):
        return self.context.angle_value_properties_for_degree(90)

    def apply(self, prop):
        seg0 = prop.angle.vectors[0].as_segment
        seg1 = prop.angle.vectors[1].as_segment
        for pt in self.context.collinear_points(seg0):
            key = (prop, 0, pt)
            if key in self.processed:
                continue
            self.processed.add(key)

            for pt1 in seg0.points:
                yield (
                    PerpendicularSegmentsProperty(pt.segment(pt1), seg1),
                    Comment(
                        '$%{segment:seg0} \\perp %{segment:seg1}$, $%{point:pt}$ lies on $%{line:seg0}$',
                        {'seg0': seg0, 'seg1': seg1, 'pt': pt}
                    ),
                    [prop, self.context.point_on_line_property(seg0, pt)]
                )
        for pt in self.context.collinear_points(seg1):
            key = (prop, 1, pt)
            if key in self.processed:
                continue
            self.processed.add(key)

            for pt1 in seg1.points:
                yield (
                    PerpendicularSegmentsProperty(pt.segment(pt1), seg0),
                    Comment(
                        '$%{segment:seg1} \\perp %{segment:seg0}$, $%{point:pt}$ lies on $%{line:seg1}$',
                        {'seg0': seg0, 'seg1': seg1, 'pt': pt}
                    ),
                    [prop, self.context.point_on_line_property(seg1, pt)]
                )

class CommonPerpendicularRule(SingleSourceRule):
    property_type = AngleValueProperty

    def accepts(self, prop):
        return prop.degree == 0

    def apply(self, prop):
        segments = (prop.angle.vectors[0].as_segment, prop.angle.vectors[1].as_segment)
        for seg0, seg1 in (segments, reversed(segments)):
            for perp in self.context.list(PerpendicularSegmentsProperty, [seg0]):
                if prop.reason.obsolete and perp.reason.obsolete:
                    continue
                other = perp.segments[1] if seg0 == perp.segments[0] else perp.segments[0]
                if prop.angle.vertex:
                    pattern = '$%{line:line0}$ is the same line as $%{line:line1}$'
                else:
                    pattern = 'any line perpendicular to $%{line:line0}$ is also perpendicular to $%{line:line1}$'
                comment = Comment(pattern, {'line0': seg0, 'line1': seg1})
                yield (
                    PerpendicularSegmentsProperty(seg1, other),
                    comment,
                    [perp, prop]
                )

class TwoPointsBelongsToTwoPerpendicularsRule(Rule):
    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def sources(self):
        return itertools.combinations(self.context.list(PerpendicularSegmentsProperty), 2)

    def apply(self, src):
        key = frozenset(src)
        if key in self.processed:
            return
        perp0, perp1 = src
        common = next((seg for seg in perp0.segments if seg in perp1.segments), None)
        if common is None:
            self.processed.add(key)
            return
        seg0 = next(seg for seg in perp0.segments if seg != common)
        seg1 = next(seg for seg in perp1.segments if seg != common)
        points = set(seg0.points + seg1.points)
        if len(points) != 3:
            self.processed.add(key)
            return
        ncl = self.context.collinearity_property(*points)
        if ncl is None:
            return
        self.processed.add(key)
        if ncl.collinear:
            return
        yield (
            PointsCoincidenceProperty(*common.points, True),
            LazyComment('%s and %s both lie on perpendiculars to non-parallel lines %s and %s', *common.points, seg0, seg1),
            [perp0, perp1, ncl]
        )

class PerpendicularTransitivityRule(Rule):
    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def sources(self):
        return itertools.combinations(self.context.list(PerpendicularSegmentsProperty), 2)

    def apply(self, src):
        key = frozenset(src)
        if key in self.processed:
            return

        perp0, perp1 = src
        common = next((seg for seg in perp0.segments if seg in perp1.segments), None)
        if common is None:
            self.processed.add(key)
            return
        seg0 = next(seg for seg in perp0.segments if seg != common)
        seg1 = next(seg for seg in perp1.segments if seg != common)
        common_point = next((pt for pt in seg0.points if pt in seg1.points), None)
        if common_point is None:
            self.processed.add(key)
            return
        ne = self.context.not_equal_property(*common.points)
        if ne is None:
            return
        self.processed.add(key)
        pt0 = next(pt for pt in seg0.points if pt != common_point)
        pt1 = next(pt for pt in seg1.points if pt != common_point)
        comment = Comment(
            '$%{segment:seg0}$ and $%{segment:seg1}$ are perpendiculars to line $%{line:line}$',
            {'seg0': seg0, 'seg1': seg1, 'line': common}
        )
        yield (
            PerpendicularSegmentsProperty(common, pt0.segment(pt1)),
            comment,
            [perp0, perp1, ne]
        )
        yield (
            PointsCollinearityProperty(common_point, pt0, pt1, True),
            comment,
            [perp0, perp1, ne]
        )

class PerpendicularToEquidistantRule(SingleSourceRule):
    property_type = PerpendicularSegmentsProperty

    def apply(self, prop):
        if len({*prop.segments[0].points, *prop.segments[1].points}) != 4:
            return
        for seg0, seg1 in (prop.segments, reversed(prop.segments)):
            segments = (
                [seg0.points[0].segment(pt) for pt in seg1.points],
                [seg0.points[1].segment(pt) for pt in seg1.points]
            )
            cs = self.context.congruent_segments_property(*segments[0], True)
            pattern = '$%{point:point}$ lies on the perpendicular bisector to $%{segment:base}$'
            if cs and not(prop.reason.obsolete and cs.reason.obsolete):
                yield (
                    ProportionalLengthsProperty(*segments[1], 1),
                    Comment(pattern, {'point': seg0.points[1], 'base': seg1}),
                    [prop, cs]
                )
            cs = self.context.congruent_segments_property(*segments[1], True)
            if cs and not(prop.reason.obsolete and cs.reason.obsolete):
                yield (
                    ProportionalLengthsProperty(*segments[0], 1),
                    Comment(pattern, {'point': seg0.points[0], 'base': seg1}),
                    [prop, cs]
                )

class EquidistantToPerpendicularRule(Rule):
    def sources(self):
        return itertools.combinations([p for p in self.context.length_ratio_properties(allow_zeroes=True) if p.value == 1], 2)

    def apply(self, src):
        cs0, cs1 = src

        common0 = next((pt for pt in cs0.segment0.points if pt in cs0.segment1.points), None)
        if common0 is None:
            return
        common1 = next((pt for pt in cs1.segment0.points if pt in cs1.segment1.points), None)
        if common1 is None:
            return
        pts0 = [pt for pt in cs0.segment0.points + cs0.segment1.points if pt != common0]
        pts1 = [pt for pt in cs1.segment0.points + cs1.segment1.points if pt != common1]
        if set(pts0) != set(pts1):
            return
        segment0 = common0.segment(common1)
        segment1 = pts0[0].segment(pts0[1])
        if not (cs0.reason.obsolete and cs1.reason.obsolete):
            yield (
                PerpendicularSegmentsProperty(segment0, segment1),
                Comment(
                    'both $%{point:pt0}$ and $%{point:pt1}$ are equidistant from $%{point:endpoint0}$ and $%{point:endpoint1}$',
                    {'pt0': common0, 'pt1': common1, 'endpoint0': pts0[0], 'endpoint1': pts0[1]}
                ),
                [cs0, cs1]
            )
        ne0 = self.context.not_equal_property(common0, common1)
        if ne0 is None:
            return
        ne1 = self.context.not_equal_property(*pts0)
        if ne1 is None:
            return
        if cs0.reason.obsolete and cs1.reason.obsolete and ne0.reason.obsolete and ne1.reason.obsolete:
            return
        yield (
            SameOrOppositeSideProperty(segment0, *pts0, False),
            Comment(
                'perpendicular bisector $%{line:bisector}$ separates endpoints of $%{segment:segment}$',
                {'bisector': segment0, 'segment': segment1}
            ),
            [cs0, cs1, ne0, ne1]
        )

class EqualAnglesToCollinearityRule(SingleSourceRule):
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
        for (p0, p1), bit in ((prop.segment.points, 1), (reversed(prop.segment.points), 2)):
            if mask & bit:
                continue
            angles = [p0.angle(p1, pt) for pt in prop.points]
            ca = self.context.angle_ratio_property(*angles)
            if ca is None:
                continue
            mask |= bit
            if ca.value != 1:
                continue
            comment = Comment(
                '$%{anglemeasure:angle0} = %{anglemeasure:angle1}$, and points $%{point:pt0}$ and $%{point:pt1}$ are on the same side of $%{line:line}$',
                {'angle0': angles[0], 'angle1': angles[1], 'pt0': prop.points[0], 'pt1': prop.points[1], 'line': prop.segment}
            )
            yield (
                AngleValueProperty(p0.angle(*prop.points), 0),
                comment,
                [ca, prop]
            )
            yield (
                PointsCollinearityProperty(p0, *prop.points, True),
                comment,
                [ca, prop]
            )

        if mask != original:
            self.processed[prop] = mask

class AngleInsideBiggerOneRule(SingleSourceRule):
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
        for (p0, p1), bit in ((prop.segment.points, 1), (reversed(prop.segment.points), 2)):
            if mask & bit:
                continue
            angles = [p0.angle(p1, pt) for pt in prop.points]
            av0 = self.context.angle_value_property(angles[0])
            if av0 is None:
                continue
            av1 = self.context.angle_value_property(angles[1])
            if av1 is None:
                continue
            mask |= bit
            if av0.degree == av1.degree:
                comment = Comment(
                    '$%{anglemeasure:angle0} = %{anglemeasure:angle1}$, and points $%{point:pt0}$ and $%{point:pt1}$ are on the same side of $%{line:line}$',
                    {'angle0': angles[0], 'angle1': angles[1], 'pt0': prop.points[0], 'pt1': prop.points[1], 'line': prop.segment}
                )
                yield (
                    AngleValueProperty(p0.angle(*prop.points), 0),
                    comment,
                    [av0, av1, prop]
                )
                yield (
                    PointsCollinearityProperty(p0, *prop.points, True),
                    comment,
                    [av0, av1, prop]
                )
            else:
                common_vector = p0.vector(p1)
                pattern = '$%{angle:a0}$ and $%{angle:a1}$ with common side $%{ray:side}$ and $%{anglemeasure:a0} < %{anglemeasure:a1}$'
                if av0.degree < av1.degree:
                    yield (
                        PointInsideAngleProperty(prop.points[0], av1.angle),
                        Comment(
                            pattern,
                            {'a0': av0.angle, 'a1': av1.angle, 'side': common_vector}
                        ),
                        [av0, av1, prop]
                    )
                else:
                    yield (
                        PointInsideAngleProperty(prop.points[1], av0.angle),
                        Comment(
                            pattern,
                            {'a0': av1.angle, 'a1': av0.angle, 'side': common_vector}
                        ),
                        [av1, av0, prop]
                    )

        if mask != original:
            self.processed[prop] = mask

class PointsSeparatedByLineAreNotCoincidentRule(SingleSourceRule):
    """
    If two points are separated by a line, the points are not coincident
    """
    property_type = SameOrOppositeSideProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def accepts(self, prop):
        return not prop.same and prop not in self.processed

    def apply(self, prop):
        self.processed.add(prop)

        yield (
            PointsCoincidenceProperty(prop.points[0], prop.points[1], False),
            Comment('the points are separated by $%{line:line}$', {'line': prop.segment}),
            [prop]
        )

class SameSidePointInsideSegmentRule(SingleSourceRule):
    """
    If endpoints of a segment are on the same side of a line,
    then any point inside the segment in on the same side too
    """
    property_type = SameOrOppositeSideProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def accepts(self, prop):
        return prop.same

    def apply(self, prop):
        segment = prop.points[0].segment(prop.points[1])
        for inside in self.context.points_inside_segment(segment):
            key = (prop, inside)
            if key in self.processed:
                continue
            self.processed.add(key)
            inside_prop = self.context.angle_value_property(inside.angle(*prop.points))
            for endpoint in prop.points:
                yield (
                    SameOrOppositeSideProperty(prop.segment, endpoint, inside, True),
                    Comment(
                        'segment $%{segment:segment}$ does not cross line $%{line:line}$',
                        {'segment': segment, 'line': prop.segment}
                    ),
                    [prop, inside_prop]
                )

class PointInsideSegmentRelativeToLineRule(SingleSourceRule):
    property_type = SameOrOppositeSideProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def apply(self, prop):
        for index, (pt_on, pt_not_on) in enumerate(itertools.product(prop.segment.points, prop.points)):
            segment = pt_on.segment(pt_not_on)
            for inside in self.context.points_inside_segment(segment):
                if inside in prop.points:
                    continue
                key = (prop, index, inside)
                if key in self.processed:
                    continue
                self.processed.add(key)
                pt2 = prop.points[1] if pt_not_on == prop.points[0] else prop.points[0]
                if prop.same:
                    pattern = '$%{point:pt_not_on}$ and $%{point:pt2}$ are on the same side of $%{line:line}$ and $%{point:inside}$ lies inside $%{segment:segment}$'
                else:
                    pattern = '$%{point:pt_not_on}$ and $%{point:pt2}$ are on opposide sides of $%{line:line}$ and $%{point:inside}$ lies inside $%{segment:segment}$'
                inside_prop = self.context.angle_value_property(inside.angle(*segment.points))
                yield (
                    SameOrOppositeSideProperty(prop.segment, inside, pt2, prop.same),
                    Comment(pattern, {
                        'pt_not_on': pt_not_on,
                        'pt2': pt2,
                        'line': prop.segment,
                        'inside': inside,
                        'segment': segment
                    }),
                    [prop, inside_prop]
                )

class TwoPerpendicularsRule(SingleSourceRule):
    """
    Two perpendiculars to the same line are parallel
    """
    property_type = SameOrOppositeSideProperty

    def apply(self, prop):
        foot0, reasons0 = self.context.foot_of_perpendicular(prop.points[0], prop.segment)
        if foot0 is None:
            return
        foot1, reasons1 = self.context.foot_of_perpendicular(prop.points[1], prop.segment)
        if foot1 is None:
            return
        premises = [prop] + reasons0 + reasons1
        if all(p.reason.obsolete for p in premises):
            return
        vec0 = foot0.vector(prop.points[0])
        vec1 = foot1.vector(prop.points[1]) if prop.same else prop.points[1].vector(foot1)
        yield (
            ParallelVectorsProperty(vec0, vec1),
            Comment('two perpendiculars to $%{line:line}$', {'line': prop.segment}),
            premises
        )

class TwoPerpendicularsRule2(Rule):
    """
    Two perpendiculars to the same line are parallel
    """
    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def sources(self):
        return itertools.combinations(self.context.list(PerpendicularSegmentsProperty), 2)

    def apply(self, src):
        key = frozenset(src)
        if key in self.processed:
            return

        perp0, perp1 = src
        common = next((seg for seg in perp0.segments if seg in perp1.segments), None)
        if common is None:
            self.processed.add(key)
            return
        ne = self.context.not_equal_property(*common.points)
        if ne is None:
            return
        self.processed.add(key)
        other0 = next(seg for seg in perp0.segments if seg != common)
        other1 = next(seg for seg in perp1.segments if seg != common)
        yield (
            ParallelSegmentsProperty(other0, other1),
            Comment(
                '$%{segment:seg0} \\perp %{segment:seg1} \\perp %{segment:seg2}$',
                {'seg0': other0, 'seg1': common, 'seg2': other1}
            ),
            [perp0, perp1, ne]
        )

class ParallelSameSideRule(SingleSourceRule):
    property_type = ParallelSegmentsProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = {}

    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0x3:
            return
        original = mask
        for seg0, seg1, bit in ((*prop.segments, 1), (*reversed(prop.segments), 2)):
            if mask & bit:
                continue
            ncl = False
            if seg1.points[0] not in seg0.points:
                ncl = self.context.collinearity_property(*seg0.points, seg1.points[0])
            if not ncl and seg1.points[1] not in seg0.points:
                ncl = self.context.collinearity_property(*seg0.points, seg1.points[1])
            if ncl is None:
                continue
            mask |= bit
            if ncl == False or ncl.collinear:
                continue
            yield (
                SameOrOppositeSideProperty(seg0, *seg1.points, True),
                Comment(
                    '$%{point:pt0}$ and $%{point:pt1}$ lie on a line parallel to $%{line:line}$',
                    {'pt0': seg1.points[0], 'pt1': seg1.points[1], 'line': seg0}
                ),
                [prop, ncl]
            )
        if mask != original:
            self.processed[prop] = mask

class LengthProductEqualityToRatioRule(SingleSourceRule):
    property_type = EqualLengthProductsProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = {}

    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0xF:
            return

        ne = [self.context.coincidence_property(*seg.points) for seg in prop.segments]
        original = mask
        for i, j, k, l, bit in [(0, 1, 2, 3, 0x1), (0, 2, 1, 3, 0x2), (3, 1, 2, 0, 0x4), (3, 2, 1, 0, 0x8)]:
            if mask & bit:
                continue
            if ne[j] is None or ne[l] is None:
                continue
            mask |= bit
            if ne[j].coincident or ne[l].coincident:
                continue

            if prop.segments[j] == prop.segments[l]:
                yield (
                    ProportionalLengthsProperty(prop.segments[i], prop.segments[k], 1),
                    prop.reason.comment,
                    prop.reason.premises + [ne[j], ne[l]]
                )
            elif prop.segments[i] == prop.segments[j]:
                yield (
                    ProportionalLengthsProperty(prop.segments[k], prop.segments[l], 1),
                    prop.reason.comment,
                    prop.reason.premises + [ne[j]]
                )
            elif prop.segments[k] == prop.segments[l]:
                yield (
                    ProportionalLengthsProperty(prop.segments[i], prop.segments[j], 1),
                    prop.reason.comment,
                    prop.reason.premises + [ne[l]]
                )
            else:
                yield (
                    EqualLengthRatiosProperty(*[prop.segments[x] for x in (i, j, k, l)]),
                    prop.reason.comment,
                    prop.reason.premises + [ne[j], ne[l]]
                )

        if mask != original:
            self.processed[prop] = mask

class RotatedAngleSimplifiedRule(Rule):
    def __init__(self, context):
        super().__init__(context)
        self.processed = {}

    def sources(self):
        for prop in self.context.angle_value_properties_for_degree(180, lambda a: a.vertex):
            segment = prop.angle.endpoints[0].segment(prop.angle.endpoints[1])
            for oppo in self.context.list(SameOrOppositeSideProperty, [segment]):
                if oppo.same:
                    yield (prop, oppo)

    def apply(self, src):
        mask = self.processed.get(src, 0)
        if mask == 0x3:
            return
        prop, oppo = src
        ang = prop.angle
        angles0 = (
            ang.vertex.angle(ang.endpoints[0], oppo.points[0]),
            ang.vertex.angle(ang.endpoints[1], oppo.points[1])
        )
        angles1 = (
            ang.vertex.angle(ang.endpoints[0], oppo.points[1]),
            ang.vertex.angle(ang.endpoints[1], oppo.points[0])
        )

        original = mask
        for angs0, angs1, bit in [(angles0, angles1, 1), (angles1, angles0, 2)]:
            if mask & bit:
                continue
            ar = self.context.angle_ratio_property(*angs0)
            if ar is None:
                continue
            if ar.value != 1:
                mask = 0x3
                break
            mask |= bit
            yield (
                AngleRatioProperty(*angs1, 1),
                LazyComment('TODO: write comment'),
                [ar, prop, oppo]
            )

        if mask != original:
            self.processed[src] = mask

class RotatedAngleRule(Rule):
    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def sources(self):
        return [(a0, a1) for a0, a1 in self.context.congruent_angles_with_vertex() if a0.vertex == a1.vertex and (a0, a1) not in self.processed]

    def apply(self, src):
        ang0, ang1 = src
        vertex = ang0.vertex
        pts0 = ang0.endpoints
        pts1 = ang1.endpoints
        if next((p for p in pts0 if p in pts1), None) is not None:
            self.processed.add(src)
            return
        co = self.context.same_cyclic_order_property(Cycle(vertex, *pts0), Cycle(vertex, *pts1))
        if co is None:
            pts1 = (pts1[1], pts1[0])
            co = self.context.same_cyclic_order_property(Cycle(vertex, *pts0), Cycle(vertex, *pts1))
        if co is None:
            return
        self.processed.add(src)
        ca = self.context.angle_ratio_property(ang0, ang1)
        new_angle0 = vertex.angle(pts0[0], pts1[0])
        new_angle1 = vertex.angle(pts0[1], pts1[1])
        yield (
            AngleRatioProperty(new_angle0, new_angle1, 1),
            Comment(
                '$%{angle:angle0}$ is $%{angle:angle1}$ rotated by $%{anglemeasure:rot_angle0} = %{anglemeasure:rot_angle1}$',
                {'angle0': new_angle0, 'angle1': new_angle1, 'rot_angle0': ang0, 'rot_angle1': ang1}
            ),
            [ca, co]
        )

class PointInsidePartOfAngleRule(SingleSourceRule):
    property_type = PointInsideAngleProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def apply(self, prop):
        for pt in prop.angle.endpoints:
            part = prop.angle.vertex.angle(pt, prop.point)
            for prop1 in self.context.list(PointInsideAngleProperty, [part]):
                key = (prop, prop1)
                if key in self.processed:
                    continue
                self.processed.add(key)
                comment = Comment(
                    '$%{point:point}$ lies inside $%{angle:part}$ that is part of $%{angle:full}$',
                    {'point': prop1.point, 'part': part, 'full': prop.angle}
                )
                yield (
                    PointInsideAngleProperty(prop1.point, prop.angle),
                    comment,
                    [prop1, prop]
                )
                pt1 = next(p for p in prop.angle.endpoints if p != pt)
                yield (
                    PointInsideAngleProperty(prop.point, prop.angle.vertex.angle(pt1, prop1.point)),
                    comment,
                    [prop1, prop]
                )

class PartOfAcuteAngleIsAcuteRule(SingleSourceRule):
    property_type = PointInsideAngleProperty

    def apply(self, prop):
        kind = self.context.angle_kind_property(prop.angle)
        if kind is None or prop.reason.obsolete and kind.reason.obsolete:
            return
        if kind.kind == AngleKindProperty.Kind.acute:
            pattern = '$%{angle:part}$ is a part of acute $%{angle:whole}$'
        elif kind.kind == AngleKindProperty.Kind.right:
            pattern = '$%{angle:part}$ is a part of right $%{angle:whole}$'
        else:
            return
        for vec in prop.angle.vectors:
            angle = prop.angle.vertex.angle(vec.end, prop.point)
            yield (
                AngleKindProperty(angle, AngleKindProperty.Kind.acute),
                Comment(pattern, {'part': angle, 'whole': prop.angle}),
                [prop, kind]
            )

class AngleTypeByDegreeRule(Rule):
    def sources(self):
        return self.context.nondegenerate_angle_value_properties()

    def apply(self, prop):
        if prop.reason.obsolete:
            return
        if prop.degree in (0, 180):
            return
        pattern = '$%{degree:min} < %{anglemeasure:angle} = %{degree:degree} < %{degree:max}$'
        if prop.degree < 90:
            yield (
                AngleKindProperty(prop.angle, AngleKindProperty.Kind.acute),
                Comment(pattern, {'angle': prop.angle, 'degree': prop.degree, 'min': 0, 'max': 90}),
                [prop]
            )
        elif prop.degree > 90:
            yield (
                AngleKindProperty(prop.angle, AngleKindProperty.Kind.obtuse),
                Comment(pattern, {'angle': prop.angle, 'degree': prop.degree, 'min': 90, 'max': 180}),
                [prop]
            )
        else:
            yield (
                AngleKindProperty(prop.angle, AngleKindProperty.Kind.right),
                prop.reason.comment,
                prop.reason.premises
            )

class PointsCollinearityByAngleDegreeRule(Rule):
    def sources(self):
        return self.context.angle_value_properties()

    def apply(self, prop):
        if prop.angle.vertex is None or prop.reason.obsolete:
            return
        yield (
            PointsCollinearityProperty(*prop.angle.point_set, prop.degree in (0, 180)),
            Comment(
                '$%{anglemeasure:angle} = %{degree:degree}$',
                {'angle': prop.angle, 'degree': prop.degree}
            ),
            [prop]
        )

class RightAngleDegreeRule(SingleSourceRule):
    property_type = AngleKindProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def accepts(self, prop):
        return prop.kind == AngleKindProperty.Kind.right and prop not in self.processed

    def apply(self, prop):
        self.processed.add(prop)

        yield (
            AngleValueProperty(prop.angle, 90),
            prop.reason.comment,
            prop.reason.premises
        )

class AngleTypesInObtuseangledTriangleRule(SingleSourceRule):
    property_type = AngleKindProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def accepts(self, prop):
        return prop.angle.vertex and prop.kind != AngleKindProperty.Kind.acute and prop not in self.processed

    def apply(self, prop):
        self.processed.add(prop)

        if prop.kind == AngleKindProperty.Kind.obtuse:
            pattern = 'an angle of $%{triangle:triangle}$, another $%{angle:other}$ is obtuse'
        else:
            pattern = 'an angle of $%{triangle:triangle}$, another $%{angle:other}$ is right'
        triangle = Scene.Triangle(prop.angle.vertex, *prop.angle.endpoints)
        comment = Comment(pattern, {'triangle': triangle, 'other': prop.angle})
        for angle in triangle.angles[1:]:
            yield (
                AngleKindProperty(angle, AngleKindProperty.Kind.acute),
                comment,
                [prop]
            )

class VerticalAnglesRule(Rule):
    def sources(self):
        return itertools.combinations(self.context.angle_value_properties_for_degree(180, lambda a: a.vertex), 2)

    @classmethod
    def priority(clazz):
        return 1

    def apply(self, src):
        av0, av1 = src
        if av0.reason.obsolete and av1.reason.obsolete:
            return
        ng0 = av0.angle
        ng1 = av1.angle
        if ng0.vertex != ng1.vertex:
            return
        if len(ng0.point_set.union(ng1.point_set)) != 5:
            return

        pattern = '$%{angle:angle0}$ and $%{angle:angle1}$ are vertical angles'
        new_prop = AngleRatioProperty(
            ng0.vertex.angle(ng0.vectors[0].end, ng1.vectors[0].end),
            ng0.vertex.angle(ng0.vectors[1].end, ng1.vectors[1].end),
            1
        )
        yield (
            new_prop,
            Comment(pattern, {'angle0': new_prop.angle0, 'angle1': new_prop.angle1}),
            [av0, av1]
        )
        new_prop = AngleRatioProperty(
            ng0.vertex.angle(ng0.vectors[0].end, ng1.vectors[1].end),
            ng0.vertex.angle(ng0.vectors[1].end, ng1.vectors[0].end),
            1
        )
        yield (
            new_prop,
            Comment(pattern, {'angle0': new_prop.angle0, 'angle1': new_prop.angle1}),
            [av0, av1]
        )

class ReversedVerticalAnglesRule(Rule):
    def __init__(self, context):
        super().__init__(context)
        self.processed = {} # pair (prop, oppo) => mask

    def sources(self):
        return self.context.angle_value_properties_for_degree(180, lambda a: a.vertex)

    def apply(self, prop):
        angle = prop.angle
        line = angle.vectors[0].end.segment(angle.vectors[1].end)
        for oppo in self.context.list(SameOrOppositeSideProperty, [line]):
            if oppo.same:
                continue
            key = (prop, oppo)
            mask = self.processed.get(key, 0)
            if mask == 0x3:
                continue
            original = mask
            for pt0, pt1, bit in ((*oppo.points, 0x1), (*reversed(oppo.points), 0x2)):
                if mask & bit:
                    continue
                ang0 = angle.vertex.angle(angle.vectors[0].end, pt0)
                ang1 = angle.vertex.angle(angle.vectors[1].end, pt1)
                ar = self.context.angle_ratio_property(ang0, ang1)
                if ar is None:
                    continue
                mask |= bit
                if ar.value != 1:
                    continue
                yield (
                    AngleValueProperty(angle.vertex.angle(pt0, pt1), 180),
                    Comment(
                        '$%{anglemeasure:angle0} = %{anglemeasure:angle1}$ and $%{point:pt}$ lies on segment $%{segment:segment}$',
                        {'angle0': ang0, 'angle1': ang1, 'pt': angle.vertex, 'segment': angle.endpoints[0].segment(angle.endpoints[1])}
                    ),
                    [ar, prop, oppo]
                )
            if mask != original:
                self.processed[key] = mask

class CorrespondingAndAlternateAnglesRule(SingleSourceRule):
    property_type = SameOrOppositeSideProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = {}

    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0x3:
            return
        original = mask

        lp0 = prop.segment.points[0]
        lp1 = prop.segment.points[1]
        for pt0, pt1, bit in [(*prop.points, 1), (*reversed(prop.points), 2)]:
            if mask & bit:
                continue
            angle0 = lp0.angle(pt0, lp1)
            angle1 = lp1.angle(pt1, lp0)
            if prop.same:
                sum_degree = self.context.sum_of_two_angles(angle0, angle1)
                if sum_degree is None:
                    continue
                mask |= bit
                if sum_degree != 180:
                    continue
                sum_reason = self.context.sum_of_two_angles_property(angle0, angle1)
                for p in AngleValueProperty.generate(lp0.vector(pt0), lp1.vector(pt1), 0):
                    yield (
                        p,
                        Comment(
                            'sum of consecutive angles: $%{anglemeasure:angle0} + %{anglemeasure:angle1} = %{degree:180}$',
                            {'angle0': angle0, 'angle1': angle1, '180': 180}
                        ),
                        [prop, sum_reason]
                    )
            else:
                ratio_reason = self.context.angle_ratio_property(angle0, angle1)
                if ratio_reason is None:
                    continue
                mask |= bit
                if ratio_reason.value != 1:
                    continue
                for p in AngleValueProperty.generate(lp0.vector(pt0), pt1.vector(lp1), 0):
                    yield (
                        p,
                        Comment(
                            'alternate angles $%{angle:angle0}$ and $%{angle:angle1}$ are congruent',
                            {'angle0': angle0, 'angle1': angle1}
                        ),
                        [prop, ratio_reason]
                    )

        if mask != original:
            self.processed[prop] = mask

class CyclicOrderRule(SingleSourceRule):
    property_type = SameOrOppositeSideProperty

    def apply(self, prop):
        if prop.reason.obsolete:
            return
        cycle0 = Cycle(*prop.segment.points, prop.points[0])
        cycle1 = Cycle(*prop.segment.points, prop.points[1])
        if not prop.same:
            cycle1 = cycle1.reversed
            pattern = '$%{line:line}$ separates $%{point:pt0}$ and $%{point:pt1}$'
        else:
            pattern = '$%{point:pt0}$ and $%{point:pt1}$ are on the same side of $%{line:line}$'
        comment = Comment(pattern, {'line': prop.segment, 'pt0': prop.points[0], 'pt1': prop.points[1]})
        yield (SameCyclicOrderProperty(cycle0, cycle1), comment, [prop])
        yield (SameCyclicOrderProperty(cycle0.reversed, cycle1.reversed), comment, [prop])

class SupplementaryAnglesRule(SingleSourceRule):
    property_type = AngleValueProperty

    def accepts(self, prop):
        return prop.angle.vertex and prop.degree == 180

    def apply(self, prop):
        ang = prop.angle
        for pt in self.context.non_coincident_points(ang.vertex):
            if pt in ang.endpoints:
                continue
            ne = self.context.coincidence_property(pt, ang.vertex)
            if prop.reason.obsolete and ne.reason.obsolete:
                continue
            yield (
                SumOfTwoAnglesProperty(
                    ang.vertex.angle(ang.vectors[0].end, pt),
                    ang.vertex.angle(pt, ang.vectors[1].end),
                    180
                ),
                LazyComment('supplementary angles'),
                [prop, ne]
            )

class TransversalRule(Rule):
    def sources(self):
        return self.context.angle_value_properties_for_degree(0) + self.context.angle_value_properties_for_degree(180)

    def apply(self, prop):
        ang = prop.angle
        for point in ang.point_set:
            for nep in self.context.non_coincident_points(point):
                common0 = next((pt for pt in (point, nep) if pt in ang.vectors[0].points), None)
                if common0 is None:
                    continue
                common1 = next((pt for pt in (point, nep) if pt in ang.vectors[1].points), None)
                if common1 is None:
                    continue
                vec = common0.vector(next(pt for pt in (point, nep) if pt != common0))
                if vec.as_segment in (ang.vectors[0].as_segment, ang.vectors[1].as_segment):
                    continue

                ne = self.context.coincidence_property(point, nep)
                if prop.reason.obsolete and ne.reason.obsolete:
                    continue

                rev = prop.degree == 180
                if ang.vectors[0].start == common0:
                    vec0 = ang.vectors[0]
                else:
                    vec0 = ang.vectors[0].reversed
                    rev = not rev
                ngl0 = vec.angle(vec0)

                if common0 == common1:
                    if ang.vectors[1].start == common1:
                        vec1 = ang.vectors[1]
                    else:
                        vec1 = ang.vectors[1].reversed
                        rev = not rev
                    ngl1 = vec.angle(vec1)
                else:
                    if ang.vectors[1].start == common1:
                        vec1 = ang.vectors[1]
                        rev = not rev
                    else:
                        vec1 = ang.vectors[1].reversed
                    ngl1 = vec.reversed.angle(vec1)

                if ang.vertex is None and (vec0 == ang.vectors[0]) != (vec1 == ang.vectors[1]):
                    continue

                if rev:
                    new_prop = SumOfTwoAnglesProperty(ngl0, ngl1, 180)
                    if common0 == common1:
                        pattern = 'supplementary angles: common side $%{ray:common}$, and $%{ray:vec0} \\uparrow\\!\\!\\!\\downarrow %{ray:vec1}$'
                    else:
                        pattern = 'consecutive angles: common line $%{line:common}$, and $%{ray:vec0} \\uparrow\\!\\!\\!\\uparrow %{ray:vec1}$'
                else:
                    if common0 == common1:
                        new_prop = AngleRatioProperty(ngl0, ngl1, 1, same=True)
                        pattern = 'same angle: common ray $%{ray:common}$, and $%{ray:vec0}$ coincides with $%{ray:vec1}$'
                    else:
                        new_prop = AngleRatioProperty(ngl0, ngl1, 1)
                        pattern = 'alternate angles: common line $%{line:common}$, and $%{ray:vec0} \\uparrow\\!\\!\\!\\downarrow %{ray:vec1}$'
                comment = Comment(pattern, {'common': vec, 'vec0': vec0, 'vec1': vec1})
                yield (new_prop, comment, [prop, ne])

class TwoPointsInsideSegmentRule(Rule):
    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def sources(self):
        segment_to_props = {}
        for av in self.context.angle_value_properties_for_degree(180, lambda a: a.vertex):
            segment = av.angle.endpoints[0].segment(av.angle.endpoints[1])
            props = segment_to_props.get(segment)
            if props:
                props.add(av)
            else:
                segment_to_props[segment] = {av}

        for segment, props in segment_to_props.items():
            for av0, av1 in itertools.combinations(props, 2):
                key = frozenset([av0.angle, av1.angle])
                if key not in self.processed:
                    self.processed.add(key)
                    yield (segment, av0, av1)

    def apply(self, src):
        segment, av0, av1 = src

        pt0 = av0.angle.vertex
        pt1 = av1.angle.vertex
        for pt in segment.points:
            yield (
                AngleValueProperty(pt.angle(pt0, pt1), 0),
                Comment(
                    'both $%{point:pt0}$ and $%{point:pt1}$ lie inside segment $%{segment:segment}$',
                    {'pt0': pt0, 'pt1': pt1, 'segment': segment}
                ),
                [av0, av1]
            )

class TwoPointsOnRayRule(Rule):
    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def sources(self):
        return self.context.angle_value_properties_for_degree(0, lambda a: a.vertex)

    def apply(self, prop):
        zero = prop.angle
        pt0, pt1 = zero.endpoints
        for pt in self.context.not_collinear_points(zero.vectors[0].as_segment):
            key = (zero, pt)
            if key in self.processed:
                continue
            angle0 = pt0.angle(zero.vertex, pt)
            value0 = self.context.angle_value_property(angle0)
            if value0 is None:
                continue
            angle1 = pt1.angle(zero.vertex, pt)
            value1 = self.context.angle_value_property(angle1)
            if value1 is None:
                continue
            self.processed.add(key)
            pattern = '$%{point:pt}$ lies on $%{ray:ray}$ and $%{anglemeasure:lesser} < %{anglemeasure:greater}$'
            if value0.degree < value1.degree:
                comment = Comment(
                    pattern,
                    {'pt': pt0, 'ray': zero.vertex.vector(pt1), 'lesser': angle0, 'greater': angle1}
                )
                yield (
                    AngleValueProperty(pt0.angle(pt1, zero.vertex), 0),
                    comment,
                    [prop, value0, value1]
                )
                yield (
                    AngleValueProperty(pt1.angle(pt0, zero.vertex), 180),
                    comment,
                    [prop, value0, value1]
                )
                yield (
                    PointsCoincidenceProperty(pt0, pt1, False),
                    Comment(
                        '$%{anglemeasure:angle0} \\neq %{anglemeasure:angle1}$',
                        {'angle0': angle0, 'angle1': angle1}
                    ),
                    [value0, value1]
                )
            elif value1.degree < value0.degree:
                comment = Comment(
                    pattern,
                    {'pt': pt1, 'ray': zero.vertex.vector(pt0), 'lesser': angle1, 'greater': angle0}
                )
                yield (
                    AngleValueProperty(pt1.angle(pt0, zero.vertex), 0),
                    comment,
                    [prop, value0, value1]
                )
                yield (
                    AngleValueProperty(pt0.angle(pt1, zero.vertex), 180),
                    comment,
                    [prop, value0, value1]
                )
                yield (
                    PointsCoincidenceProperty(pt0, pt1, False),
                    Comment(
                        '$%{anglemeasure:angle0} \\neq %{anglemeasure:angle1}$',
                        {'angle0': angle0, 'angle1': angle1}
                    ),
                    [value0, value1]
                )
            else:
                yield (
                    PointsCoincidenceProperty(pt0, pt1, True),
                    Comment(
                        '$%{point:pt}$ lies on $%{ray:ray}$ and $%{anglemeasure:angle0} = %{anglemeasure:angle1}$',
                        {'pt': pt0, 'ray': zero.vertex.vector(pt1), 'angle0': angle0, 'angle1': angle1}
                    ),
                    [prop, value0, value1]
                )

class SameAngleRule(Rule):
    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def sources(self):
        return itertools.combinations([av for av in self.context.list(AngleValueProperty) if av.angle.vertex and av.degree == 0], 2)

    def apply(self, src):
        if src in self.processed:
            return
        self.processed.add(src)

        av0, av1 = src
        ng0 = av0.angle
        ng1 = av1.angle
        if ng0.vertex != ng1.vertex:
            return
        if len(ng0.point_set.union(ng1.point_set)) != 5:
            return

        angle0 = ng0.vertex.angle(ng0.vectors[0].end, ng1.vectors[0].end)
        angle1 = ng0.vertex.angle(ng0.vectors[1].end, ng1.vectors[1].end)
        yield (
            AngleRatioProperty(angle0, angle1, 1, same=True),
            Comment(
                '$%{vector:vec0} \\uparrow\\!\\!\\!\\uparrow %{vector:vec1}$ and $%{vector:vec2} \\uparrow\\!\\!\\!\\uparrow %{vector:vec3}$',
                {
                    'vec0': ng0.vectors[0],
                    'vec1': ng0.vectors[1],
                    'vec2': ng1.vectors[0],
                    'vec3': ng1.vectors[1]
                }
            ),
            [av0, av1]
        )

class SameAngleRule2(Rule):
    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def sources(self):
        return self.context.angle_value_properties_for_degree(180, lambda a: a.vertex)

    def apply(self, prop):
        angle = prop.angle
        side = angle.endpoints[0].segment(angle.endpoints[1])
        for pt in self.context.not_collinear_points(side):
            key = (angle, pt)
            if key in self.processed:
                continue
            self.processed.add(key)

            for pt0, pt1 in (angle.endpoints, reversed(angle.endpoints)):
                angle0 = pt0.angle(pt, pt1)
                angle1 = pt0.angle(pt, angle.vertex)
                yield (
                    AngleRatioProperty(angle0, angle1, 1, same=True),
                    Comment(
                        '$%{point:pt}$ lies on side $%{segment:side}$ of $%{angle:angle}$',
                        {'pt': angle.vertex, 'side': side, 'angle': angle0}
                    ),
                    [prop]
                )
                pattern = '$%{point:pt}$ lies on side $%{segment:side}$ of $%{angle:angle}$, $%{anglemeasure:known} = %{degree:degree}$'
                value = self.context.angle_value_property(angle0)
                if value:
                    yield (
                        AngleValueProperty(angle1, value.degree),
                        Comment(
                            pattern,
                            {'pt': angle.vertex, 'side': side, 'angle': angle0, 'known': angle0, 'degree': value.degree}
                        ),
                        [prop, value]
                    )
                value = self.context.angle_value_property(angle1)
                if value:
                    yield (
                        AngleValueProperty(angle0, value.degree),
                        Comment(
                            pattern,
                            {'pt': angle.vertex, 'side': side, 'angle': angle0, 'known': angle1, 'degree': value.degree}
                        ),
                        [prop, value]
                    )

class SameAngleDegreeRule(Rule):
    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def sources(self):
        return self.context.nondegenerate_angle_value_properties()

    def apply(self, prop):
        angle = prop.angle
        for vec0, vec1 in (angle.vectors, reversed(angle.vectors)):
            for inside in self.context.points_inside_segment(vec0.as_segment):
                pt = inside
                key = (angle, pt)
                if key in self.processed:
                    continue
                self.processed.add(key)

                inside_prop = self.context.angle_value_property(inside.angle(*vec0.points))
                yield (
                    AngleValueProperty(vec1.angle(vec0.start.vector(pt)), prop.degree),
                    Comment(
                        '$%{point:pt}$ lies on side $%{segment:side}$ of $%{angle:angle}$, $%{anglemeasure:angle} = %{degree:degree}$',
                        {'pt': pt, 'side': vec0, 'angle': angle, 'degree': prop.degree}
                    ),
                    [prop, inside_prop]
                )

class PlanePositionsToLinePositionsRule(SingleSourceRule):
    property_type = SameOrOppositeSideProperty

    def apply(self, prop):
        pt0 = prop.points[0]
        pt1 = prop.points[1]
        crossing, reasons = self.context.intersection_of_lines(prop.segment, pt0.segment(pt1))
        if not crossing:
            return
        if prop.reason.obsolete and all(p.reason.obsolete for p in reasons):
            return
        if prop.same:
            pattern = '$%{point:crossing}$ is the intersection of lines $%{line:line0}$ and $%{line:line1}$'
            new_prop = AngleValueProperty(crossing.angle(pt0, pt1), 0)
        else:
            pattern = '$%{point:crossing}$ is the intersection of segment $%{segment:line0}$ and line $%{line:line1}$'
            new_prop = AngleValueProperty(crossing.angle(pt0, pt1), 180)
        yield (
            new_prop,
            Comment(pattern, {'crossing': crossing, 'line0': pt0.segment(pt1), 'line1': prop.segment}),
            [prop] + reasons
        )

class CeviansIntersectionRule(Rule):
    def sources(self):
        return itertools.combinations(self.context.angle_value_properties_for_degree(180, lambda a: a.vertex), 2)

    def apply(self, src):
        av0, av1 = src
        ends0 = (av0.angle.vectors[0].end, av0.angle.vectors[1].end)
        ends1 = (av1.angle.vectors[0].end, av1.angle.vectors[1].end)
        vertex = next((pt for pt in ends0 if pt in ends1), None)
        if vertex is None:
            return
        pt0 = next(pt for pt in ends0 if pt != vertex)
        pt1 = next(pt for pt in ends1 if pt != vertex)
        if pt0 == pt1:
            return
        ncl = self.context.collinearity_property(vertex, pt0, pt1)
        if ncl is None or ncl.collinear:
            return
        segment0 = pt0.segment(av1.angle.vertex)
        segment1 = pt1.segment(av0.angle.vertex)
        crossing, reasons = self.context.intersection_of_lines(segment0, segment1)
        if crossing is None:
            return
        if av0.reason.obsolete and av1.reason.obsolete and ncl.reason.obsolete and all(r.reason.obsolete for r in reasons):
            return
        comment = Comment(
            '$%{point:crossing}$ is the intersection of cevians $%{segment:cevian0}$ and $%{segment:cevian1}$ with feet $%{point:foot0}$ and $%{point:foot1}$ on sides of $%{triangle:triangle}$',
            {
                'crossing': crossing,
                'cevian0': segment0,
                'cevian1': segment1,
                'foot0': av1.angle.vertex,
                'foot1': av0.angle.vertex,
                'triangle': Scene.Triangle(vertex, pt0, pt1)
            }
        )
        yield (
            PointInsideAngleProperty(crossing, vertex.angle(pt0, pt1)),
            comment,
            [ncl, av0, av1] + reasons
        )
        yield (
            PointInsideAngleProperty(crossing, pt0.angle(vertex, pt1)),
            comment,
            [ncl, av0, av1] + reasons
        )
        yield (
            PointInsideAngleProperty(crossing, pt1.angle(vertex, pt0)),
            comment,
            [ncl, av0, av1] + reasons
        )

class TwoAnglesWithCommonSideRule(SingleSourceRule):
    property_type = PointInsideAngleProperty

    def apply(self, prop):
        av = self.context.angle_value_property(prop.angle)
        if av is None or prop.reason.obsolete and av.reason.obsolete:
            return
        angle0 = prop.angle.vertex.angle(prop.angle.vectors[0].end, prop.point)
        angle1 = prop.angle.vertex.angle(prop.angle.vectors[1].end, prop.point)
        yield (
            SumOfTwoAnglesProperty(angle0, angle1, av.degree),
            Comment(
                '$%{anglemeasure:angle0} + %{anglemeasure:angle1} = %{anglemeasure:sum} = %{degree:degree}$',
                {'angle0': angle0, 'angle1': angle1, 'sum': prop.angle, 'degree': av.degree}
            ),
            [prop, av]
        )

class TwoAnglesWithCommonSideDegreeRule(SingleSourceRule):
    property_type = PointInsideAngleProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = {}

    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0x7:
            return

        angle0 = prop.angle.vertex.angle(prop.angle.vectors[0].end, prop.point)
        angle1 = prop.angle.vertex.angle(prop.angle.vectors[1].end, prop.point)
        av0 = self.context.angle_value_property(angle0)
        av1 = self.context.angle_value_property(angle1)
        if av0 is None and av1 is None:
            return
        av_sum = self.context.angle_value_property(prop.angle)

        original = mask

        if (mask & 0x1) == 0 and av0 and av1:
            mask |= 0x1
            yield (
                AngleValueProperty(prop.angle, av0.degree + av1.degree),
                Comment(
                    '$%{anglemeasure:sum} = %{anglemeasure:angle0} + %{anglemeasure:angle1} = %{degree:degree0} + %{degree:degree1}$',
                    {'sum': prop.angle, 'angle0': angle0, 'angle1': angle1, 'degree0': av0.degree, 'degree1': av1.degree}
                ),
                [prop, av0, av1]
            )
        if (mask & 0x2) == 0 and av0 and av_sum:
            mask |= 0x2
            yield (
                AngleValueProperty(angle1, av_sum.degree - av0.degree),
                Comment(
                    '$%{anglemeasure:angle1} = %{anglemeasure:sum} - %{anglemeasure:angle0} = %{degree:degree_sum} - %{degree:degree0}$',
                    {'sum': prop.angle, 'angle0': angle0, 'angle1': angle1, 'degree0': av0.degree, 'degree_sum': av_sum.degree}
                ),
                [prop, av_sum, av0]
            )
        if (mask & 0x4) == 0 and av1 and av_sum:
            mask |= 0x4
            yield (
                AngleValueProperty(angle0, av_sum.degree - av1.degree),
                Comment(
                    '$%{anglemeasure:angle0} = %{anglemeasure:sum} - %{anglemeasure:angle1} = %{degree:degree_sum} - %{degree:degree1}$',
                    {'sum': prop.angle, 'angle0': angle0, 'angle1': angle1, 'degree1': av1.degree, 'degree_sum': av_sum.degree}
                ),
                [prop, av_sum, av1]
            )

        if mask != original:
            self.processed[prop] = mask

class SameSideToInsideAngleRule(SingleSourceRule):
    property_type = SameOrOppositeSideProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = {}

    def accepts(self, prop):
        return not prop.same

    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0xF:
            return

        original = mask
        index = 0
        for (centre, pt1) in (prop.segment.points, reversed(prop.segment.points)):
            for (pt0, pt2) in (prop.points, reversed(prop.points)):
                index += 1
                bit = 1 << index
                if mask & bit:
                    continue
                prop1 = self.context.two_points_relative_to_line_property(centre.segment(pt0), pt1, pt2)
                if prop1 is None:
                    continue
                mask |= bit
                if prop1.same:
                    continue
                triangle = Scene.Triangle(pt0, pt1, pt2)
                comment = Comment(
                    'line $%{line:line0}$ separates $%{point:pt0}$ and $%{point:pt1}$, line $%{line:line1}$ separates $%{point:pt2}$ and $%{point:pt3}$ => the intersection $%{point:crossing}$ lies inside $%{triangle:triangle}$',
                    {
                        'line0': prop.segment,
                        'pt0': prop.points[0],
                        'pt1': prop.points[1],
                        'line1': prop1.segment,
                        'pt2': prop1.points[0],
                        'pt3': prop1.points[1],
                        'crossing': centre,
                        'triangle': triangle
                    }
                )
                angles = triangle.angles
                for i in range(0, 3):
                    yield (
                        PointInsideAngleProperty(centre, angles[i]),
                        comment,
                        [prop, prop1]
                    )
        if mask != original:
            self.processed[prop] = mask

class TwoPointsRelativeToLineTransitivityRule(Rule):
    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def sources(self):
        for p0 in self.context.list(SameOrOppositeSideProperty):
            for p1 in self.context.list(SameOrOppositeSideProperty, [p0.segment]):
                if p0 != p1:
                    yield (p0, p1)

    def apply(self, src):
        key = frozenset(src)
        if key in self.processed:
            return
        self.processed.add(key)

        sos0, sos1 = src
        if sos0.points[0] in sos1.points:
            common = sos0.points[0]
            other0 = sos0.points[1]
        elif sos0.points[1] in sos1.points:
            common = sos0.points[1]
            other0 = sos0.points[0]
        else:
            return
        other1 = sos1.points[0] if sos1.points[1] == common else sos1.points[1]
        if sos0.same and sos1.same:
            pattern = '$%{point:other0}$, $%{point:common}$, and $%{point:other1}$ lie on the same side of $%{line:line}$'
            pts = (other0, other1)
            premises = [sos0, sos1]
        elif sos0.same:
            pattern = '$%{point:other0}$ and $%{point:common}$ lie on the same side of $%{line:line}$, $%{point:other1}$ is on the opposite side'
            pts = (other0, other1)
            premises = [sos0, sos1]
        elif sos1.same:
            pattern = '$%{point:other1}$ and $%{point:common}$ lie on the same side of $%{line:line}$, $%{point:other0}$ is on the opposite side'
            pts = (other1, other0)
            premises = [sos1, sos0]
        else:
            pattern = '$%{point:other0}$ and $%{point:common}$ lie on opposite sides of $%{line:line}$, and $%{point:common}$ and $%{point:other1}$ too'
            pts = (other0, other1)
            premises = [sos0, sos1]

        yield (
            SameOrOppositeSideProperty(sos0.segment, *pts, sos0.same == sos1.same),
            Comment(
                pattern,
                {'other0': other0, 'other1': other1, 'common': common, 'line': sos0.segment}
            ),
            premises
        )

class CongruentAnglesDegeneracyRule(Rule):
    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def sources(self):
        return self.context.congruent_angles_with_vertex()

    def apply(self, src):
        ca = None
        for key in (src, (src[1], src[0])):
            if key in self.processed:
                continue
            ang0, ang1 = key
            col = self.context.collinearity_property(*ang0.point_set)
            if col is None:
                continue
            self.processed.add(key)
            if ca is None:
                ca = self.context.angle_ratio_property(ang0, ang1)
            if col.collinear:
                pattern = 'angles $%{angle:angle1}$ and $%{angle:angle0}$ are congruent, $%{angle:angle0}$ is degenerate'
            else:
                pattern = 'angles $%{angle:angle1}$ and $%{angle:angle0}$ are congruent, $%{angle:angle0}$ is non-degenerate'
            comment = Comment(pattern, {'angle0': ang0, 'angle1': ang1})
            yield (
                PointsCollinearityProperty(*ang1.point_set, col.collinear),
                comment,
                [ca, col]
            )

class PointAndAngleRule(SingleSourceRule):
    property_type = SameOrOppositeSideProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = {}

    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0x0F:
            return
        original = mask
        for vertex, bit0 in zip(prop.segment.points, (0x1, 0x4)):
            pt0 = other_point(prop.segment.points, vertex)
            for pt1, bit in zip(prop.points, (bit0, bit0 >> 1)):
                if mask & bit:
                    continue
                fourth = other_point(prop.points, pt1)
                prop1 = self.context.two_points_relative_to_line_property(
                    vertex.segment(pt1), pt0, fourth
                )
                if prop1 is None:
                    continue
                mask |= bit
                # TODO: update self.processed[prop1]
                if not prop.same and not prop1.same:
                    continue

                params = {
                    'pt0': pt0,
                    'pt1': pt1,
                    'fourth': fourth,
                    'side0': vertex.vector(pt0),
                    'side1': vertex.vector(pt1)
                }
                if prop.same and prop1.same:
                    yield (
                        PointInsideAngleProperty(fourth, vertex.angle(pt0, pt1)),
                        Comment(
                            '$%{point:fourth}$ lies on the same side of $%{ray:side0}$ as $%{point:pt1}$ and on the same side of $%{ray:side1}$ as $%{point:pt0}$',
                            params
                        ),
                        [prop, prop1]
                    )
                elif prop.same:
                    yield (
                        PointInsideAngleProperty(pt1, vertex.angle(pt0, fourth)),
                        Comment(
                            '$%{point:pt1}$ lies on the same side of $%{ray:side0}$ as $%{point:fourth}$ and $%{ray:side1}$ separates $%{point:pt0}$ and $%{point:fourth}$',
                            params
                        ),
                        [prop, prop1]
                    )
                else:
                    yield (
                        PointInsideAngleProperty(pt0, vertex.angle(fourth, pt1)),
                        Comment(
                            '$%{point:pt0}$ lies on the same side of $%{ray:side1}$ as $%{point:fourth}$ and $%{ray:side0}$ separates $%{point:pt1}$ and $%{point:fourth}$',
                            params
                        ),
                        [prop1, prop]
                    )

        if mask != original:
            self.processed[prop] = mask

class PerpendicularToSideOfObtuseAngledRule(SingleSourceRule):
    property_type = AngleKindProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def accepts(self, prop):
        return prop.angle.vertex and prop.kind == AngleKindProperty.Kind.obtuse

    def apply(self, prop):
        long_side = prop.angle.endpoints[0].segment(prop.angle.endpoints[1])
        for seg in [v.as_segment for v in prop.angle.vectors]:
            for inside in self.context.points_inside_segment(seg):
                key = (prop.angle, inside)
                if key in self.processed:
                    continue
                inside_prop = self.context.angle_value_property(inside.angle(*seg.points))
                for pt in self.context.collinear_points(long_side):
                    perp_line = pt.segment(inside)
                    perp = self.context[PerpendicularSegmentsProperty(seg, perp_line)]
                    if perp is None:
                        continue
                    self.processed.add(key)
                    comment = Comment(
                        '$%{triangle:triangle}$ is obtuse-angled (with the vertex $%{point:vertex}$), $%{point:inside}$ is inside $%{segment:side}$, $%{point:pt} \\in %{line:long}$, and $%{line:perp} \\perp %{line:side}$',
                        {
                            'triangle': Scene.Triangle(*prop.angle.point_set),
                            'vertex': prop.angle.vertex,
                            'inside': inside,
                            'side': seg,
                            'pt': pt,
                            'long': long_side,
                            'perp': perp_line
                        }
                    )
                    for ep in prop.angle.endpoints:
                        yield (
                            PointsCoincidenceProperty(pt, ep, False),
                            comment,
                            [prop, inside_prop, perp]
                        )
                    yield (
                        AngleValueProperty(pt.angle(*prop.angle.endpoints), 180),
                        comment,
                        [prop, inside_prop, perp]
                    )
                    break

class MiddleOfSegmentRule(SingleSourceRule):
    property_type = MiddleOfSegmentProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = {}

    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0xF:
            return
        original = mask

        comment = Comment(
            '$%{point:point}$ is the midpoint of $%{segment:segment}$',
            {'point': prop.point, 'segment': prop.segment}
        )

        triangle = Scene.Triangle(prop.point, *prop.segment.points)
        if (mask & 0x1) == 0:
            # properties not depending on degeneracy
            mask |= 0x1
            new_properties = (
                PointsCollinearityProperty(*triangle.points, True),
                ProportionalLengthsProperty(triangle.sides[0], triangle.sides[1], 2),
                ProportionalLengthsProperty(triangle.sides[0], triangle.sides[2], 2),
                ProportionalLengthsProperty(triangle.sides[1], triangle.sides[2], 1),
            )
            for p in new_properties:
                yield (p, comment, [prop])

        for index, seg in enumerate(triangle.sides):
            bit = 2 << index
            if mask & bit:
                continue
            ne = self.context.coincidence_property(*seg.points)
            if ne is None:
                continue
            mask |= bit
            if ne.coincident:
                mask |= 0xE
                break

            new_properties = [
                AngleValueProperty(triangle.angles[0], 180),
                AngleValueProperty(triangle.angles[1], 0),
                AngleValueProperty(triangle.angles[2], 0),
            ]
            for side in triangle.sides:
                if side != seg:
                    new_properties.append(PointsCoincidenceProperty(*side.points, False))
            for p in new_properties:
                yield (p, comment, [prop, ne])

        if mask != original:
            self.processed[prop] = mask
