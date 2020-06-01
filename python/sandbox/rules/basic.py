import itertools

from ..property import *
from ..scene import Scene
from ..util import LazyComment, divide

from .abstract import Rule, SingleSourceRule

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

        comment = LazyComment('%s is the intersection of ray [%s) and segment [%s]', X, A.vector(D).as_ray, B.segment(C))
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
        oppo = self.context.two_points_relatively_to_line_property(prop.angles[0].vertex.segment(common), pt0, pt1)
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

        if lr0.segment0 == lr1.segment0:
            coef = divide(lr1.value, lr0.value)
            yield (
                ProportionalLengthsProperty(lr0.segment1, lr1.segment1, coef),
                LazyComment('|%s| = %s|%s| = %s|%s|', lr0.segment1, _cs(divide(1, lr0.value)), lr0.segment0, _cs(coef), lr1.segment1),
                [lr0, lr1]
            )
        elif lr0.segment0 == lr1.segment1:
            coef = lr1.value * lr0.value
            yield (
                ProportionalLengthsProperty(lr1.segment0, lr0.segment1, coef),
                LazyComment('|%s| = %s|%s| = %s|%s|', lr1.segment0, _cs(lr1.value), lr0.segment0, _cs(coef), lr0.segment1),
                [lr1, lr0]
            )
        elif lr0.segment1 == lr1.segment0:
            coef = lr1.value * lr0.value
            yield (
                ProportionalLengthsProperty(lr0.segment0, lr1.segment1, coef),
                LazyComment('|%s| = %s|%s| = %s|%s|', lr0.segment0, _cs(lr0.value), lr0.segment1, _cs(coef), lr1.segment1),
                [lr0, lr1]
            )
        elif lr0.segment1 == lr1.segment1:
            coef = divide(lr0.value, lr1.value)
            yield (
                ProportionalLengthsProperty(lr0.segment0, lr1.segment0, coef),
                LazyComment('|%s| = %s|%s| = %s|%s|', lr0.segment0, _cs(lr0.value), lr0.segment1, _cs(coef), lr1.segment0),
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
                    LazyComment('%s and %s belong to two different lines %s and %s', *side.points, pt0.segment(ncl_pt), pt1.segment(ncl_pt)),
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

class NonCollinearPointsAreDifferentRule(SingleSourceRule):
    """
    If three points are collinear, any two of them are not coincident
    """
    property_type = PointsCollinearityProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def accepts(self, prop):
        return not prop.collinear and prop not in self.processed

    def apply(self, prop):
        self.processed.add(prop)
        for pt0, pt1 in itertools.combinations(prop.points, 2):
            yield (
                PointsCoincidenceProperty(pt0, pt1, False),
                LazyComment('two of three non-collinear points %s, %s, and %s', *prop.points),
                [prop]
            )

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
        angle1 = angle0.endpoints[0].angle(angle0.vertex, angle0.endpoints[1])
        angle2 = angle0.endpoints[1].angle(angle0.vertex, angle0.endpoints[0])

        yield (
            SumOfTwoAnglesProperty(angle1, angle2, 180 - prop.degree),
            LazyComment('sum of two angles of %s, the third %s = %s', Scene.Triangle(*angle0.point_set), angle0, prop.degree_str),
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
            LazyComment('three angles of %s', triangle),
            [ne0, ne1, ne2]
        )

class SumOfThreeAnglesOnLineRule(Rule):
    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def sources(self):
        avs = [p for p in self.context.angle_value_properties_for_degree(0) if p.angle.vertex]
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
            LazyComment('%s = %s and %s = %s', av0.angle, av0.degree_str, av1.angle, av1.degree_str),
            [av0, av1]
        )

class SumOfThreeAnglesOnLineRule2(Rule):
    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def sources(self):
        return [p for p in self.context.angle_value_properties_for_degree(180) if p.angle.vertex and p not in self.processed]

    def apply(self, prop):
        self.processed.add(prop)

        for vec0, vec1 in (prop.angle.vectors, reversed(prop.angle.vectors)):
            yield (
                AngleValueProperty(vec0.end.angle(vec0.start, vec1.end), 0),
                LazyComment('%s lies between %s and %s', vec0.start, vec0.end, vec1.end),
                [prop]
            )

