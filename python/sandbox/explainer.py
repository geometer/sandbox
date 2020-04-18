import itertools
import time
import sympy as sp

from .core import Constraint
from .predefined import enumerate_predefined_properties
from .property import *
from .propertyset import PropertySet
from .reason import Reason
from .rules.advanced import *
from .rules.basic import *
from .rules.triangle_elements import *
from .rules.triangles import *
from .rules.trigonometric import *
from .scene import Scene, Triangle
from .stats import Stats
from .util import LazyComment, divide

class Explainer:
    def __init__(self, scene, options={}):
        self.scene = scene
        self.context = PropertySet()
        self.__options = options
        self.__explanation_time = None
        self.__iteration_step_count = -1
        self.__rules = [
            LengthRatioTransitivityRule(self.context),
            ProportionalLengthsToLengthsRatioRule(self.context),
            SumAndRatioOfTwoAnglesRule(self.context),
            NonCollinearPointsAreDifferentRule(self.context),
            CoincidenceTransitivityRule(self.context),
            CollinearityCollisionRule(self.context),
            TwoPointsBelongsToTwoLinesRule(self.context),
            TwoPointsBelongsToTwoPerpendicularsRule(self.context),
            LengthRatioRule(self.context),
            ParallelVectorsRule(self.context),
            PerpendicularSegmentsRule(self.context),
            Degree90ToPerpendicularSegmentsRule(self.context),
            PerpendicularTransitivityRule(self.context),
            PerpendicularToEquidistantRule(self.context),
            EquidistantToPerpendicularRule(self.context),
            PointsSeparatedByLineAreNotCoincidentRule(self.context),
            SameSidePointInsideSegmentRule(self.context),
            TwoPerpendicularsRule(self.context),
            CommonPerpendicularRule(self.context),
            SideProductsInSimilarTrianglesRule(self.context),
            CorrespondingAnglesInSimilarTrianglesRule(self.context),
            LengthProductEqualityToRatioRule(self.context),
            CongruentTrianglesByAngleAndTwoSidesRule(self.context),
            SimilarTrianglesByTwoAnglesRule(self.context),
            SimilarTrianglesByAngleAndTwoSidesRule(self.context),
            SimilarTrianglesWithCongruentSideRule(self.context),
            BaseAnglesOfIsoscelesRule(self.context),
            LegsOfIsoscelesRule(self.context),
            RotatedAngleRule(self.context),
            AngleTypeByDegreeRule(self.context),
            RightAngleDegreeRule(self.context),
            AngleTypesInObtuseangledTriangleRule(self.context),
            PartOfAcuteAngleIsAcuteRule(self.context),
            SameAngleRule(self.context),
            SameAngleRule2(self.context),
            SupplementaryAnglesRule(self.context),
            VerticalAnglesRule(self.context),
            CorrespondingAndAlternateAnglesRule(self.context),
            CyclicOrderRule(self.context),
            PlanePositionsToLinePositionsRule(self.context),
            CeviansIntersectionRule(self.context),
            SameSideToInsideAngleRule(self.context),
            TwoAnglesWithCommonSideRule(self.context),
        ]
        if options.get('advanced'):
            self.__rules += [
                RightAngledTriangleMedianRule(self.context),
                Triangle30_60_90SidesRule(self.context),
                Triangle30_30_120SidesRule(self.context),
            ]
        if options.get('trigonometric'):
            self.__rules += [
                LawOfSinesRule(self.context),
            ]

    def __reason(self, prop, comments, premises=None):
        reason = Reason(len(self.context), self.__iteration_step_count, comments, premises)
        if prop in reason.all_premises:
            return
        existing = self.context[prop]
        #TODO: report contradiction between prop and existing
        if existing is None:
            prop.reason = reason
            prop.reason.obsolete = False
            self.context.add(prop)
        elif len(reason.all_premises) < len(existing.reason.all_premises):
            reason.index = existing.reason.index
            reason.generation = existing.reason.generation
            reason.obsolete = existing.reason.obsolete
            if hasattr(existing, 'synthetic'):
                prop.reason = reason
                self.context.add(prop)
            else:
                existing.reason = reason

    def explain(self):
        start = time.time()
        frozen = self.scene.is_frozen
        if not frozen:
            self.scene.freeze()
        self.__explain_all()
        if not frozen:
            self.scene.unfreeze()
        self.__explanation_time = time.time() - start

    def __explain_all(self):
        def iteration():
            for rule in self.__rules:
                for prop, comment, premises in rule.generate():
                    prop.rule = rule
                    yield (prop, comment, premises)

            for zero in [av for av in self.context.list(AngleValueProperty) if av.degree == 0]:
                zero_is_too_old = zero.reason.obsolete
                for ne in self.context.list(PointsCoincidenceProperty):
                    if ne.coincident or zero_is_too_old and ne.reason.obsolete:
                        continue
                    vec = ne.points[0].vector(ne.points[1])
                    if vec.as_segment in [zero.angle.vector0.as_segment, zero.angle.vector1.as_segment]:
                        continue
                    for ngl0, cmpl0 in good_angles(vec, zero.angle.vector0):
                        for ngl1, cmpl1 in good_angles(vec, zero.angle.vector1):
                            if cmpl0 == cmpl1:
                                prop = AngleRatioProperty(ngl0, ngl1, 1)
                            else:
                                prop = SumOfAnglesProperty(ngl0, ngl1, 180)
                            yield (
                                prop,
                                LazyComment('%s ↑↑ %s', zero.angle.vector0, zero.angle.vector1),
                                [zero, ne]
                            )

            for pia in self.context.list(PointInsideAngleProperty):
                A = pia.angle.vertex
                B = pia.angle.vector0.end
                C = pia.angle.vector1.end
                D = pia.point
                AD = A.segment(D)
                BC = B.segment(C)
                X, reasons = self.context.intersection_of_lines(AD, BC)
                if X is None or X in (A, B, C, D):
                    continue
                if pia.reason.obsolete and all(p.reason.obsolete for p in reasons):
                    continue

                comment = LazyComment('%s is intersection of ray [%s %s) and segment [%s %s]', X, A, D, B, C)
                yield (AngleValueProperty(A.angle(D, X), 0), [comment], [pia] + reasons)
                yield (AngleValueProperty(B.angle(C, X), 0), [comment], [pia] + reasons)
                yield (AngleValueProperty(C.angle(B, X), 0), [comment], [pia] + reasons)
                yield (AngleValueProperty(X.angle(B, C), 180), [comment], [pia] + reasons)

            for pia in self.context.list(PointInsideAngleProperty):
                if pia.reason.obsolete:
                    continue
                for endpoint in pia.angle.endpoints:
                    yield (
                        PointsCollinearityProperty(pia.point, pia.angle.vertex, endpoint, False),
                        '', #TODO: write comment
                        [pia]
                    )
                yield (
                    SameOrOppositeSideProperty(pia.angle.vector0.as_segment, pia.point, pia.angle.vector1.end, True),
                    '', #TODO: write comment
                    [pia]
                )
                yield (
                    SameOrOppositeSideProperty(pia.angle.vector1.as_segment, pia.point, pia.angle.vector0.end, True),
                    '', #TODO: write comment
                    [pia]
                )

            for ss0, ss1 in itertools.combinations([p for p in self.context.list(SameOrOppositeSideProperty) if p.same], 2):
                for pts in itertools.combinations(ss0.segment.points + ss1.segment.points, 3):
                    ncl = self.context.not_collinear_property(*pts)
                    if ncl:
                        break
                else:
                    continue

                if ss0.points[0] in ss1.points:
                    if ss0.points[1] in ss1.points:
                        continue
                    common = ss0.points[0]
                    other0 = ss0.points[1]
                    other1 = ss1.points[0] if ss1.points[1] == common else ss1.points[1]
                else:
                    common = ss0.points[1]
                    other0 = ss0.points[0]
                    if ss1.points[0] == common:
                        other1 = ss1.points[1]
                    elif ss1.points[1] == common:
                        other1 = ss1.points[0]
                    else:
                        continue

                if other0 not in ss1.segment.points or other1 not in ss0.segment.points:
                    continue

                vertex, reasons = self.context.intersection_of_lines(ss0.segment, ss1.segment)
                if vertex is None or vertex in [common, other0, other1]:
                    continue

                reasons = [ss0, ss1, ncl] + reasons
                if all(p.reason.obsolete for p in reasons):
                    continue

                yield (
                    PointInsideAngleProperty(common, vertex.angle(other0, other1)),
                    '', #TODO: write comment
                    reasons
                )

            angle_values = [prop for prop in self.context.angle_value_properties() \
                if prop.angle.vertex is not None]

            for av in [av for av in angle_values if av.degree == 0]:
                av_is_too_old = av.reason.obsolete
                vertex = av.angle.vertex
                pt0 = av.angle.vector0.end
                pt1 = av.angle.vector1.end
                for vec in (av.angle.vector0, av.angle.vector1):
                    for nc in self.context.list(PointsCollinearityProperty, [vec.as_segment]):
                        if nc.collinear or av_is_too_old and nc.reason.obsolete:
                            continue
                        segment = vertex.segment(
                            next(pt for pt in nc.points if pt not in vec.points)
                        )
                        yield (
                            SameOrOppositeSideProperty(segment, pt0, pt1, True),
                            [str(av), str(nc)], #TODO: better comment
                            [av, nc]
                        )

            for av in [av for av in angle_values if av.degree == 180]:
                av_is_too_old = av.reason.obsolete
                segment = av.angle.vector0.end.segment(av.angle.vector1.end)
                for ncl in self.context.list(PointsCollinearityProperty, [segment]):
                    if ncl.collinear or av_is_too_old and ncl.reason.obsolete:
                        continue
                    vertex = next(pt for pt in ncl.points if pt not in segment.points)
                    angle = vertex.angle(*segment.points)
                    yield (
                        PointInsideAngleProperty(av.angle.vertex, angle),
                        LazyComment('%s lies inside a segment with endpoints on sides of %s', av.angle.vertex, angle),
                        [av, ncl]
                    )
                    yield (
                        SameOrOppositeSideProperty(av.angle.vertex.segment(vertex), *segment.points, False),
                        LazyComment('%s lies inside segment %s, and %s is not on the line %s', av.angle.vertex, segment, vertex, segment),
                        [av, ncl]
                    )

            for sos0, sos1 in itertools.combinations(self.context.list(SameOrOppositeSideProperty), 2):
                if sos0.reason.obsolete and sos1.reason.obsolete:
                    continue
                if sos0.segment != sos1.segment:
                    continue

                if sos0.points[0] in sos1.points:
                    common = sos0.points[0]
                    other0 = sos0.points[1]
                elif sos0.points[1] in sos1.points:
                    common = sos0.points[1]
                    other0 = sos0.points[0]
                else:
                    continue
                other1 = sos1.points[0] if sos1.points[1] == common else sos1.points[1]
                if other0 == other1:
                    break
                yield (
                    SameOrOppositeSideProperty(sos0.segment, other0, other1, sos0.same == sos1.same),
                    'Transitivity', #TODO: better comment
                    [sos0, sos1]
                )

            for ar in self.context.same_triple_angle_ratio_properties():
                a0 = ar.angle0
                a1 = ar.angle1
                third_vertex = next(pt for pt in a0.point_set if pt not in (a0.vertex, a1.vertex))
                a2 = third_vertex.angle(a0.vertex, a1.vertex)
                a2_reason = self.context.angle_value_property(a2)
                if a2_reason is None:
                    continue
                if ar.reason.obsolete and a2_reason.reason.obsolete:
                    continue
                #a0 + a1 + a2 = 180
                #a0 + a1 = 180 - a2
                a1_value = divide(180 - a2_reason.degree, 1 + ar.value)
                a0_value = 180 - a2_reason.degree - a1_value
                comment = LazyComment('%s + %s + %s = 180º', a0, a1, a2)
                yield (AngleValueProperty(a0, a0_value), comment, [ar, a2_reason])
                yield (AngleValueProperty(a1, a1_value), comment, [ar, a2_reason])

            for aa in [p for p in self.context.list(AngleKindProperty) if p.kind == AngleKindProperty.Kind.acute]:
                base = aa.angle
                if base.vertex is None:
                    continue
                for vec0, vec1 in [(base.vector0, base.vector1), (base.vector1, base.vector0)]:
                    for col in [p for p in self.context.list(PointsCollinearityProperty, [vec0.as_segment]) if p.collinear]:
                        reasons_are_too_old = aa.reason.obsolete and col.reason.obsolete
                        pt = next(pt for pt in col.points if pt not in vec0.points)
                        for angle in [pt.angle(vec1.end, p) for p in vec0.points]:
                            ka = self.context.angle_value_property(angle)
                            if ka is None or reasons_are_too_old and ka.reason.obsolete:
                                continue
                            if ka.degree >= 90:
                                comment = LazyComment(
                                    '%s, %s, %s are collinear, %s is acute, and %s = %sº',
                                    pt, *vec0.points, base, angle, ka.degree
                                )
                                zero = base.vertex.angle(vec0.end, pt)
                                yield (AngleValueProperty(zero, 0), comment, [col, aa, ka])
                            break

            for aa in [p for p in self.context.list(AngleKindProperty) if p.kind == AngleKindProperty.Kind.acute]:
                base = aa.angle
                if base.vertex is None:
                    continue
                for vec0, vec1 in [(base.vector0, base.vector1), (base.vector1, base.vector0)]:
                    for perp in self.context.list(PerpendicularSegmentsProperty, [vec0.as_segment]):
                        other = perp.segment0 if vec0.as_segment == perp.segment1 else perp.segment1
                        if vec1.end not in other.points:
                            continue
                        foot = next(pt for pt in other.points if pt != vec1.end)
                        col = self.context.collinearity_property(foot, *vec0.points)
                        if col is None or not col.collinear:
                            continue
                        if aa.reason.obsolete and perp.reason.obsolete and col.reason.obsolete:
                            continue
                        yield (
                            AngleValueProperty(base.vertex.angle(vec0.end, foot), 0),
                            LazyComment(
                                '%s it the foot of the perpendicular from %s to %s, %s is acute',
                                foot, vec1.end, vec0, base
                            ),
                            [perp, col, aa]
                        )

            for aa in [p for p in self.context.list(AngleKindProperty) if p.kind == AngleKindProperty.Kind.obtuse]:
                base = aa.angle
                if base.vertex is None:
                    continue
                for vec0, vec1 in [(base.vector0, base.vector1), (base.vector1, base.vector0)]:
                    for perp in self.context.list(PerpendicularSegmentsProperty, [vec0.as_segment]):
                        other = perp.segment0 if vec0.as_segment == perp.segment1 else perp.segment1
                        if vec1.end not in other.points:
                            continue
                        foot = next(pt for pt in other.points if pt != vec1.end)
                        col = self.context.collinearity_property(foot, *vec0.points)
                        if col is None or not col.collinear:
                            continue
                        if aa.reason.obsolete and perp.reason.obsolete and col.reason.obsolete:
                            continue
                        yield (
                            AngleValueProperty(base.vertex.angle(vec0.end, foot), 180),
                            LazyComment(
                                '%s it the foot of the perpendicular from %s to %s, %s is obtuse',
                                foot, vec1.end, vec0, base
                            ),
                            [perp, col, aa]
                        )

            for aa in [p for p in self.context.list(AngleValueProperty) if p.degree == 90]:
                base = aa.angle
                if base.vertex is None:
                    continue
                for vec0, vec1 in [(base.vector0, base.vector1), (base.vector1, base.vector0)]:
                    for perp in self.context.list(PerpendicularSegmentsProperty, [vec0.as_segment]):
                        other = perp.segment0 if vec0.as_segment == perp.segment1 else perp.segment1
                        if vec1.end not in other.points:
                            continue
                        foot = next(pt for pt in other.points if pt != vec1.end)
                        col = self.context.collinearity_property(foot, *vec0.points)
                        if col is None or not col.collinear:
                            continue
                        if aa.reason.obsolete and perp.reason.obsolete and col.reason.obsolete:
                            continue
                        yield (
                            PointsCoincidenceProperty(base.vertex, foot, True),
                            LazyComment(
                                '%s it the foot of the perpendicular from %s to %s, %s is right',
                                foot, vec1.end, vec0, base
                            ),
                            [perp, col, aa]
                        )

            for oa in [p for p in self.context.list(AngleKindProperty) if p.kind == AngleKindProperty.Kind.obtuse]:
                base = oa.angle
                if base.vertex is None:
                    continue
                for vec0, vec1 in [(base.vector0, base.vector1), (base.vector1, base.vector0)]:
                    for col in [p for p in self.context.list(PointsCollinearityProperty, [vec0.as_segment]) if p.collinear]:
                        reasons_are_too_old = oa.reason.obsolete and col.reason.obsolete
                        pt = next(pt for pt in col.points if pt not in vec0.points)
                        for angle in [pt.angle(vec1.end, p) for p in vec0.points]:
                            ka = self.context.angle_value_property(angle)
                            if ka is None or reasons_are_too_old and ka.reason.obsolete:
                                continue
                            if ka.degree <= 90:
                                comment = LazyComment(
                                    '%s, %s, %s are collinear, %s is obtuse, and %s = %sº',
                                    pt, *vec0.points, base, angle, ka.degree
                                )
                                zero = base.vertex.angle(vec0.end, pt)
                                yield (AngleValueProperty(zero, 180), comment, [col, oa, ka])
                            break

            for ka in self.context.nondegenerate_angle_value_properties():
                base = ka.angle
                if ka.degree >= 90 or base.vertex is None:
                    continue
                ka_is_too_old = ka.reason.obsolete
                for vec0, vec1 in [(base.vector0, base.vector1), (base.vector1, base.vector0)]:
                    for col in [p for p in self.context.list(PointsCollinearityProperty, [vec0.as_segment]) if p.collinear]:
                        reasons_are_too_old = ka_is_too_old and col.reason.obsolete
                        pt = next(pt for pt in col.points if pt not in vec0.points)
                        for angle in [pt.angle(vec1.end, p) for p in vec0.points]:
                            ka2 = self.context.angle_value_property(angle)
                            if ka2 is None or reasons_are_too_old and ka2.reason.obsolete:
                                continue
                            if ka2.degree > ka.degree:
                                comment = LazyComment(
                                    '%s, %s, %s are collinear, %s is acute, and %s > %s',
                                    pt, *vec0.points, base, angle, base
                                )
                                zero = base.vertex.angle(vec0.end, pt)
                                yield (AngleValueProperty(zero, 0), comment, [ka, col, ka2])
                            break

            for aa0, aa1 in itertools.combinations([a for a in self.context.list(AngleKindProperty) if a.angle.vertex and a.kind == AngleKindProperty.Kind.acute], 2):
                vertex = aa0.angle.vertex
                if vertex != aa1.angle.vertex:
                    continue
                vectors0 = [aa0.angle.vector0, aa0.angle.vector1]
                vectors1 = [aa1.angle.vector0, aa1.angle.vector1]
                common = next((v for v in vectors0 if v in vectors1), None)
                if common is None:
                    continue
                other0 = next(v for v in vectors0 if v != common)
                other1 = next(v for v in vectors1 if v != common)
                col = self.context.collinearity_property(*other0.points, other1.end)
                if col is None or not col.collinear or aa0.reason.obsolete and aa1.reason.obsolete and col.reason.obsolete:
                    continue
                yield (
                    AngleValueProperty(other0.angle(other1), 0),
                    LazyComment('Both %s and %s are acute', aa0.angle, aa1.angle),
                    [aa0, aa1, col]
                )

            for cs in [p for p in self.context.length_ratio_properties(allow_zeroes=True) if p.value == 1]:
                if cs.reason.obsolete:
                    continue
                common = next((p for p in cs.segment0.points if p in cs.segment1.points), None)
                if common is None:
                    continue
                pt0 = next(p for p in cs.segment0.points if p != common)
                pt1 = next(p for p in cs.segment1.points if p != common)
                cs2 = self.context.congruent_segments_property(common.segment(pt0), pt0.segment(pt1), True)
                if cs2:
                    yield (
                        EquilateralTriangleProperty((common, pt0, pt1)),
                        'Congruent sides',
                        [cs, cs2]
                    )

            for cs in [p for p in self.context.length_ratio_properties(allow_zeroes=True) if p.value == 1]:
                if cs.segment1.points[0] in cs.segment0.points:
                    apex = cs.segment1.points[0]
                    base0 = cs.segment1.points[1]
                elif cs.segment1.points[1] in cs.segment0.points:
                    apex = cs.segment1.points[1]
                    base0 = cs.segment1.points[0]
                else:
                    continue
                base1 = cs.segment0.points[0] if apex == cs.segment0.points[1] else cs.segment0.points[1]
                ne = self.context.not_equal_property(base0, base1)
                if ne and not (cs.reason.obsolete and ne.reason.obsolete):
                    yield (
                        IsoscelesTriangleProperty(apex, base0.segment(base1)),
                        'Congruent legs',
                        [cs, ne]
                    )

            for ang0, ang1 in self.context.congruent_angles_with_vertex():
                if ang0.point_set != ang1.point_set:
                    continue
                nc = self.context.not_collinear_property(*ang0.point_set)
                if nc is None:
                    continue
                ca = self.context.angle_ratio_property(ang0, ang1)
                if ca.reason.obsolete and nc.reason.obsolete:
                    continue
                base = ang0.vertex.segment(ang1.vertex)
                apex = next(pt for pt in ang0.point_set if pt not in base.point_set)
                yield (
                    IsoscelesTriangleProperty(apex, base),
                    'Congruent base angles',
                    [ca, nc]
                )

            for equ in self.context.list(EquilateralTriangleProperty):
                ne = None
                sides = equ.triangle.sides
                for i in range(0, 3):
                    ne = self.context.not_equal_property(*sides[i].points)
                    if ne:
                        break
                if ne is not None and not equ.reason.obsolete and not ne.reason.obsolete:
                    angles = equ.triangle.angles
                    for i in range(0, 3):
                        yield (
                            AngleValueProperty(angles[i], 60),
                            LazyComment('Angle of non-degenerate equilateral %s', equ.triangle),
                            [equ]
                        )
                if not equ.reason.obsolete:
                    for i, j in itertools.combinations(range(0, 3), 2):
                        yield (
                            ProportionalLengthsProperty(sides[i], sides[j], 1),
                            LazyComment('Sides of equilateral %s', equ.triangle),
                            [equ]
                        )

            for ct in self.context.list(CongruentTrianglesProperty):
                ncl = self.context.not_collinear_property(*ct.triangle0.points)
                if ncl is None:
                    ncl = self.context.not_collinear_property(*ct.triangle1.points)
                if ncl is None or ct.reason.obsolete and ncl.reason.obsolete:
                    continue
                angles0 = ct.triangle0.angles
                angles1 = ct.triangle1.angles
                for i in range(0, 3):
                    if angles0[i] != angles1[i]:
                        yield (
                            AngleRatioProperty(angles0[i], angles1[i], 1),
                            'Corresponding angles in congruent non-degenerate triangles',
                            [ct, ncl]
                        )

            for st in self.context.list(SimilarTrianglesProperty):
                st_is_too_old = st.reason.obsolete
                sides0 = st.triangle0.sides
                sides1 = st.triangle1.sides
                for i in range(0, 3):
                    cs = self.context.congruent_segments_property(sides0[i], sides1[i], True)
                    if cs is None:
                        continue
                    if st_is_too_old and cs.reason.obsolete:
                        break
                    yield (
                        CongruentTrianglesProperty(st.triangle0, st.triangle1),
                        'Similar triangles with congruent corresponding sides',
                        [st, cs]
                    )
                    break

            for ratio0, ratio1 in self.context.equal_length_ratios_with_common_denominator():
                prop = self.context.congruent_segments_property(ratio0[0], ratio1[0], True)
                if prop:
                    continue
                ratio_prop = self.context.equal_length_ratios_property(*ratio0, *ratio1)
                yield (
                    ProportionalLengthsProperty(ratio0[0], ratio1[0], 1),
                    ratio_prop.reason.comments,
                    ratio_prop.reason.premises
                )

            for ct in self.context.list(CongruentTrianglesProperty):
                if ct.reason.obsolete:
                    continue
                sides0 = ct.triangle0.sides
                sides1 = ct.triangle1.sides
                for i in range(0, 3):
                    segment0 = sides0[i]
                    segment1 = sides1[i]
                    if segment0 != segment1:
                        yield (
                            ProportionalLengthsProperty(segment0, segment1, 1),
                            'Corresponding sides in congruent triangles',
                            [ct]
                        )

            for st in self.context.list(SimilarTrianglesProperty):
                sides0 = st.triangle0.sides
                sides1 = st.triangle1.sides
                for i in range(0, 3):
                    lr, ratio = self.context.length_ratio_property_and_value(sides0[i], sides1[i], True)
                    if lr is None:
                        continue
                    if ratio == 1 or st.reason.obsolete and lr.reason.obsolete:
                        break
                    for j in [j for j in range(0, 3) if j != i]:
                        yield (
                            ProportionalLengthsProperty(sides0[j], sides1[j], ratio),
                            'Ratios of sides in similar triangles',
                            [st, lr]
                        )
                    break

            for av in self.context.angle_value_properties():
                if av.angle.vertex is None:
                    continue
                av_is_too_old = av.reason.obsolete

                second = av.angle.vector0.end.angle(av.angle.vertex, av.angle.vector1.end)
                third = av.angle.vector1.end.angle(av.angle.vertex, av.angle.vector0.end)
                if av.degree == 180:
                    if av_is_too_old:
                        continue
                    for ang in second, third:
                        yield (
                            AngleValueProperty(ang, 0),
                            LazyComment('%s = 180º', av.angle),
                            [av]
                        )
                else:
                    second_reason = self.context.angle_value_property(second)
                    if second_reason:
                        if av_is_too_old and second_reason.reason.obsolete:
                            continue
                        yield (
                            AngleValueProperty(third, 180 - av.degree - second_reason.degree),
                            LazyComment('%s + %s + %s = 180º', third, av.angle, second),
                            [av, second_reason]
                        )
                    else:
                        third_reason = self.context.angle_value_property(third)
                        if third_reason is None or av_is_too_old and third_reason.reason.obsolete:
                            continue
                        yield (
                            AngleValueProperty(second, 180 - av.degree - third_reason.degree),
                            LazyComment('%s + %s + %s = 180º', second, av.angle, third),
                            [av, third_reason]
                        )

            for sa in self.context.list(SumOfAnglesProperty):
                av0 = self.context.angle_value_property(sa.angle0)
                av1 = self.context.angle_value_property(sa.angle1)
                if av0 and av1:
                    continue
                elif av0:
                    if sa.reason.obsolete and av0.reason.obsolete:
                        continue
                    yield (
                        AngleValueProperty(sa.angle1, sa.degree - av0.degree),
                        LazyComment('%sº - %sº', sa.degree, av0.degree),
                        [sa, av0]
                    )
                elif av1:
                    if sa.reason.obsolete and av1.reason.obsolete:
                        continue
                    yield (
                        AngleValueProperty(sa.angle0, sa.degree - av1.degree),
                        LazyComment('%sº - %sº', sa.degree, av1.degree),
                        [sa, av1]
                    )

            for ar in [p for p in self.context.list(SumOfAnglesProperty) if p.angle0.vertex is not None and p.angle0.vertex == p.angle1.vertex and p.degree == 180]:
                common = next((pt for pt in ar.angle0.endpoints if pt in ar.angle1.endpoints), None)
                if common is None:
                    continue
                pt0 = next(pt for pt in ar.angle0.endpoints if pt not in ar.angle1.endpoints)
                pt1 = next(pt for pt in ar.angle1.endpoints if pt not in ar.angle0.endpoints)
                oppo = self.context[SameOrOppositeSideProperty(ar.angle0.vertex.segment(common), pt0, pt1, False)]
                if not oppo or oppo.same or ar.reason.obsolete and oppo.reason.obsolete:
                    continue
                yield (
                    AngleValueProperty(ar.angle0.vertex.angle(pt0, pt1), 180),
                    LazyComment('%s + %s', ar.angle0, ar.angle1),
                    [ar, oppo]
                )

            for av in self.context.list(AngleValueProperty):
                if av.reason.obsolete or av.angle.vertex is None:
                    continue
                yield (
                    PointsCollinearityProperty(*av.angle.point_set, av.degree in (0, 180)),
                    '',#TODO: write comment
                    [av]
                )

            for ang0, ang1 in self.context.congruent_angles_with_vertex():
                ncl0 = self.context.not_collinear_property(*ang0.point_set)
                ncl1 = self.context.not_collinear_property(*ang1.point_set)
                if ncl0 and ncl1 or not ncl0 and not ncl1:
                    continue
                ca = self.context.angle_ratio_property(ang0, ang1)
                if ncl0:
                    yield (
                        PointsCollinearityProperty(*ang1.point_set, False),
                        'Transitivity',
                        [ca, ncl0]
                    )
                else:
                    yield (
                        PointsCollinearityProperty(*ang0.point_set, False),
                        'Transitivity',
                        [ca, ncl1]
                    )

            for zero in [p for p in self.context.list(AngleValueProperty) if p.angle.vertex is None and p.degree == 0]:
                zero_is_too_old = zero.reason.obsolete
                ang = zero.angle

                for vec0, vec1 in [(ang.vector0, ang.vector1), (ang.vector1, ang.vector0)]:
                    for i, j in [(0, 1), (1, 0)]:
                        ncl = self.context.not_collinear_property(*vec0.points, vec1.points[i])
                        if ncl is None:
                            continue
                        ne = self.context.not_equal_property(*vec1.points)
                        if ne is None:
                            continue
                        if zero_is_too_old and ncl.reason.obsolete and ne.reason.obsolete:
                            continue
                        yield (
                            PointsCollinearityProperty(*vec0.points, vec1.points[j], False),
                            'Transitivity',
                            [ncl, zero, ne]
                        )
                        yield (
                            PointsCollinearityProperty(*vec1.points, vec0.points[i], False),
                            'Transitivity',
                            [ncl, zero, ne]
                        )
                        yield (
                            PointsCollinearityProperty(*vec1.points, vec0.points[j], False),
                            'Transitivity',
                            [ncl, zero, ne]
                        )

            for zero in [p for p in self.context.list(AngleValueProperty) if p.angle.vertex is None and p.degree == 0]:
                ang = zero.angle
                ncl = self.context.not_collinear_property(*ang.vector0.points, ang.vector1.points[0])
                if ncl is None:
                    continue
                ne = self.context.not_equal_property(*ang.vector1.points)
                if ne is None:
                    continue
                if zero.reason.obsolete and ncl.reason.obsolete and ne.reason.obsolete:
                    continue
                comment = LazyComment('%s ↑↑ %s', ang.vector0, ang.vector1)
                premises = [zero, ncl, ne]
                yield (
                    SameOrOppositeSideProperty(ang.vector0.as_segment, *ang.vector1.points, True),
                    comment, premises
                )
                yield (
                    SameOrOppositeSideProperty(ang.vector1.as_segment, *ang.vector0.points, True),
                    comment, premises
                )
                yield (
                    SameOrOppositeSideProperty(
                        ang.vector0.start.segment(ang.vector1.end),
                        ang.vector0.end, ang.vector1.start, False
                    ),
                    comment, premises
                )
                yield (
                    SameOrOppositeSideProperty(
                        ang.vector1.start.segment(ang.vector0.end),
                        ang.vector1.end, ang.vector0.start, False
                    ),
                    comment, premises
                )

            congruent_segments = [p for p in self.context.length_ratio_properties(allow_zeroes=True) if p.value == 1]
            def common_point(segment0, segment1):
                if segment0.points[0] in segment1.points:
                    if segment0.points[1] in segment1.points:
                        return None
                    return segment0.points[0]
                if segment0.points[1] in segment1.points:
                    return segment0.points[1]
                return None
            def other_point(segment, point):
                return segment.points[0] if point == segment.points[1] else segment.points[1]

            for cs0, cs1 in itertools.combinations(congruent_segments, 2):
                if cs0.reason.obsolete and cs1.reason.obsolete:
                    continue
                for seg0, seg1 in [(cs0.segment0, cs0.segment1), (cs0.segment1, cs0.segment0)]:
                    points0 = set((*seg0.points, *cs1.segment0.points))
                    if len(points0) != 3 or points0 == set((*seg1.points, *cs1.segment1.points)):
                        continue
                    common0 = common_point(seg0, cs1.segment0)
                    common1 = common_point(seg1, cs1.segment1)
                    if common1 is None:
                        continue
                    third0 = other_point(seg0, common0).vector(other_point(cs1.segment0, common0))
                    third1 = other_point(seg1, common1).vector(other_point(cs1.segment1, common1))
                    prop = CongruentTrianglesProperty(
                        (common0, *third0.points), (common1, *third1.points)
                    )
                    if third0.as_segment == third1.as_segment:
                        yield (
                            prop,
                            LazyComment('Common side %s, two pairs of congruent sides', third0),
                            [cs0, cs1]
                        )
                    else:
                        cs2 = self.context.congruent_segments_property(third0.as_segment, third1.as_segment, True)
                        if cs2:
                            yield (
                                prop,
                                'Three pairs of congruent sides',
                                [cs0, cs1, cs2]
                            )

            for sos in self.context.list(SameOrOppositeSideProperty):
                for col in [p for p in self.context.list(PointsCollinearityProperty) if p.collinear]:
                    if sos.segment.points[0] not in col.points:
                        continue
                    if sos.segment.points[1] not in col.points:
                        continue
                    too_old = sos.reason.obsolete and col.reason.obsolete
                    other = next(pt for pt in col.points if pt not in sos.segment.points)
                    for pt in sos.segment.points:
                        ne = self.context.not_equal_property(other, pt)
                        if ne is None or too_old and ne.reason.obsolete:
                            continue
                        yield (
                            SameOrOppositeSideProperty(other.segment(pt), *sos.points, sos.same),
                            LazyComment('%s is same line as %s', other.segment(pt), sos.segment),
                            [sos, col, ne]
                        )

        for prop, comment in enumerate_predefined_properties(self.scene, max_layer=self.__options.get('max_layer', 'user')):
            self.__reason(prop, comment, [])

        self.__iteration_step_count = 0
        while itertools.count():
            explained_size = len(self.context)
            for prop, comment, premises in iteration():
                self.__reason(prop, comment, premises)
            for prop in self.context.all:
                prop.reason.obsolete = prop.reason.generation < self.__iteration_step_count
            self.__iteration_step_count += 1
            if len(self.context) == explained_size:
                break

    def dump(self, properties_to_explain=[]):
        if len(self.context) > 0:
            print('Explained:')
            explained = self.context.all
            explained.sort(key=lambda p: p.reason.index)
            for prop in explained:
                print('\t%2d (%d): %s [%s]' % (prop.reason.index, prop.reason.generation, prop, prop.reason))
        if properties_to_explain:
            unexplained = [prop for prop in properties_to_explain if prop not in self.context]
            if len(unexplained) > 0:
                print('\nNot explained:')
                for prop in unexplained:
                    print('\t%s' % prop)

    def stats(self, properties_to_explain=[]):
        def type_presentation(kind):
            return kind.__doc__.strip() if kind.__doc__ else kind.__name__

        unexplained = [prop for prop in properties_to_explain if prop not in self.context]
        unexplained_by_kind = {}
        for prop in unexplained:
            kind = type(prop)
            unexplained_by_kind[kind] = unexplained_by_kind.get(kind, 0) + 1
        unexplained_by_kind = [(type_presentation(k), v) for k, v in unexplained_by_kind.items()]
        unexplained_by_kind.sort(key=lambda pair: -pair[1])

        return Stats([
            ('Explained properties', len(self.context)),
            self.context.stats(),
            ('Explained property keys', self.context.keys_num()),
            ('Unexplained properties', len(unexplained)),
            Stats(unexplained_by_kind),
            ('Iterations', self.__iteration_step_count),
            ('Explanation time', '%.3f sec' % self.__explanation_time),
        ], 'Explainer stats')

    def explained(self, obj):
        if isinstance(obj, Property):
            return obj in self.context
        if isinstance(obj, Scene.Angle):
            rsn = self.context.angle_value_property(obj)
            return rsn.degree if rsn else None
        raise Exception('Explanation not supported for objects of type %s' % type(obj).__name__)

    def explanation(self, obj):
        if isinstance(obj, Property):
            return self.context[obj]
        if isinstance(obj, Scene.Angle):
            return self.context.angle_value_property(obj)
        return None
