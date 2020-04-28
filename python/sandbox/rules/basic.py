import itertools

from sandbox.property import *
from sandbox.scene import Scene
from sandbox.util import LazyComment, divide

from .abstract import Rule, SingleSourceRule

class ProportionalLengthsToLengthsRatioRule(SingleSourceRule):
    property_type = ProportionalLengthsProperty

    def apply(self, prop):
        ne = self.context.not_equal_property(*prop.segment0.points)
        if ne is None:
            ne = self.context.not_equal_property(*prop.segment1.points)
        if ne is None or prop.reason.obsolete and ne.reason.obsolete:
            return
        yield (
            LengthRatioProperty(prop.segment0, prop.segment1, prop.value),
            prop.reason.comments,
            [prop, ne]
        )

class LengthRatioTransitivityRule(Rule):
    """
    For three segments seg0, seg1, and seg2, from
        |seg0| = A |seg1|, and
        |seg1| = B |seg2|
    we conclude that |seg0| = A B |seg2|
    """
    def sources(self):
        return itertools.combinations(self.context.length_ratio_properties(allow_zeroes=True), 2)

    def apply(self, src):
        lr0, lr1 = src

        if lr0.reason.obsolete and lr1.reason.obsolete:
            return

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
    def sources(self):
        return itertools.combinations(self.context.list(PointsCoincidenceProperty), 2)

    def apply(self, src):
        co0, co1 = src
        if not co0.coincident and not co1.coincident:
            return
        if co0.reason.obsolete and co1.reason.obsolete:
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
                    LazyComment('%s and %s belong to two different lines %s and %s', *side.points, pt0.segment(ncl_pt), pt1.segment(ncl_pt)),
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
                            LazyComment('%s and %s belong to three lines %s, %s, and %s, at least two of them are different', *side.points, *lines),
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
                LazyComment('%s lies on the line %s %s, %s does not', pt_col, *common_points, pt_ncl),
                [ncl, col]
            )
        for common in common_points:
            ne = self.context.not_equal_property(common, pt_col)
            if ne is not None and not (reasons_are_too_old and ne.reason.obsolete):
                yield (
                    PointsCollinearityProperty(common, pt_col, pt_ncl, False),
                    LazyComment(
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
                LazyComment('two of three non-collinear points %s, %s, and %s', *prop.points),
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
        ar = self.context.angle_ratio_property(prop.angle0, prop.angle1)
        if ar is None or prop.reason.obsolete and ar.reason.obsolete:
            return
        value1 = divide(prop.degree, 1 + ar.value)
        value0 = prop.degree - value1
        if ar.value == 1:
            comment0 = LazyComment('%s + %s = %s + %s = %sº', ar.angle0, ar.angle0, ar.angle0, ar.angle1, prop.degree)
            comment1 = LazyComment('%s + %s = %s + %s = %sº', ar.angle1, ar.angle1, ar.angle1, ar.angle0, prop.degree)
        else:
            comment0 = LazyComment('%s + %s / %s = %s + %s = %sº', ar.angle0, ar.angle0, ar.value, ar.angle0, ar.angle1, prop.degree)
            comment1 = LazyComment('%s + %s %s = %s + %s = %sº', ar.angle1, ar.value, ar.angle1, ar.angle1, ar.angle0, prop.degree)
        yield (AngleValueProperty(ar.angle0, value0), comment0, [prop, ar])
        yield (AngleValueProperty(ar.angle1, value1), comment1, [prop, ar])

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
                LazyComment('non-zero parallel vectors %s and %s', vec0, vec1),
                [para, ne0, ne1]
            )

class PerpendicularSegmentsRule(SingleSourceRule):
    property_type = PerpendicularSegmentsProperty

    def apply(self, pv):
        seg0 = pv.segments[0]
        seg1 = pv.segments[1]
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
                LazyComment('non-zero perpendicular segments %s and %s', seg0, seg1),
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
                other = perp.segments[1] if seg0 == perp.segments[0] else perp.segments[0]
                yield (
                    PerpendicularSegmentsProperty(seg1, other),
                    LazyComment('Any line perpendicular to %s is also perpendicular to %s', seg0, seg1),
                    [perp, prop]
                )

class TwoPointsBelongsToTwoPerpendicularsRule(Rule):
    def sources(self):
        return itertools.combinations(self.context.list(PerpendicularSegmentsProperty), 2)

    def apply(self, src):
        perp0, perp1 = src
        common = next((seg for seg in perp0.segments if seg in perp1.segments), None)
        if common is None:
            return
        seg0 = next(seg for seg in perp0.segments if seg != common)
        seg1 = next(seg for seg in perp1.segments if seg != common)
        points = set(seg0.points + seg1.points)
        if len(points) != 3:
            return
        ncl = self.context.collinearity_property(*points)
        if ncl is None or ncl.collinear or ncl.reason.obsolete and perp0.reason.obsolete and perp1.reason.obsolete:
            return
        yield (
            PointsCoincidenceProperty(*common.points, True),
            LazyComment('%s and %s lie on perpendiculars to non-parallel lines %s and %s', *common.points, seg0, seg1),
            [perp0, perp1, ncl]
        )

class PerpendicularTransitivityRule(Rule):
    def sources(self):
        return itertools.combinations(self.context.list(PerpendicularSegmentsProperty), 2)

    def apply(self, src):
        perp0, perp1 = src
        common = next((seg for seg in perp0.segments if seg in perp1.segments), None)
        if common is None:
            return
        seg0 = next(seg for seg in perp0.segments if seg != common)
        seg1 = next(seg for seg in perp1.segments if seg != common)
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
            LazyComment('%s and %s are perpendiculars to non-zero %s', seg0, seg1, common),
            [perp0, perp1, ne]
        )
        yield (
            PointsCollinearityProperty(common_point, pt0, pt1, True),
            LazyComment('%s and %s are perpendiculars to non-zero %s', seg0, seg1, common),
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
            if cs:
                if prop.reason.obsolete and cs.reason.obsolete:
                    continue
                new_prop = ProportionalLengthsProperty(*segments[1], 1)
            else:
                cs = self.context.congruent_segments_property(*segments[1], True)
                if cs is None or prop.reason.obsolete and cs.reason.obsolete:
                    continue
                new_prop = ProportionalLengthsProperty(*segments[0], 1)
            yield (
                new_prop,
                LazyComment('%s and %s lie on the same perpendicular to %s', *seg0.points, seg1),
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
            LazyComment('Perpendicular bisector %s separates endpoints of the segment %s', segment0.as_line, segment1),
            [cs0, cs1, ne0, ne1]
        )

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
        for col in [p for p in self.context.list(PointsCollinearityProperty, [segment]) if p.collinear]:
            pt = next(p for p in col.points if p not in prop.points)
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

class LengthProductEqualityToRatioRule(SingleSourceRule):
    property_type = EqualLengthProductsProperty

    def apply(self, prop):
        ne = [self.context.not_equal_property(*seg.points) for seg in prop.segments]
        for (i, j, k, l) in [(0, 1, 2, 3), (0, 2, 1, 3), (3, 1, 2, 0), (3, 2, 1, 0)]:
            if ne[j] and ne[l] and not (prop.reason.obsolete and ne[j].reason.obsolete and ne[l].reason.obsolete):
                if prop.segments[j] == prop.segments[l]:
                    yield (
                        ProportionalLengthsProperty(prop.segments[i], prop.segments[k], 1),
                        prop.reason.comments,
                        prop.reason.premises + [ne[j], ne[l]]
                    )
                elif prop.segments[i] == prop.segments[j]:
                    yield (
                        ProportionalLengthsProperty(prop.segments[k], prop.segments[l], 1),
                        prop.reason.comments,
                        prop.reason.premises + [ne[j]]
                    )
                elif prop.segments[k] == prop.segments[l]:
                    yield (
                        ProportionalLengthsProperty(prop.segments[i], prop.segments[j], 1),
                        prop.reason.comments,
                        prop.reason.premises + [ne[l]]
                    )
                else:
                    yield (
                        EqualLengthRatiosProperty(*[prop.segments[x] for x in (i, j, k, l)]),
                        prop.reason.comments,
                        prop.reason.premises + [ne[j], ne[l]]
                    )

class RotatedAngleRule(Rule):
    def sources(self):
        return [(a0, a1) for a0, a1 in self.context.congruent_angles_with_vertex() if a0.vertex == a1.vertex]

    def apply(self, src):
        ang0, ang1 = src
        vertex = ang0.vertex
        pts0 = ang0.endpoints
        pts1 = ang1.endpoints
        if next((p for p in pts0 if p in pts1), None) is not None:
            return
        co = self.context.same_cyclic_order_property(Cycle(vertex, *pts0), Cycle(vertex, *pts1))
        if co is None:
            pts1 = (pts1[1], pts1[0])
            co = self.context.same_cyclic_order_property(Cycle(vertex, *pts0), Cycle(vertex, *pts1))
        if co is None:
            return
        ca = self.context.angle_ratio_property(ang0, ang1)
        if ca.reason.obsolete and co.reason.obsolete:
            return
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
        for vec in prop.angle.vector0, prop.angle.vector1:
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
        if prop.degree < 90:
            yield (
                AngleKindProperty(prop.angle, AngleKindProperty.Kind.acute),
                LazyComment('0º < %sº < 90º', prop.degree),
                [prop]
            )
        elif prop.degree > 90:
            yield (
                AngleKindProperty(prop.angle, AngleKindProperty.Kind.obtuse),
                LazyComment('90º < %sº < 180º', prop.degree),
                [prop]
            )
        else:
            yield (
                AngleKindProperty(prop.angle, AngleKindProperty.Kind.right),
                prop.reason.comments,
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
            prop.reason.comments,
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
            AngleKindProperty(ang.vector0.end.angle(ang.vertex, ang.vector1.end), AngleKindProperty.Kind.acute),
            LazyComment('An angle of %s, another angle is %s', Scene.Triangle(*ang.point_set), prop.kind),
            [prop]
        )
        yield (
            AngleKindProperty(ang.vector1.end.angle(ang.vertex, ang.vector0.end), AngleKindProperty.Kind.acute),
            LazyComment('An angle of %s, another angle is %s', Scene.Triangle(*ang.point_set), prop.kind),
            [prop]
        )

class VerticalAnglesRule(Rule):
    def sources(self):
        return itertools.combinations([av for av in self.context.list(AngleValueProperty) if av.angle.vertex and av.degree == 180], 2)

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
                ng0.vertex.angle(ng0.vector0.end, ng1.vector0.end),
                ng0.vertex.angle(ng0.vector1.end, ng1.vector1.end),
                1
            ),
            LazyComment('vertical angles'),
            [av0, av1]
        )
        yield (
            AngleRatioProperty(
                ng0.vertex.angle(ng0.vector0.end, ng1.vector1.end),
                ng0.vertex.angle(ng0.vector1.end, ng1.vector0.end),
                1
            ),
            LazyComment('vertical angles'),
            [av0, av1]
        )

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
                    sum_reason = self.context[SumOfAnglesProperty(angle0, angle1, 180)]
                except: #TODO: check contradiction with no try/except
                    continue
                ratio_reason = None
                if sum_reason is None:
                    for cnd in [p for p in self.context.list(SumOfAnglesProperty, [angle0]) if p.degree == 180]:
                        other = cnd.angle0 if cnd.angle1 == angle0 else cnd.angle1
                        ratio_reason = self.context.angle_ratio_property(other, angle1)
                        if ratio_reason:
                            if ratio_reason.value == 1:
                                sum_reason = cnd
                            break
                if sum_reason is None:
                    for cnd in [p for p in self.context.list(SumOfAnglesProperty, [angle1]) if p.degree == 180]:
                        other = cnd.angle0 if cnd.angle1 == angle1 else cnd.angle1
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
                    yield (p, 'Sum of alternate angles = 180º', reasons)
            else:
                ratio_reason = self.context.angle_ratio_property(angle0, angle1)
                if ratio_reason is None or prop.reason.obsolete and ratio_reason.reason.obsolete:
                    continue
                if ratio_reason.value == 1:
                    for p in AngleValueProperty.generate(lp0.vector(pt0), pt1.vector(lp1), 0):
                        yield (
                            p,
                            LazyComment('corresponding angles %s and %s are equal', angle0, angle1),
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
        for ne in self.context.list(PointsCoincidenceProperty, [ang.vertex]):
            if ne.coincident or prop.reason.obsolete and ne.reason.obsolete:
                continue
            pt = ne.points[0] if ang.vertex == ne.points[1] else ne.points[1]
            if pt in ang.point_set:
                continue
            yield (
                SumOfAnglesProperty(
                    ang.vertex.angle(ang.vector0.end, pt),
                    ang.vertex.angle(pt, ang.vector1.end),
                    180
                ),
                LazyComment('supplementary angles'),
                [prop, ne]
            )

class SameAngleRule(SingleSourceRule):
    property_type = AngleValueProperty

    def accepts(self, prop):
        return prop.degree == 0

    def apply(self, prop):
        ang = prop.angle
        for ne in self.context.list(PointsCoincidenceProperty):
            if ne.coincident or prop.reason.obsolete and ne.reason.obsolete:
                continue
            vec = ne.points[0].vector(ne.points[1])
            if vec.as_segment in (ang.vector0.as_segment, ang.vector1.as_segment):
                continue
            for ngl0, cmpl0 in good_angles(vec, ang.vector0):
                for ngl1, cmpl1 in good_angles(vec, ang.vector1):
                    if cmpl0 == cmpl1:
                        new_prop = AngleRatioProperty(ngl0, ngl1, 1)
                    else:
                        new_prop = SumOfAnglesProperty(ngl0, ngl1, 180)
                    yield (
                        new_prop,
                        LazyComment('common ray %s, and %s ↑↑ %s', vec, ang.vector0, ang.vector1),
                        [prop, ne]
                    )

class SameAngleRule2(Rule):
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
                ng0.vertex.angle(ng0.vector0.end, ng1.vector0.end),
                ng0.vertex.angle(ng0.vector1.end, ng1.vector1.end),
                1
            ),
            LazyComment('%s ↑↑ %s and %s ↑↑ %s', ng0.vector0, ng0.vector1, ng1.vector0, ng1.vector1),
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
                LazyComment('%s is the intersection point of segment %s and line %s', crossing, pt0.segment(pt1), prop.segment),
                [prop] + reasons
            )