class LengthRatioRule(SingleSourceRule):
    property_type = ProportionalLengthsProperty

    def apply(self, prop):
        seg0 = prop.segment0
        seg1 = prop.segment1

        ne0 = self.context.not_equal_property(*seg0.points)
        ne1 = self.context.not_equal_property(*seg1.points)
        if ne0 is not None and ne1 is None:
            if prop.reason.obsolete and ne0.reason.obsolete:
                return
            yield (PointsCoincidenceProperty(*seg1.points, False), LazyComment('Otherwise, %s = %s', *seg0.points), [prop, ne0])
        elif ne1 is not None and ne0 is None:
            if prop.reason.obsolete and ne1.reason.obsolete:
                return
            yield (PointsCoincidenceProperty(*seg0.points, False), LazyComment('Otherwise, %s = %s', *seg1.points), [prop, ne1])
        elif ne0 is None and ne1 is None:
            common = next((pt for pt in seg0.points if pt in seg1.points), None)
            if common is None:
                return
            pt0 = next(pt for pt in seg0.points if pt != common)
            pt1 = next(pt for pt in seg1.points if pt != common)
            ne = self.context.not_equal_property(pt0, pt1)
            if ne is None or prop.reason.obsolete and ne.reason.obsolete:
                return
            yield (PointsCoincidenceProperty(*seg0.points, False), LazyComment('Otherwise, %s = %s = %s', ne.points[0], common, ne.points[1]), [prop, ne])
            yield (PointsCoincidenceProperty(*seg1.points, False), LazyComment('Otherwise, %s = %s = %s', ne.points[1], common, ne.points[0]), [prop, ne])

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
                LazyComment('non-zero parallel vectors %s and %s', vec0, vec1),
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
                LazyComment('non-zero perpendicular segments %s and %s', seg0, seg1),
                [pv, ne0, ne1]
            )

