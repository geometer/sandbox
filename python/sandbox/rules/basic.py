from sandbox.property import *
from sandbox.util import _comment, divide, side_of

class Rule:
    pass

class SingleSourceRule(Rule):
    def accepts(self, prop):
        return True

    def sources(self, context):
        return [p for p in context.list(self.property_type) if self.accepts(p)]

class DifferentAnglesToDifferentPointsRule(Rule):
    """
    For three vectors, v0, v1, v2, if it is known that
        v1 and v2 have common start (or end), and
        ∠(v0, v1) != ∠(v0, v2),
    then ends (starts) of v1 and v2 are different
    """
    def sources(self, context):
        return itertools.combinations(context.angle_value_properties(), 2)

    def apply(self, src, context):
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
    def sources(self, context):
        return context.length_ratio_properties()

    def apply(self, prop, context):
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
    def sources(self, context):
        return itertools.combinations(context.list(LengthRatioProperty), 2)

    def apply(self, src, context):
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

    def apply(self, cl0, context):
        for side, pt0 in [(side_of(cl0.points, i), cl0.points[i]) for i in range(0, 3)]:
            third_points = [pt0]
            for cl1 in [p for p in context.list(PointsCollinearityProperty, [side]) if p.collinear and p != cl0]:
                pt1 = next(pt for pt in cl1.points if pt not in side.points)
                third_points.append(pt1)

                for ncl_pt in side.points:
                    ncl = context.collinearity_property(pt0, pt1, ncl_pt)
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
                    ncl = context.collinearity_property(*triple)
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
    def sources(self, context):
        return itertools.product( \
            [p for p in context.list(PointsCollinearityProperty) if not p.collinear], \
            [p for p in context.list(PointsCollinearityProperty) if p.collinear] \
        )

    def apply(self, src, context):
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
            ne = context.not_equal_property(common, pt_col)
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

    def apply(self, prop, context):
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

    def apply(self, prop, context):
        if context.angle_value_property(prop.angle0) or context.angle_value_property(prop.angle1):
            return
        ar = context.angles_ratio_property(prop.angle0, prop.angle1)
        if ar is None or prop.reason.obsolete and ar.reason.obsolete:
            return
        value1 = divide(prop.degree, 1 + ar.value)
        value0 = prop.degree - value1
        if ar.value == 1:
            comment0 = _comment('%s + %s = %s + %s = %sº', ar.angle0, ar.angle0, ar.angle0, ar.angle1, prop.degree),
            comment1 = _comment('%s + %s = %s + %s = %sº', ar.angle1, ar.angle1, ar.angle1, ar.angle0, prop.degree),
        else:
            comment0 = _comment('%s + %s / %s = %s + %s = %sº', ar.angle0, ar.angle0, ar.value, ar.angle0, ar.angle1, prop.degree),
            comment1 = _comment('%s + %s %s = %s + %s = %sº', ar.angle1, ar.value, ar.angle1, ar.angle1, ar.angle0, prop.degree),
        yield (AngleValueProperty(ar.angle0, value0), comment0, [prop, ar])
        yield (AngleValueProperty(ar.angle1, value1), comment1, [prop, ar])

class LengthRatioRule(SingleSourceRule):
    property_type = LengthRatioProperty

    def apply(self, prop, context):
        seg0 = prop.segment0
        seg1 = prop.segment1

        ne0 = context.not_equal_property(*seg0.points)
        ne1 = context.not_equal_property(*seg1.points)
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
            ne = context.not_equal_property(pt0, pt1)
            if ne is None or prop.reason.obsolete and ne.reason.obsolete:
                return
            yield (PointsCoincidenceProperty(*seg0.points, False), _comment('Otherwise, %s = %s = %s', ne.points[0], common, ne.points[1]), [prop, ne])
            yield (PointsCoincidenceProperty(*seg1.points, False), _comment('Otherwise, %s = %s = %s', ne.points[1], common, ne.points[0]), [prop, ne])

class ParallelVectorsRule(SingleSourceRule):
    property_type = ParallelVectorsProperty

    def apply(self, pv, context):
        vec0 = pv.vector0
        vec1 = pv.vector1
        ne0 = context.not_equal_property(*vec0.points)
        ne1 = context.not_equal_property(*vec1.points)
        if ne0 is None or ne1 is None:
            return
        if pv.reason.obsolete and ne0.reason.obsolete and ne1.reason.obsolete:
            return
        for prop in AngleValueProperty.generate(vec0, vec1, 0):
            yield (
                prop,
                _comment('Non-zero parallel vectors %s and %s', vec0, vec1),
                [pv, ne0, ne1]
            )

class PerpendicularSegmentsRule(SingleSourceRule):
    property_type = PerpendicularSegmentsProperty

    def apply(self, pv, context):
        seg0 = pv.segment0
        seg1 = pv.segment1
        ne0 = context.not_equal_property(*seg0.points)
        ne1 = context.not_equal_property(*seg1.points)
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
    def sources(self, context):
        return [p for p in context.nondegenerate_angle_value_properties() if p.degree == 90]

    def apply(self, prop, context):
        if not prop.reason.obsolete:
            yield (
                PerpendicularSegmentsProperty(prop.angle.vector0.as_segment, prop.angle.vector1.as_segment),
                prop.reason.comments,
                prop.reason.premises
            )

class Degree0ToParallelVectorsRule(SingleSourceRule):
    property_type = AngleValueProperty

    def accepts(self, prop):
        return prop.degree == 0

    def apply(self, prop, context):
        if not prop.reason.obsolete:
            yield (
                ParallelVectorsProperty(prop.angle.vector0, prop.angle.vector1),
                prop.reason.comments,
                prop.reason.premises
            )

class CommonPerpendicularRule(SingleSourceRule):
    property_type = AngleValueProperty

    def accepts(self, prop):
        return prop.degree == 0

    def apply(self, prop, context):
        segments = (prop.angle.vector0.as_segment, prop.angle.vector1.as_segment)
        for seg0, seg1 in (segments, reversed(segments)):
            for perp in context.list(PerpendicularSegmentsProperty, [seg0]):
                if prop.reason.obsolete and perp.reason.obsolete:
                    continue
                other = perp.segment1 if seg0 == perp.segment0 else perp.segment0
                yield (
                    PerpendicularSegmentsProperty(seg1, other),
                    '', #TODO: write comment
                    [perp, prop]
                )

class SinglePerperndicularBisectorRule(SingleSourceRule):
    property_type = PerpendicularSegmentsProperty

    def apply(self, prop, context):
        if len({*prop.segment0.points, *prop.segment1.points}) != 4:
            return
        segments = (prop.segment0, prop.segment1)
        for seg0, seg1 in (segments, reversed(segments)):
            for i, j in ((0, 1), (1, 0)):
                ppb = context[PointOnPerpendicularBisectorProperty(seg0.points[i], seg1)]
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

    def apply(self, prop, context):
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

    def apply(self, prop, context):
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

    def apply(self, prop, context):
        segment = prop.points[0].segment(prop.points[1])
        for col in [p for p in context.list(PointsCollinearityProperty, [segment]) if p.collinear]:
            pt = next(p for p in col.points if p not in prop.points)
            value = context.angle_value_property(pt.angle(*prop.points))
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

    def apply(self, prop, context):
        foot0, reasons0 = context.foot_of_perpendicular(prop.points[0], prop.segment)
        if foot0 is None:
            return
        foot1, reasons1 = context.foot_of_perpendicular(prop.points[1], prop.segment)
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
