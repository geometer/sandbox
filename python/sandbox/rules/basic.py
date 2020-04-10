import itertools

from sandbox.property import *
from sandbox.util import _comment, divide, side_of

from .abstract import Rule, SingleSourceRule

class DifferentAnglesToDifferentPointsRule(Rule):
    """
    For three vectors, v0, v1, v2, if it is known that
        v1 and v2 have common start (or end), and
        ∠(v0, v1) != ∠(v0, v2),
    then ends (starts) of v1 and v2 are different
    """
    def sources(self):
        return itertools.combinations(self.context.angle_value_properties(), 2)

    def apply(self, src):
        av0, av1 = src

        if av0.degree == av1.degree or av0.reason.obsolete and av1.reason.obsolete:
            return
        ang0 = av0.angle
        ang1 = av1.angle

        if ang0.vector0 == ang1.vector0:
            vec0, vec1 = ang0.vector1, ang1.vector1
        elif ang0.vector0 == ang1.vector1:
            vec0, vec1 = ang0.vector1, ang1.vector0
        elif ang0.vector1 == ang1.vector0:
            vec0, vec1 = ang0.vector0, ang1.vector1
        elif ang0.vector1 == ang1.vector1:
            vec0, vec1 = ang0.vector0, ang1.vector0
        elif ang0.vector0 == ang1.vector0.reversed:
            vec0, vec1 = ang0.vector1, ang1.vector1.reversed
        elif ang0.vector0 == ang1.vector1.reversed:
            vec0, vec1 = ang0.vector1, ang1.vector0.reversed
        elif ang0.vector1 == ang1.vector0.reversed:
            vec0, vec1 = ang0.vector0, ang1.vector1.reversed
        elif ang0.vector1 == ang1.vector1.reversed:
            vec0, vec1 = ang0.vector0, ang1.vector0.reversed
        else:
            return

        if vec0.start == vec1.start:
            prop = PointsCoincidenceProperty(vec0.end, vec1.end, False)
        elif vec0.end == vec1.end:
            prop = PointsCoincidenceProperty(vec0.start, vec1.start, False)
        else:
            return

        yield (prop, _comment('Otherwise, %s = %s', ang0, ang1), [av0, av1])

class LengthRatioSimplificationRule(Rule):
    def sources(self):
        return self.context.length_ratio_properties()

    def apply(self, prop):
        if not prop.reason.obsolete:
            yield (
                LengthRatioProperty(prop.segment0, prop.segment1, prop.value),
                prop.reason.comments,
                prop.reason.premises
            )