class Degree90ToPerpendicularSegmentsRule(Rule):
    def sources(self):
        return self.context.angle_value_properties_for_degree(90)

    def apply(self, prop):
        if not prop.reason.obsolete:
            yield (
                PerpendicularSegmentsProperty(prop.angle.vectors[0].as_segment, prop.angle.vectors[1].as_segment),
                prop.reason.comment,
                prop.reason.premises
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
                    comment = LazyComment('%s is the same line as %s', seg0.as_line, seg1.as_line)
                else:
                    comment = LazyComment('any line perpendicular to %s is also perpendicular to %s', seg0.as_line, seg1.as_line)
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
        yield (
            PerpendicularSegmentsProperty(common, pt0.segment(pt1)),
            LazyComment('%s and %s are perpendiculars to line %s', seg0, seg1, common.as_line),
            [perp0, perp1, ne]
        )
        yield (
            PointsCollinearityProperty(common_point, pt0, pt1, True),
            LazyComment('%s and %s are perpendiculars to line %s', seg0, seg1, common.as_line),
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
            if cs and not(prop.reason.obsolete and cs.reason.obsolete):
                yield (
                    ProportionalLengthsProperty(*segments[1], 1),
                    LazyComment('%s lies on the perpendicular bisector to %s', seg0.points[1], seg1),
                    [prop, cs]
                )
            cs = self.context.congruent_segments_property(*segments[1], True)
            if cs and not(prop.reason.obsolete and cs.reason.obsolete):
                yield (
                    ProportionalLengthsProperty(*segments[0], 1),
                    LazyComment('%s lies on the perpendicular bisector to %s', seg0.points[0], seg1),
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
                LazyComment('%s and %s are both equidistant from %s and %s', common0, common1, *pts0),
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
            LazyComment('perpendicular bisector %s separates endpoints of the segment %s', segment0.as_line, segment1),
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
            yield (
                AngleValueProperty(p0.angle(*prop.points), 0),
                LazyComment(
                    '%s = %s, and points %s and %s are on the same side of %s',
                    *angles, *prop.points, prop.segment.as_line
                ),
                [ca, prop]
            )
            yield (
                PointsCollinearityProperty(p0, *prop.points, True),
                LazyComment(
                    '%s = %s, and points %s and %s are on the same side of %s',
                    *angles, *prop.points, prop.segment.as_line
                ),
                [ca, prop]
            )

        if mask != original:
            self.processed[prop] = mask

class PointsSeparatedByLineAreNotCoincidentRule(SingleSourceRule):
    """
    If two points are separated by a line, the points are not coincident
    """
    property_type = SameOrOppositeSideProperty

    def accepts(self, prop):
        return not prop.same

    def apply(self, prop):
        if not prop.reason.obsolete:
            yield (
                PointsCoincidenceProperty(prop.points[0], prop.points[1], False),
                LazyComment('the points are separated by line %s', prop.segment.as_line),
                [prop]
            )

class SameSidePointInsideSegmentRule(SingleSourceRule):
    """
    If endpoints of a segment are on the same side of a line,
    then any point inside the segment in on the same side too
    """
    property_type = SameOrOppositeSideProperty

    def accepts(self, prop):
        return prop.same

    def apply(self, prop):
        segment = prop.points[0].segment(prop.points[1])
        for pt in self.context.collinear_points(segment):
            value = self.context.angle_value_property(pt.angle(*prop.points))
            if not value or value.degree != 180 or prop.reason.obsolete and value.reason.obsolete:
                return
            for endpoint in prop.points:
                yield (
                    SameOrOppositeSideProperty(prop.segment, endpoint, pt, True),
                    LazyComment('Segment %s does not cross line %s', segment, prop.segment),
                    [prop, value]
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
            LazyComment('Two perpendiculars to line %s', prop.segment),
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
            LazyComment('%s ⟂ %s ⟂ %s', other0, common, other1),
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
                LazyComment('%s and %s lie on a line parallel to %s', *seg1.points, seg0),
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
            LazyComment('%s is %s rotated by %s = %s', new_angle0, new_angle1, ang0, ang1),
            [ca, co]
        )

class PartOfAcuteAngleIsAcuteRule(SingleSourceRule):
    property_type = PointInsideAngleProperty

    def apply(self, prop):
        kind = self.context.angle_kind_property(prop.angle)
        if kind is None or kind.kind == AngleKindProperty.Kind.obtuse or prop.reason.obsolete and kind.reason.obsolete:
            return
        for vec in prop.angle.vectors:
            angle = prop.angle.vertex.angle(vec.end, prop.point)
            yield (
                AngleKindProperty(angle, AngleKindProperty.Kind.acute),
                LazyComment('%s is a part of %s %s', angle, kind.kind, prop.angle),
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
        if prop.degree < 90:
            yield (
                AngleKindProperty(prop.angle, AngleKindProperty.Kind.acute),
                LazyComment('0º < %s = %s < 90º', prop.angle, prop.degree_str),
                [prop]
            )
        elif prop.degree > 90:
            yield (
                AngleKindProperty(prop.angle, AngleKindProperty.Kind.obtuse),
                LazyComment('90º < %s = %s < 180º', prop.angle, prop.degree_str),
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
            LazyComment('%s', prop),
            [prop]
        )

class RightAngleDegreeRule(SingleSourceRule):
    property_type = AngleKindProperty

    def accepts(self, prop):
        return prop.kind == AngleKindProperty.Kind.right

    def apply(self, prop):
        if prop.reason.obsolete:
            return
        yield (
            AngleValueProperty(prop.angle, 90),
            prop.reason.comment,
            prop.reason.premises
        )

class AngleTypesInObtuseangledTriangleRule(SingleSourceRule):
    property_type = AngleKindProperty

    def accepts(self, prop):
        return prop.angle.vertex and prop.kind != AngleKindProperty.Kind.acute

    def apply(self, prop):
        if prop.reason.obsolete:
            return
        ang = prop.angle
        yield (
            AngleKindProperty(ang.vectors[0].end.angle(ang.vertex, ang.vectors[1].end), AngleKindProperty.Kind.acute),
            LazyComment('An angle of %s, another angle is %s', Scene.Triangle(*ang.point_set), prop.kind),
            [prop]
        )
        yield (
            AngleKindProperty(ang.vectors[1].end.angle(ang.vertex, ang.vectors[0].end), AngleKindProperty.Kind.acute),
            LazyComment('An angle of %s, another angle is %s', Scene.Triangle(*ang.point_set), prop.kind),
            [prop]
        )

class VerticalAnglesRule(Rule):
    def sources(self):
        return itertools.combinations([av for av in self.context.angle_value_properties_for_degree(180) if av.angle.vertex], 2)

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
        new_prop = AngleRatioProperty(
            ng0.vertex.angle(ng0.vectors[0].end, ng1.vectors[0].end),
            ng0.vertex.angle(ng0.vectors[1].end, ng1.vectors[1].end),
            1
        )
        yield (
            new_prop,
            LazyComment('%s and %s are vertical angles', new_prop.angle0, new_prop.angle1),
            [av0, av1]
        )
        new_prop = AngleRatioProperty(
            ng0.vertex.angle(ng0.vectors[0].end, ng1.vectors[1].end),
            ng0.vertex.angle(ng0.vectors[1].end, ng1.vectors[0].end),
            1
        )
        yield (
            new_prop,
            LazyComment('%s and %s are vertical angles', new_prop.angle0, new_prop.angle1),
            [av0, av1]
        )

class ReversedVerticalAnglesRule(Rule):
    def __init__(self, context):
        super().__init__(context)
        self.processed = {} # pair (prop, oppo) => mask

    def sources(self):
        return [p for p in self.context.angle_value_properties_for_degree(180) if p.angle.vertex]

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
                    LazyComment('%s = %s and %s lies on segment %s', ang0, ang1, angle.vertex, angle.vectors[0].end.segment(angle.vectors[1].end)),
                    [ar, prop, oppo]
                )
            if mask != original:
                self.processed[key] = mask

class CorrespondingAndAlternateAnglesRule(SingleSourceRule):
    property_type = SameOrOppositeSideProperty

    def apply(self, prop):
        lp0 = prop.segment.points[0]
        lp1 = prop.segment.points[1]
        for pt0, pt1 in [prop.points, reversed(prop.points)]:
            angle0 = lp0.angle(pt0, lp1)
            angle1 = lp1.angle(pt1, lp0)
            if prop.same:
                try:
                    sum_reason = self.context[SumOfTwoAnglesProperty(angle0, angle1, 180)]
                except: #TODO: check contradiction with no try/except
                    continue
                ratio_reason = None
                if sum_reason is None:
                    for cnd in [p for p in self.context.list(SumOfTwoAnglesProperty, [angle0]) if p.degree == 180]:
                        other = cnd.angles[0] if cnd.angles[1] == angle0 else cnd.angles[1]
                        ratio_reason = self.context.angle_ratio_property(other, angle1)
                        if ratio_reason:
                            if ratio_reason.value == 1:
                                sum_reason = cnd
                            break
                if sum_reason is None:
                    for cnd in [p for p in self.context.list(SumOfTwoAnglesProperty, [angle1]) if p.degree == 180]:
                        other = cnd.angles[0] if cnd.angles[1] == angle1 else cnd.angles[1]
                        ratio_reason = self.context.angle_ratio_property(other, angle0)
                        if ratio_reason:
                            if ratio_reason.value == 1:
                                sum_reason = cnd
                            break
                if sum_reason is None:
                    continue
                reasons = [prop, sum_reason]
                if ratio_reason:
                    reasons.append(ratio_reason)
                if all(p.reason.obsolete for p in reasons):
                    continue
                for p in AngleValueProperty.generate(lp0.vector(pt0), lp1.vector(pt1), 0):
                    yield (
                        p,
                        LazyComment('sum of consecutive angles: %s + %s = 180º', angle0, angle1),
                        reasons
                    )
            else:
                ratio_reason = self.context.angle_ratio_property(angle0, angle1)
                if ratio_reason is None or prop.reason.obsolete and ratio_reason.reason.obsolete:
                    continue
                if ratio_reason.value == 1:
                    for p in AngleValueProperty.generate(lp0.vector(pt0), pt1.vector(lp1), 0):
                        yield (
                            p,
                            LazyComment('alternate angles %s and %s are equal', angle0, angle1),
                            [prop, ratio_reason]
                        )

class CyclicOrderRule(SingleSourceRule):
    property_type = SameOrOppositeSideProperty

    def apply(self, prop):
        if prop.reason.obsolete:
            return
        cycle0 = Cycle(*prop.segment.points, prop.points[0])
        cycle1 = Cycle(*prop.segment.points, prop.points[1])
        if not prop.same:
            cycle1 = cycle1.reversed
        yield (
            SameCyclicOrderProperty(cycle0, cycle1),
            '', #TODO: write comment
            [prop]
        )

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
                        comment = LazyComment('supplementary angles: common side %s, and %s ↑↓ %s', vec.as_ray, vec0.as_ray, vec1.as_ray)
                    else:
                        comment = LazyComment('consecutive angles: common line %s, and %s ↑↑ %s', vec.as_line, vec0.as_ray, vec1.as_ray)
                else:
                    if common0 == common1:
                        new_prop = AngleRatioProperty(ngl0, ngl1, 1, same=True)
                        comment = LazyComment('same angle: common ray %s, and %s coincides with %s', vec.as_ray, vec0.as_ray, vec1.as_ray)
                    else:
                        new_prop = AngleRatioProperty(ngl0, ngl1, 1)
                        comment = LazyComment('alternate angles: common line %s, and %s ↑↓ %s', vec.as_line, vec0.as_ray, vec1.as_ray)
                yield (new_prop, comment, [prop, ne])

class SameAngleRule(Rule):
    def sources(self):
        return itertools.combinations([av for av in self.context.list(AngleValueProperty) if av.angle.vertex and av.degree == 0], 2)

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
        yield (
            AngleRatioProperty(
                ng0.vertex.angle(ng0.vectors[0].end, ng1.vectors[0].end),
                ng0.vertex.angle(ng0.vectors[1].end, ng1.vectors[1].end),
                1,
                same=True
            ),
            LazyComment('%s ↑↑ %s and %s ↑↑ %s', *ng0.vectors, *ng1.vectors),
            [av0, av1]
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
            yield (
                AngleValueProperty(crossing.angle(pt0, pt1), 0),
                LazyComment('%s is the intersection point of lines %s and %s', crossing, pt0.segment(pt1), prop.segment),
                [prop] + reasons
            )
        else:
            yield (
                AngleValueProperty(crossing.angle(pt0, pt1), 180),
                LazyComment('%s is the intersection point of segment %s and line %s', crossing, pt0.segment(pt1), prop.segment.as_line),
                [prop] + reasons
            )

class CeviansIntersectionRule(Rule):
    def sources(self):
        return itertools.combinations([av for av in self.context.angle_value_properties_for_degree(180) if av.angle.vertex], 2)

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
        comment = LazyComment('%s is the intersection of cevians %s and %s with %s and %s inside the sides of %s', crossing, segment0, segment1, av1.angle.vertex, av0.angle.vertex, Scene.Triangle(vertex, pt0, pt1))
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
            LazyComment('%s + %s = %s = %s', angle0, angle1, prop.angle, av.degree_str),
            [prop, av]
        )

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
                prop1 = self.context.two_points_relatively_to_line_property(centre.segment(pt0), pt1, pt2)
                if prop1 is None:
                    continue
                mask |= bit
                if prop1.same:
                    continue
                triangle = Scene.Triangle(pt0, pt1, pt2)
                comment = LazyComment('Line %s separates %s and %s, line %s separates %s and %s => the intersection %s lies inside %s', prop.segment.as_line, *prop.points, prop1.segment.as_line, *prop1.points, centre, triangle)
                angles = triangle.angles
                for i in range(0, 3):
                    yield (
                        PointInsideAngleProperty(centre, angles[i]),
                        comment,
                        [prop, prop1]
                    )
        if mask != original:
            self.processed[prop] = mask

class TwoPointsRelativelyToLineTransitivityRule(Rule):
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
            comment = LazyComment(
                '%s, %s, and %s lies on the same side of %s',
                other0, common, other1, sos0.segment.as_line
            )
            pts = (other0, other1)
            premises = [sos0, sos1]
        elif sos0.same:
            comment = LazyComment(
                '%s, %s lies on the same side of %s, %s is on the opposite side',
                other0, common, sos0.segment.as_line, other1
            )
            pts = (other0, other1)
            premises = [sos0, sos1]
        elif sos1.same:
            comment = LazyComment(
                '%s, %s lies on the same side of %s, %s is on the opposite side',
                other1, common, sos0.segment.as_line, other0
            )
            pts = (other1, other0)
            premises = [sos1, sos0]
        else:
            comment = LazyComment(
                '%s, %s lies on opposite sides of %s, and %s, %s too',
                other0, common, sos0.segment.as_line, common, other1
            )
            pts = (other0, other1)
            premises = [sos0, sos1]

        yield (
            SameOrOppositeSideProperty(sos0.segment, *pts, sos0.same == sos1.same),
            comment,
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
                comment = LazyComment(
                    'angles %s and %s are congruent, %s is degenerate', ang1, ang0, ang0
                )
            else:
                comment = LazyComment(
                    'angles %s and %s are congruent, %s is non-degenerate', ang1, ang0, ang0
                )
            yield (
                PointsCollinearityProperty(*ang1.point_set, col.collinear),
                comment,
                [ca, col]
            )