class CeviansIntersectionRule(Rule):
    def sources(self):
        return itertools.combinations([av for av in self.context.list(AngleValueProperty) if av.angle.vertex and av.degree == 180], 2)

    def apply(self, src):
        av0, av1 = src
        ends0 = (av0.angle.vector0.end, av0.angle.vector1.end)
        ends1 = (av1.angle.vector0.end, av1.angle.vector1.end)
        vertex = next((pt for pt in ends0 if pt in ends1), None)
        if vertex is None:
            return
        pt0 = next(pt for pt in ends0 if pt != vertex)
        pt1 = next(pt for pt in ends1 if pt != vertex)
        if pt0 == pt1:
            return
        ncl = self.context.not_collinear_property(vertex, pt0, pt1)
        if ncl is None:
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
        angle0 = prop.angle.vertex.angle(prop.angle.vector0.end, prop.point)
        angle1 = prop.angle.vertex.angle(prop.angle.vector1.end, prop.point)
        yield (
            SumOfAnglesProperty(angle0, angle1, av.degree),
            LazyComment('%s + %s = %s = %sº', angle0, angle1, prop.angle, av.degree),
            [prop, av]
        )

class SameSideToInsideAngleRule(Rule):
    def sources(self):
        return itertools.combinations([op for op in self.context.list(SameOrOppositeSideProperty) if not op.same], 2)

    def apply(self, src):
        op0, op1 = src
        if op0.reason.obsolete and op1.reason.obsolete:
            return
        set0 = {*op0.points, *op0.segment.points}
        if set0 != {*op1.points, *op1.segment.points}:
            return
        centre = next((pt for pt in op0.segment.points if pt in op1.segment.points), None)
        if centre is None:
            return
        triangle = Scene.Triangle(*[pt for pt in set0 if pt != centre])
        comment = LazyComment('Line %s separates %s and %s, line %s separates %s and %s => the intersection %s lies inside %s', op0.segment.as_line, *op0.points, op1.segment.as_line, *op1.points, centre, triangle)
        angles = triangle.angles
        for i in range(0, 3):
            yield (
                PointInsideAngleProperty(centre, angles[i]),
                comment,
                [op0, op1]
            )