class LengthRatioTransitivityRule(Rule):
    """
    For three segments seg0, seg1, and seg2, from
        |seg0| = A |seg1|, and
        |seg1| = B |seg2|
    we conclude that |seg0| = A B |seg2|
    """
    def sources(self):
        return itertools.combinations(self.context.list(LengthRatioProperty), 2)

    def apply(self, src):
        lr0, lr1 = src

        if lr0.reason.obsolete and lr1.reason.obsolete:
            return

        def _cs(coef):
            return '' if coef == 1 else ('%s ' % coef)

        if lr0.segment0 == lr1.segment0:
            coef = divide(lr1.value, lr0.value)
            yield (
                LengthRatioProperty(lr0.segment1, lr1.segment1, coef),
                _comment('|%s| = %s|%s| = %s|%s|', lr0.segment1, _cs(divide(1, lr0.value)), lr0.segment0, _cs(coef), lr1.segment1),
                [lr0, lr1]
            )
        elif lr0.segment0 == lr1.segment1:
            coef = lr1.value * lr0.value
            yield (
                LengthRatioProperty(lr1.segment0, lr0.segment1, coef),
                _comment('|%s| = %s|%s| = %s|%s|', lr1.segment0, _cs(lr1.value), lr0.segment0, _cs(coef), lr0.segment1),
                [lr1, lr0]
            )
        elif lr0.segment1 == lr1.segment0:
            coef = lr1.value * lr0.value
            yield (
                LengthRatioProperty(lr0.segment0, lr1.segment1, coef),
                _comment('|%s| = %s|%s| = %s|%s|', lr0.segment0, _cs(lr0.value), lr0.segment1, _cs(coef), lr1.segment1),
                [lr0, lr1]
            )
        elif lr0.segment1 == lr1.segment1:
            coef = divide(lr0.value, lr1.value)
            yield (
                LengthRatioProperty(lr0.segment0, lr1.segment0, coef),
                _comment('|%s| = %s|%s| = %s|%s|', lr0.segment0, _cs(lr0.value), lr0.segment1, _cs(coef), lr1.segment0),
                [lr0, lr1]
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
        for side, pt0 in [(side_of(cl0.points, i), cl0.points[i]) for i in range(0, 3)]:
            third_points = [pt0]
            for cl1 in [p for p in self.context.list(PointsCollinearityProperty, [side]) if p.collinear and p != cl0]:
                pt1 = next(pt for pt in cl1.points if pt not in side.points)
                third_points.append(pt1)

                for ncl_pt in side.points:
                    ncl = self.context.collinearity_property(pt0, pt1, ncl_pt)
                    if ncl:
                        break
                else:
                    continue
                if ncl.collinear or cl0.reason.obsolete and cl1.reason.obsolete and ncl.reason.obsolete:
                    continue
                yield (
                    PointsCoincidenceProperty(*side.points, True),
                    _comment('%s and %s belong to two different lines %s and %s', *side.points, pt0.segment(ncl_pt), pt1.segment(ncl_pt)),
                    [cl0, cl1, ncl]
                )
                break
            else:
                for triple in itertools.combinations(third_points, 3):
                    ncl = self.context.collinearity_property(*triple)
                    if ncl and not ncl.collinear:
                        lines = [pt.segment(side.points[0]) for pt in triple]
                        yield (
                            PointsCoincidenceProperty(*side.points, True),
                            _comment('%s and %s belong to three lines %s, %s, and %s, at least two of them are different', *side.points, *lines),
                            [cl0, cl1, ncl]
                        )
                        break

class CollinearityCollisionRule(Rule):
    """
    If a point belongs to some line, and another one does not,
    then the points are different.
    Moreover, if a third point belongs to the line and does not coincide to the first,
    then the three points are not collinear.
    """
    def sources(self):
        return itertools.product( \
            [p for p in self.context.list(PointsCollinearityProperty) if not p.collinear], \
            [p for p in self.context.list(PointsCollinearityProperty) if p.collinear] \
        )

    def apply(self, src):
        ncl, col = src

        common_points = [pt for pt in ncl.points if pt in col.points]
        if len(common_points) != 2:
            return
        pt_ncl = next(pt for pt in ncl.points if pt not in common_points)
        pt_col = next(pt for pt in col.points if pt not in common_points)

        reasons_are_too_old = ncl.reason.obsolete and col.reason.obsolete
        if not reasons_are_too_old:
            yield (
                PointsCoincidenceProperty(pt_col, pt_ncl, False),
                _comment('%s lies on the line %s %s, %s does not', pt_col, *common_points, pt_ncl),
                [ncl, col]
            )
        for common in common_points:
            ne = self.context.not_equal_property(common, pt_col)
            if ne is not None and not (reasons_are_too_old and ne.reason.obsolete):
                yield (
                    PointsCollinearityProperty(common, pt_col, pt_ncl, False),
                    _comment(
                        '%s and %s lie on the line %s %s, %s does not',
                        common, pt_col, *common_points, pt_ncl
                    ),
                    [ncl, col, ne]
                )

class NonCollinearPointsAreDifferentRule(SingleSourceRule):
    """
    If three points are collinear, any two of them are not coincident
    """
    property_type = PointsCollinearityProperty

    def accepts(self, prop):
        return not prop.collinear

    def apply(self, prop):
        if prop.reason.obsolete:
            return
        for pt0, pt1 in itertools.combinations(prop.points, 2):
            yield (
                PointsCoincidenceProperty(pt0, pt1, False),
                'Two of three non-collinear points',
                [prop]
            )

class SumAndRatioOfTwoAnglesRule(SingleSourceRule):
    """
    If the sum and the ratio of two angles are known, we can find the values
    """
    property_type = SumOfAnglesProperty

    def apply(self, prop):
        if self.context.angle_value_property(prop.angle0) or self.context.angle_value_property(prop.angle1):
            return
        ar = self.context.angles_ratio_property(prop.angle0, prop.angle1)
        if ar is None or prop.reason.obsolete and ar.reason.obsolete:
            return
        value1 = divide(prop.degree, 1 + ar.value)
        value0 = prop.degree - value1
        if ar.value == 1:
            comment0 = _comment('%s + %s = %s + %s = %sº', ar.angle0, ar.angle0, ar.angle0, ar.angle1, prop.degree)
            comment1 = _comment('%s + %s = %s + %s = %sº', ar.angle1, ar.angle1, ar.angle1, ar.angle0, prop.degree)
        else:
            comment0 = _comment('%s + %s / %s = %s + %s = %sº', ar.angle0, ar.angle0, ar.value, ar.angle0, ar.angle1, prop.degree)
            comment1 = _comment('%s + %s %s = %s + %s = %sº', ar.angle1, ar.value, ar.angle1, ar.angle1, ar.angle0, prop.degree)
        yield (AngleValueProperty(ar.angle0, value0), comment0, [prop, ar])
        yield (AngleValueProperty(ar.angle1, value1), comment1, [prop, ar])

class LengthRatioRule(SingleSourceRule):
    property_type = LengthRatioProperty

    def apply(self, prop):
        seg0 = prop.segment0
        seg1 = prop.segment1

        ne0 = self.context.not_equal_property(*seg0.points)
        ne1 = self.context.not_equal_property(*seg1.points)
        if ne0 is not None and ne1 is None:
            if prop.reason.obsolete and ne0.reason.obsolete:
                return
            yield (PointsCoincidenceProperty(*seg1.points, False), _comment('Otherwise, %s = %s', *seg0.points), [prop, ne0])
        elif ne1 is not None and ne0 is None:
            if prop.reason.obsolete and ne1.reason.obsolete:
                return
            yield (PointsCoincidenceProperty(*seg0.points, False), _comment('Otherwise, %s = %s', *seg1.points), [prop, ne1])
        elif ne0 is None and ne1 is None:
            common = next((pt for pt in seg0.points if pt in seg1.points), None)
            if common is None:
                return
            pt0 = next(pt for pt in seg0.points if pt != common)
            pt1 = next(pt for pt in seg1.points if pt != common)
            ne = self.context.not_equal_property(pt0, pt1)
            if ne is None or prop.reason.obsolete and ne.reason.obsolete:
                return
            yield (PointsCoincidenceProperty(*seg0.points, False), _comment('Otherwise, %s = %s = %s', ne.points[0], common, ne.points[1]), [prop, ne])
            yield (PointsCoincidenceProperty(*seg1.points, False), _comment('Otherwise, %s = %s = %s', ne.points[1], common, ne.points[0]), [prop, ne])

class ParallelVectorsRule(SingleSourceRule):
    property_type = ParallelVectorsProperty

    def apply(self, para):
        vec0 = para.vector0
        vec1 = para.vector1
        ne0 = self.context.not_equal_property(*vec0.points)
        ne1 = self.context.not_equal_property(*vec1.points)
        if ne0 is None or ne1 is None:
            return
        if para.reason.obsolete and ne0.reason.obsolete and ne1.reason.obsolete:
            return
        for prop in AngleValueProperty.generate(vec0, vec1, 0):
            yield (
                prop,
                _comment('Non-zero parallel vectors %s and %s', vec0, vec1),
                [para, ne0, ne1]
            )

class PerpendicularSegmentsRule(SingleSourceRule):
    property_type = PerpendicularSegmentsProperty

    def apply(self, pv):
        seg0 = pv.segment0
        seg1 = pv.segment1
        ne0 = self.context.not_equal_property(*seg0.points)
        ne1 = self.context.not_equal_property(*seg1.points)
        if ne0 is None or ne1 is None:
            return
        if pv.reason.obsolete and ne0.reason.obsolete and ne1.reason.obsolete:
            return
        vec0 = seg0.points[0].vector(seg0.points[1])
        vec1 = seg1.points[0].vector(seg1.points[1])
        for prop in AngleValueProperty.generate(vec0, vec1, 90):
            yield (
                prop,
                _comment('Non-zero perpendicular segments %s and %s', seg0, seg1),
                [pv, ne0, ne1]
            )

class Degree90ToPerpendicularSegmentsRule(Rule):
    def sources(self):
        return [p for p in self.context.nondegenerate_angle_value_properties() if p.degree == 90]

    def apply(self, prop):
        if not prop.reason.obsolete:
            yield (
                PerpendicularSegmentsProperty(prop.angle.vector0.as_segment, prop.angle.vector1.as_segment),
                prop.reason.comments,
                prop.reason.premises
            )

class CommonPerpendicularRule(SingleSourceRule):
    property_type = AngleValueProperty

    def accepts(self, prop):
        return prop.degree == 0

    def apply(self, prop):
        segments = (prop.angle.vector0.as_segment, prop.angle.vector1.as_segment)
        for seg0, seg1 in (segments, reversed(segments)):
            for perp in self.context.list(PerpendicularSegmentsProperty, [seg0]):
                if prop.reason.obsolete and perp.reason.obsolete:
                    continue
                other = perp.segment1 if seg0 == perp.segment0 else perp.segment0
                yield (
                    PerpendicularSegmentsProperty(seg1, other),
                    _comment('Any line perpendicular to %s is also perpendicular to %s', seg0, seg1),
                    [perp, prop]
                )

class TwoPointsBelongsToTwoPerpendicularsRule(Rule):
    def sources(self):
        return itertools.combinations(self.context.list(PerpendicularSegmentsProperty), 2)

    def apply(self, src):
        perp0, perp1 = src
        segments0 = (perp0.segment0, perp0.segment1)
        segments1 = (perp1.segment0, perp1.segment1)
        common = next((seg for seg in segments0 if seg in segments1), None)
        if common is None:
            return
        seg0 = next(seg for seg in segments0 if seg != common)
        seg1 = next(seg for seg in segments1 if seg != common)
        points = set(seg0.points + seg1.points)
        if len(points) != 3:
            return
        ncl = self.context.collinearity_property(*points)
        if ncl is None or ncl.collinear or ncl.reason.obsolete and perp0.reason.obsolete and perp1.reason.obsolete:
            return
        yield (
            PointsCoincidenceProperty(*common.points, True),
            _comment('%s and %s lies on perpendiculars to non-parallel lines %s and %s', *common.points, seg0, seg1),
            [perp0, perp1, ncl]
        )

class PerpendicularTransitivityRule(Rule):
    def sources(self):
        return itertools.combinations(self.context.list(PerpendicularSegmentsProperty), 2)

    def apply(self, src):
        perp0, perp1 = src
        segments0 = (perp0.segment0, perp0.segment1)
        segments1 = (perp1.segment0, perp1.segment1)
        common = next((seg for seg in segments0 if seg in segments1), None)
        if common is None:
            return
        seg0 = next(seg for seg in segments0 if seg != common)
        seg1 = next(seg for seg in segments1 if seg != common)
        common_point = next((pt for pt in seg0.points if pt in seg1.points), None)
        if common_point is None:
            return
        ne = self.context.not_equal_property(*common.points)
        if ne is None or ne.reason.obsolete and perp0.reason.obsolete and perp1.reason.obsolete:
            return
        pt0 = next(pt for pt in seg0.points if pt != common_point)
        pt1 = next(pt for pt in seg1.points if pt != common_point)
        yield (
            PerpendicularSegmentsProperty(common, pt0.segment(pt1)),
            _comment('%s and %s are perpendicular to non-zero %s', seg0, seg1, common),
            [perp0, perp1, ne]
        )

class SinglePerpendicularBisectorRule(SingleSourceRule):
    property_type = PerpendicularSegmentsProperty

    def apply(self, prop):
        if len({*prop.segment0.points, *prop.segment1.points}) != 4:
            return
        segments = (prop.segment0, prop.segment1)
        for seg0, seg1 in (segments, reversed(segments)):
            for i, j in ((0, 1), (1, 0)):
                ppb = self.context[PointOnPerpendicularBisectorProperty(seg0.points[i], seg1)]
                if ppb:
                    if not (prop.reason.obsolete and ppb.reason.obsolete):
                        yield (
                            PointOnPerpendicularBisectorProperty(seg0.points[j], seg1),
                            _comment('%s lies on the same perpendicular to %s as %s', seg0.points[j], seg1, seg0.points[i]),
                            [prop, ppb]
                        )
                    break

class PointOnPerpendicularBisectorIsEquidistantRule(SingleSourceRule):
    """
    A point on the perpendicular bisector of a segment,
    is equidistant from the endpoints of the segment endpoints
    """
    property_type = PointOnPerpendicularBisectorProperty

    def apply(self, prop):
        if not prop.reason.obsolete:
            yield (
                LengthRatioProperty(prop.point.segment(prop.segment.points[0]), prop.point.segment(prop.segment.points[1]), 1),
                _comment('A point on the perpendicular bisector to %s is equidistant from %s and %s', prop.segment, *prop.segment.points),
                [prop]
            )

class SeparatedPointsRule(SingleSourceRule):
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
                _comment('%s and %s are separated by line %s', prop.points[0], prop.points[1], prop.segment),
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
        for col in [p for p in self.context.list(PointsCollinearityProperty, [segment]) if p.collinear]:
            pt = next(p for p in col.points if p not in prop.points)
            value = self.context.angle_value_property(pt.angle(*prop.points))
            if not value or value.degree != 180 or prop.reason.obsolete and value.reason.obsolete:
                return
            for endpoint in prop.points:
                yield (
                    SameOrOppositeSideProperty(prop.segment, endpoint, pt, True),
                    _comment('Segment %s does not cross line %s', segment, prop.segment),
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
            _comment('Two perpendiculars to line %s', prop.segment),
            premises
        )

class SideProductsInSimilarTrianglesRule(SingleSourceRule):
    property_type = SimilarTrianglesProperty

    def apply(self, prop):
        for i, j in itertools.combinations(range(0, 3), 2):
            yield (
                EqualLengthProductsProperty(
                    side_of(prop.ABC, i), side_of(prop.ABC, j),
                    side_of(prop.DEF, i), side_of(prop.DEF, j)
                ),
                'Relation of sides in similar triangles',
                [prop]
            )

class LengthProductEqualityToRatioRule(SingleSourceRule):
    property_type = EqualLengthProductsProperty

    def apply(self, prop):
        ne = [self.context.not_equal_property(*seg.points) for seg in prop.segments]
        for (i, j, k, l) in [(0, 1, 2, 3), (0, 2, 1, 3), (3, 1, 2, 0), (3, 2, 1, 0)]:
            if ne[j] and ne[l] and not (prop.reason.obsolete and ne[j].reason.obsolete and ne[l].reason.obsolete):
                if prop.segments[j] == prop.segments[l]:
                    yield (
                        LengthRatioProperty(prop.segments[i], prop.segments[k], 1),
                        prop.reason.comments,
                        prop.reason.premises + [ne[j], ne[l]]
                    )
                elif prop.segments[i] == prop.segments[j]:
                    yield (
                        LengthRatioProperty(prop.segments[k], prop.segments[l], 1),
                        prop.reason.comments,
                        prop.reason.premises + [ne[j]]
                    )
                elif prop.segments[k] == prop.segments[l]:
                    yield (
                        LengthRatioProperty(prop.segments[i], prop.segments[j], 1),
                        prop.reason.comments,
                        prop.reason.premises + [ne[l]]
                    )
                else:
                    yield (
                        EqualLengthRatiosProperty(*[prop.segments[x] for x in (i, j, k, l)]),
                        prop.reason.comments,
                        prop.reason.premises + [ne[j], ne[l]]
                    )

class SimilarTrianglesByTwoAnglesRule(Rule):
    def sources(self):
        groups = {}
        for prop in self.context.congruent_angle_properties():
            if not prop.angle0.vertex or not prop.angle1.vertex:
                continue
            key = frozenset([frozenset(prop.angle0.points), frozenset(prop.angle1.points)])
            lst = groups.get(key)
            if lst:
                lst.append(prop)
            else:
                groups[key] = [prop]

        for group in groups.values():
            for ca0, ca1 in itertools.combinations(group, 2):
                if ca1.angle0 in ca0.angle_set or ca1.angle1 in ca0.angle_set:
                    continue
                yield (ca0, ca1)

    def apply(self, src):
        ca0, ca1 = src

        ncl = self.context.not_collinear_property(*ca0.angle0.points)
        first_non_degenerate = True
        if ncl is None:
            ncl = self.context.not_collinear_property(*ca1.angle1.points)
            first_non_degenerate = False
        if ncl is None or ca0.reason.obsolete and ca1.reason.obsolete and ncl.reason.obsolete:
            return

        #this code ensures that vertices are listed in corresponding orders
        if ca0.angle0.points == ca1.angle0.points:
            tr0 = [ca0.angle0.vertex, ca1.angle0.vertex]
            tr1 = [ca0.angle1.vertex, ca1.angle1.vertex]
        else:
            tr0 = [ca0.angle0.vertex, ca1.angle1.vertex]
            tr1 = [ca0.angle1.vertex, ca1.angle0.vertex]
        tr0.append(next(p for p in ca0.angle0.points if p not in tr0))
        tr1.append(next(p for p in ca0.angle1.points if p not in tr1))

        yield (
            SimilarTrianglesProperty(tr0, tr1),
            _comment('Two pairs of congruent angles, and △ %s %s %s is non-degenerate', *(tr0 if first_non_degenerate else tr1)),
            [ca0, ca1, ncl]
        )

class SimilarRightangledTrianglesByCommonAngleRule(Rule):
    def sources(self):
        return itertools.combinations(self.context.list(PerpendicularSegmentsProperty), 2)

    def apply(self, src):
        perp0, perp1 = src

        vertex0 = next((pt for pt in perp0.segment0.points if pt in perp0.segment1.points), None)
        if vertex0 is None:
            return
        vertex1 = next((pt for pt in perp1.segment0.points if pt in perp1.segment1.points), None)
        if vertex1 is None:
            return
        pt00 = next(pt for pt in perp0.segment0.points if pt != vertex0)
        pt01 = next(pt for pt in perp0.segment1.points if pt != vertex0)
        pt10 = next(pt for pt in perp1.segment0.points if pt != vertex1)
        pt11 = next(pt for pt in perp1.segment1.points if pt != vertex1)

        if pt00 == pt10:
            col0 = self.context.collinearity_property(pt00, vertex0, pt11)
            if col0 is None or not col0.collinear:
                return
            col1 = self.context.collinearity_property(pt00, vertex1, pt01)
            if col1 is None or not col1.collinear:
                return
            if perp0.reason.obsolete and perp1.reason.obsolete and col0.reason.obsolete and col1.reason.obsolete:
                return
            vec0 = pt01.vector(vertex0)
            vec1 = pt11.vector(vertex1)
            line0 = pt00.vector(pt01)
            line1 = pt00.vector(pt11)
            yield (
                SimilarTrianglesProperty((vertex0, pt00, pt01), (vertex1, pt00, pt11)),
                _comment('%s and %s are perpendiculars from a point on the line %s to the line %s and from a point on %s to %s, correspondingly', vec0, vec1, line0, line1, line1, line0),
                [perp0, perp1, col0, col1]
            )

class SimilarTrianglesByAngleAndTwoSidesRule(Rule):
    def sources(self):
        return [ar for ar in self.context.congruent_angle_properties() if ar.angle0.vertex and ar.angle1.vertex]

    def apply(self, ca):
        ang0 = ca.angle0
        ang1 = ca.angle1
        for vec0, vec1 in [(ang0.vector0, ang0.vector1), (ang0.vector1, ang0.vector0)]:
            segments = (
                vec0.as_segment, vec1.as_segment,
                ang1.vector0.as_segment, ang1.vector1.as_segment
            )
            for inds in [(0, 1, 2, 3), (0, 2, 1, 3), (1, 0, 3, 2), (1, 3, 0, 2)]:
                elr = self.context.equal_length_ratios_property(*[segments[i] for i in inds])
                if elr:
                    break
            else:
                continue
            if ca.reason.obsolete and elr.reason.obsolete:
                continue
            yield (
                SimilarTrianglesProperty(
                    (ang0.vertex, vec0.end, vec1.end),
                    (ang1.vertex, ang1.vector0.end, ang1.vector1.end)
                ),
                'Two pairs of sides with the same ratio, and angle between the sides',
                [elr, ca]
            )

class CorrespondingAnglesInSimilarTriangles(SingleSourceRule):
    property_type = SimilarTrianglesProperty

    def apply(self, prop):
        ne0 = []
        ne1 = []
        for i in range(0, 3):
            ne0.append(self.context.not_equal_property(*side_of(prop.ABC, i).points))
            ne1.append(self.context.not_equal_property(*side_of(prop.DEF, i).points))

        for i in range(0, 3):
            angle0 = angle_of(prop.ABC, i)
            angle1 = angle_of(prop.DEF, i)
            if angle0 == angle1:
                continue
            ne = []
            for j in range(0, 3):
                if i != j:
                    if ne0[j]:
                        ne.append(ne0[j])
                    if ne1[j]:
                        ne.append(ne1[j])
            if len(ne) < 3 or prop.reason.obsolete and all(p.reason.obsolete for p in ne):
                continue
            yield (
                AnglesRatioProperty(angle0, angle1, 1),
                'Corresponding non-degenerate angles in similar triangles',
                [prop] + ne
            )
