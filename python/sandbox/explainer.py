import itertools
import time
import sympy as sp

from .core import Constraint
from .property import *
from .propertyset import PropertySet
from .reason import Reason
from .rules.advanced import *
from .rules.basic import *
from .rules.trigonometric import *
from .scene import Scene
from .stats import Stats
from .util import _comment, divide, side_of, angle_of

class Explainer:
    def __init__(self, scene, options=()):
        self.scene = scene
        self.context = PropertySet()
        self.__options = options
        self.__explanation_time = None
        self.__iteration_step_count = -1
        self.__rules = [
            DifferentAnglesToDifferentPointsRule(),
            LengthRatioSimplificationRule(),
            LengthRatioTransitivityRule(),
            SumAndRatioOfTwoAnglesRule(),
            NonCollinearPointsAreDifferentRule(),
            CollinearityCollisionRule(),
            TwoPointsBelongsToTwoLinesRule(),
            LengthRatioRule(),
            ParallelVectorsRule(),
            PerpendicularVectorsRule(),
            Degree90ToPerpendicularVectorsRule(),
            #Degree0ToParallelVectorsRule(),
            SinglePerperndicularBisectorRule(),
            SeparatedPointsRule(),
            PointOnPerpendicularBisectorIsEquidistantRule(),
            SameSidePointInsideSegmentRule(),
            TwoPerpendicularsRule(),
            CommonPerpendicularRule(),
        ]
        if 'advanced' in options:
            self.__rules += [
                RightAngledTriangleMedianRule(),
                Triangle30_60_90SidesRule(),
                Triangle30_30_120SidesRule(),
            ]
        if 'trigonometric' in options:
            self.__rules += [
                LawOfSinesRule(),
            ]

    def __reason(self, prop, comments, premises=None):
        reason = Reason(len(self.context), self.__iteration_step_count, comments, premises)
        if prop in reason.all_premises:
            return
        existing = self.context[prop]
        #TODO: report contradiction between prop and existing
        if existing is None:
            prop.reason = Reason(len(self.context), self.__iteration_step_count, comments, premises)
            prop.reason.obsolete = False
            self.context.add(prop)
        elif len(reason.all_premises) < len(existing.reason.all_premises):
            reason.index = existing.reason.index
            reason.generation = existing.reason.generation
            reason.obsolete = existing.reason.obsolete
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
                for src in rule.sources(self.context):
                    for reason in rule.apply(src, self.context):
                        yield reason

            for prop in self.context.list(SameOrOppositeSideProperty):
                pt0 = prop.points[0]
                pt1 = prop.points[1]
                crossing, reasons = self.context.intersection_of_lines(prop.segment, pt0.segment(pt1))
                if not crossing:
                    continue
                if prop.reason.obsolete and all(p.reason.obsolete for p in reasons):
                    continue
                if prop.same:
                    yield (
                        AngleValueProperty(crossing.angle(pt0, pt1), 0),
                        _comment('%s is the intersection point of lines %s and %s', crossing, pt0.segment(pt1), prop.segment),
                        [prop] + reasons
                    )
                else:
                    yield (
                        AngleValueProperty(crossing.angle(pt0, pt1), 180),
                        _comment('%s is the intersection point of segment %s and line %s', crossing, pt0.segment(pt1), prop.segment),
                        [prop] + reasons
                    )

            for ra in [av for av in self.context.nondegenerate_angle_value_properties() if av.degree == 90]:
                ra_is_too_old = ra.reason.obsolete
                vectors = (ra.angle.vector0, ra.angle.vector1)
                for vec0, vec1 in (vectors, reversed(vectors)):
                    for col in [p for p in self.context.list(PointsCollinearityProperty, [vec0.as_segment]) if p.collinear]:
                        reasons_are_too_old = ra_is_too_old and col.reason.obsolete
                        pt0 = next(p for p in col.points if p not in vec0.points)
                        for pt1 in vec0.points:
                            ne = self.context.not_equal_property(pt0, pt1)
                            if ne is not None and not (reasons_are_too_old and ne.reason.obsolete):
                                for prop in AngleValueProperty.generate(vec1, pt0.vector(pt1), 90):
                                    yield (prop, '', [ra, col, ne]) #TODO: write comment

            for av in [av for av in self.context.list(AngleValueProperty) if av.angle.vertex and av.degree == 180]:
                av_is_too_old = av.reason.obsolete
                ang = av.angle
                for ne in self.context.list(PointsCoincidenceProperty, [ang.vertex]):
                    if ne.coincident or av_is_too_old and ne.reason.obsolete:
                        continue
                    pt = ne.points[0] if ang.vertex == ne.points[1] else ne.points[1]
                    if pt in ang.points:
                        continue
                    yield (
                        SumOfAnglesProperty(
                            ang.vertex.angle(ang.vector0.end, pt),
                            ang.vertex.angle(pt, ang.vector1.end),
                            180
                        ),
                        'Supplementary angles',
                        [av, ne]
                    )

            for av0, av1 in itertools.combinations([av for av in self.context.list(AngleValueProperty) if av.angle.vertex and av.degree == 180], 2):
                ends0 = (av0.angle.vector0.end, av0.angle.vector1.end)
                ends1 = (av1.angle.vector0.end, av1.angle.vector1.end)
                vertex = next((pt for pt in ends0 if pt in ends1), None)
                if vertex is None:
                    continue
                pt0 = next(pt for pt in ends0 if pt != vertex)
                pt1 = next(pt for pt in ends1 if pt != vertex)
                if pt0 == pt1:
                    continue
                ncl = self.context.not_collinear_property(vertex, pt0, pt1)
                if ncl is None:
                    continue
                segment0 = pt0.segment(av1.angle.vertex)
                segment1 = pt1.segment(av0.angle.vertex)
                crossing, reasons = self.context.intersection_of_lines(segment0, segment1)
                if crossing is None:
                    continue
                if av0.reason.obsolete and av1.reason.obsolete and ncl.reason.obsolete and all(r.reason.obsolete for r in reasons):
                    continue
                comment = _comment('%s is the intersection of cevians %s and %s with %s and %s inside the sides of △ %s %s %s', crossing, segment0, segment1, av1.angle.vertex, av0.angle.vertex, vertex, pt0, pt1)
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

            for op0, op1 in itertools.combinations([op for op in self.context.list(SameOrOppositeSideProperty) if not op.same], 2):
                if op0.reason.obsolete and op1.reason.obsolete:
                    continue
                set0 = {*op0.points, *op0.segment.points}
                if set0 != {*op1.points, *op1.segment.points}:
                    continue
                centre = next((pt for pt in op0.segment.points if pt in op1.segment.points), None)
                if centre is None:
                    continue
                triangle = [pt for pt in set0 if pt != centre]
                comment = _comment('Line %s separates %s and %s, line %s separates %s and %s => the intersection %s lies inside △ %s %s %s', op0.segment, *op0.points, op1.segment, *op1.points, centre, *triangle)
                for i in range(0, 3):
                    yield (
                        PointInsideAngleProperty(centre, angle_of(triangle, i)),
                        comment,
                        [op0, op1]
                    )

            for av0, av1 in itertools.combinations([av for av in self.context.list(AngleValueProperty) if av.angle.vertex and av.degree == 180], 2):
                if av0.reason.obsolete and av1.reason.obsolete:
                    continue
                ng0 = av0.angle
                ng1 = av1.angle
                if ng0.vertex != ng1.vertex:
                    continue
                if len(ng0.points.union(ng1.points)) != 5:
                    continue
                yield (
                    AnglesRatioProperty(
                        ng0.vertex.angle(ng0.vector0.end, ng1.vector0.end),
                        ng0.vertex.angle(ng0.vector1.end, ng1.vector1.end),
                        1
                    ),
                    'Vertical angles',
                    [av0, av1]
                )
                yield (
                    AnglesRatioProperty(
                        ng0.vertex.angle(ng0.vector0.end, ng1.vector1.end),
                        ng0.vertex.angle(ng0.vector1.end, ng1.vector0.end),
                        1
                    ),
                    'Vertical angles',
                    [av0, av1]
                )

            for av in [av for av in self.context.list(AngleValueProperty) if av.angle.vertex and av.degree == 0]:
                av_is_too_old = av.reason.obsolete
                ang = av.angle
                for ne in self.context.list(PointsCoincidenceProperty, [ang.vertex]):
                    if ne.coincident or av_is_too_old and ne.reason.obsolete:
                        continue
                    pt = ne.points[0] if ang.vertex == ne.points[1] else ne.points[1]
                    if pt in ang.points:
                        continue
                    yield (
                        AnglesRatioProperty(
                            ang.vertex.angle(pt, ang.vector0.end),
                            ang.vertex.angle(pt, ang.vector1.end),
                            1
                        ),
                        'Same angle',
                        [av, ne]
                    )

            for av0, av1 in itertools.combinations([av for av in self.context.list(AngleValueProperty) if av.angle.vertex and av.degree == 0], 2):
                if av0.reason.obsolete and av1.reason.obsolete:
                    continue
                ng0 = av0.angle
                ng1 = av1.angle
                if ng0.vertex != ng1.vertex:
                    continue
                if len(ng0.points.union(ng1.points)) != 5:
                    continue
                yield (
                    AnglesRatioProperty(
                        ng0.vertex.angle(ng0.vector0.end, ng1.vector0.end),
                        ng0.vertex.angle(ng0.vector1.end, ng1.vector1.end),
                        1
                    ),
                    'Same angle',
                    [av0, av1]
                )
                yield (
                    AnglesRatioProperty(
                        ng0.vertex.angle(ng0.vector0.end, ng1.vector1.end),
                        ng0.vertex.angle(ng0.vector1.end, ng1.vector0.end),
                        1
                    ),
                    'Same angle',
                    [av0, av1]
                )

            for so in self.context.list(SameOrOppositeSideProperty):
                so_is_too_old = so.reason.obsolete
                lp0 = so.segment.points[0]
                lp1 = so.segment.points[1]
                ne = self.context.not_equal_property(lp0, lp1)
                if ne is None:
                    continue
                reasons_are_too_old = so_is_too_old and ne.reason.obsolete
                for pt0, pt1 in [so.points, reversed(so.points)]:
                    if so.same:
                        sum_reason = self.context[SumOfAnglesProperty(lp0.angle(pt0, lp1), lp1.angle(pt1, lp0), 180)]
                        if sum_reason is None or reasons_are_too_old and sum_reason.reason.obsolete:
                            continue
                        if sum_reason.degree == 180:
                            for prop in AngleValueProperty.generate(lp0.vector(pt0), lp1.vector(pt1), 0):
                                yield (prop, 'Alternate angles', [so, sum_reason, ne])
                    else:
                        ratio_reason = self.context.angles_ratio_property(lp0.angle(pt0, lp1), lp1.angle(pt1, lp0))
                        if ratio_reason is None or reasons_are_too_old and ratio_reason.reason.obsolete:
                            continue
                        if ratio_reason.value == 1:
                            for prop in AngleValueProperty.generate(lp0.vector(pt0), pt1.vector(lp1), 0):
                                yield (prop, 'Corresponding angles', [so, ratio_reason, ne])

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
                                prop = AnglesRatioProperty(ngl0, ngl1, 1)
                            else:
                                prop = SumOfAnglesProperty(ngl0, ngl1, 180)
                            yield (
                                prop,
                                _comment('%s ↑↑ %s', zero.angle.vector0, zero.angle.vector1),
                                [zero, ne]
                            )

            for pia in self.context.list(PointInsideAngleProperty):
                acute = self.context[AcuteAngleProperty(pia.angle)]
                if acute is None or pia.reason.obsolete and acute.reason.obsolete:
                    continue
                for vec in pia.angle.vector0, pia.angle.vector1:
                    angle = pia.angle.vertex.angle(vec.end, pia.point)
                    yield (
                        AcuteAngleProperty(angle),
                        _comment('%s is a part of acute %s', angle, pia.angle),
                        [pia, acute]
                    )

            for pia in self.context.list(PointInsideAngleProperty):
                right = self.context.angle_value_property(pia.angle)
                if right is None or right.degree != 90 or pia.reason.obsolete and right.reason.obsolete:
                    continue
                for vec in pia.angle.vector0, pia.angle.vector1:
                    angle = pia.angle.vertex.angle(vec.end, pia.point)
                    yield (
                        AcuteAngleProperty(angle),
                        _comment('%s is a part of right %s', angle, pia.angle),
                        [pia, right]
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

                comment = _comment('%s is intersection of ray [%s %s) and segment [%s %s]', X, A, D, B, C)
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

            for pia in self.context.list(PointInsideAngleProperty):
                av = self.context.angle_value_property(pia.angle)
                if av is None or pia.reason.obsolete and av.reason.obsolete:
                    continue
                angle0 = pia.angle.vertex.angle(pia.angle.vector0.end, pia.point)
                angle1 = pia.angle.vertex.angle(pia.angle.vector1.end, pia.point)
                yield (
                    SumOfAnglesProperty(angle0, angle1, av.degree),
                    'Two angles with common side',
                    [pia, av]
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
                        _comment('%s lies inside a segment with endpoints on sides of %s', av.angle.vertex, angle),
                        [av, ncl]
                    )
                    yield (
                        SameOrOppositeSideProperty(av.angle.vertex.segment(vertex), *segment.points, False),
                        _comment('%s lies inside segment %s, and %s is not on the line %s', av.angle.vertex, segment, vertex, segment),
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

            congruent_angles = self.context.congruent_angle_properties()
            congruent_angles_with_vertex = [ar for ar in congruent_angles if ar.angle0.vertex and ar.angle1.vertex]
            same_triple_ratios = self.context.same_triple_angle_ratio_properties()

            for ar in same_triple_ratios:
                a0 = ar.angle0
                a1 = ar.angle1
                if a0.vertex is None or a1.vertex is None:
                    continue
                s0 = {a0.vertex, a0.vector0.end, a0.vector1.end}
                s1 = {a1.vertex, a1.vector0.end, a1.vector1.end}
                if s0 != s1:
                    continue
                s0.remove(a0.vertex)
                s0.remove(a1.vertex)
                third_vertex = s0.pop()
                a2 = third_vertex.angle(a0.vertex, a1.vertex)
                a2_reason = self.context.angle_value_property(a2)
                if a2_reason is None or ar.reason.obsolete and a2_reason.reason.obsolete:
                    continue
                #a0 + a1 + a2 = 180
                #a0 + a1 = 180 - a2
                a1_value = divide(180 - a2_reason.degree, 1 + ar.value)
                a0_value = 180 - a2_reason.degree - a1_value
                comment = _comment('%s + %s + %s = 180º', a0, a1, a2)
                yield (AngleValueProperty(a0, a0_value), comment, [ar, a2_reason])
                yield (AngleValueProperty(a1, a1_value), comment, [ar, a2_reason])

            for ka in self.context.nondegenerate_angle_value_properties():
                if ka.reason.obsolete:
                    continue
                if ka.degree < 90:
                    yield (
                        AcuteAngleProperty(ka.angle),
                        _comment('0º < %sº < 90º', ka.degree),
                        [ka]
                    )
                elif ka.degree > 90:
                    yield (
                        ObtuseAngleProperty(ka.angle),
                        _comment('90º < %sº < 180º', ka.degree),
                        [ka]
                    )
                ang = ka.angle
                if ang.vertex and ka.degree >= 90:
                    yield (
                        AcuteAngleProperty(ang.vector0.end.angle(ang.vertex, ang.vector1.end)),
                        _comment('An angle of △ %s %s %s, another angle = %sº', *ang.points, ka.degree),
                        [ka]
                    )
                    yield (
                        AcuteAngleProperty(ang.vector1.end.angle(ang.vertex, ang.vector0.end)),
                        _comment('An angle of △ %s %s %s, another angle = %sº', *ang.points, ka.degree),
                        [ka]
                    )

            for aa in self.context.list(AcuteAngleProperty):
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
                                comment = _comment(
                                    '%s, %s, %s are collinear, %s is acute, and %s = %sº',
                                    pt, *vec0.points, base, angle, ka.degree
                                )
                                zero = base.vertex.angle(vec0.end, pt)
                                yield (AngleValueProperty(zero, 0), comment, [col, aa, ka])
                            break

            for oa in self.context.list(ObtuseAngleProperty):
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
                                comment = _comment(
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
                                comment = _comment(
                                    '%s, %s, %s are collinear, %s is acute, and %s > %s',
                                    pt, *vec0.points, base, angle, base
                                )
                                zero = base.vertex.angle(vec0.end, pt)
                                yield (AngleValueProperty(zero, 0), comment, [ka, col, ka2])
                            break

            for aa0, aa1 in itertools.combinations([a for a in self.context.list(AcuteAngleProperty) if a.angle.vertex], 2):
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
                    _comment('Both %s and %s are acute', aa0.angle, aa1.angle),
                    [aa0, aa1, col]
                )

            for iso in self.context.list(IsoscelesTriangleProperty):
                if iso.reason.obsolete:
                    continue
                yield (
                    AnglesRatioProperty(
                        iso.base.points[0].angle(iso.apex, iso.base.points[1]),
                        iso.base.points[1].angle(iso.apex, iso.base.points[0]),
                        1
                    ),
                    _comment('Base angles of isosceles △ %s %s %s', iso.apex, *iso.base.points),
                    [iso]
                )
                yield (
                    LengthRatioProperty(
                        iso.apex.segment(iso.base.points[0]),
                        iso.apex.segment(iso.base.points[1]),
                        1
                    ),
                    _comment('Legs of isosceles △ %s %s %s', iso.apex, *iso.base.points),
                    [iso]
                )

            for cs in [p for p in self.context.list(LengthRatioProperty) if p.value == 1]:
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

            for cs in [p for p in self.context.list(LengthRatioProperty) if p.value == 1]:
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

            for ar in same_triple_ratios:
                if ar.value != 1:
                    continue
                nc = self.context.not_collinear_property(*ar.angle0.points)
                if nc is None:
                    continue
                base = ar.angle0.vertex.segment(ar.angle1.vertex)
                apex = next(pt for pt in ar.angle0.points if pt not in base.points)
                yield (
                    IsoscelesTriangleProperty(apex, base),
                    'Congruent base angles',
                    [ar]
                )

            for equ in self.context.list(EquilateralTriangleProperty):
                ne = None
                for i in range(0, 3):
                    ne = self.context.not_equal_property(*side_of(equ.ABC, i).points)
                    if ne:
                        break
                if ne is not None and not equ.reason.obsolete and not ne.reason.obsolete:
                    for i in range(0, 3):
                        yield (
                            AngleValueProperty(angle_of(equ.ABC, i), 60),
                            _comment('Angle of non-degenerate equilateral △ %s %s %s', *equ.ABC),
                            [equ]
                        )
                if not equ.reason.obsolete:
                    for i, j in itertools.combinations(range(0, 3), 2):
                        yield (
                            LengthRatioProperty(side_of(equ.ABC, i), side_of(equ.ABC, j), 1),
                            _comment('Sides of equilateral △ %s %s %s', *equ.ABC),
                            [equ]
                        )

            for ct in self.context.list(CongruentTrianglesProperty):
                ncl = self.context.not_collinear_property(*ct.ABC)
                if ncl is None:
                    ncl = self.context.not_collinear_property(*ct.DEF)
                if ncl is None or ct.reason.obsolete and ncl.reason.obsolete:
                    continue
                for i in range(0, 3):
                    angle0 = angle_of(ct.ABC, i)
                    angle1 = angle_of(ct.DEF, i)
                    if angle0 != angle1:
                        yield (
                            AnglesRatioProperty(angle0, angle1, 1),
                            'Corresponding angles in congruent non-degenerate triangles',
                            [ct, ncl]
                        )

            for st in self.context.list(SimilarTrianglesProperty):
                ne0 = []
                ne1 = []
                for i in range(0, 3):
                    ne0.append(self.context.not_equal_property(*side_of(st.ABC, i).points))
                    ne1.append(self.context.not_equal_property(*side_of(st.DEF, i).points))

                for i in range(0, 3):
                    angle0 = angle_of(st.ABC, i)
                    angle1 = angle_of(st.DEF, i)
                    if angle0 == angle1:
                        continue
                    ne = []
                    for j in range(0, 3):
                        if i != j:
                            ne.append(ne0[j] if ne0[j] else ne1[j])
                    if ne[0] is None or ne[1] is None:
                        continue
                    if st.reason.obsolete and ne[0].reason.obsolete and ne[1].reason.obsolete:
                        continue
                    yield (
                        AnglesRatioProperty(angle0, angle1, 1),
                        'Corresponding angles in similar non-degenerate triangles',
                        [st, ne[0], ne[1]]
                    )

            for st in self.context.list(SimilarTrianglesProperty):
                st_is_too_old = st.reason.obsolete
                for i in range(0, 3):
                    cs = self.context.congruent_segments_property(side_of(st.ABC, i), side_of(st.DEF, i), True)
                    if cs is None:
                        continue
                    if st_is_too_old and cs.reason.obsolete:
                        break
                    yield (
                        CongruentTrianglesProperty(st.ABC, st.DEF),
                        'Similar triangles with congruent corresponding sides',
                        [st, cs]
                    )
                    break

            for segment0, segment1, comment, premises in self.context.length_ratios_equal_to_one():
                if all(prop.reason.obsolete for prop in premises):
                    continue
                yield (
                    LengthRatioProperty(segment0, segment1, 1),
                    comment,
                    premises
                )

            for st in self.context.list(SimilarTrianglesProperty):
                for i, j in itertools.combinations(range(0, 3), 2):
                    side00 = side_of(st.ABC, i)
                    side01 = side_of(st.ABC, j)
                    side10 = side_of(st.DEF, i)
                    side11 = side_of(st.DEF, j)
                    sides = [side00, side01, side10, side11]
                    neq_all = [self.context.not_equal_property(*side.points) for side in sides]
                    neq = [prop for prop in neq_all if prop is not None]
                    if len(neq) < 3 or st.reason.obsolete and all(ne.reason.obsolete for ne in neq):
                        continue

                    neq = list(set(neq[:3]))
                    for prop, side in zip(neq_all, sides):
                        if prop is None:
                            yield (
                                PointsCoincidenceProperty(*side.points, False),
                                'Similar triangles with non-zero sides',
                                [st] + neq
                            )

                    if side00 == side10:
                        yield (
                            LengthRatioProperty(side01, side11, 1),
                            'Ratios of sides in similar triangles',
                            [st] + neq
                        )
                        continue
                    if side01 == side11:
                        yield (
                            LengthRatioProperty(side00, side10, 1),
                            'Ratios of sides in similar triangles',
                            [st] + neq
                        )
                        continue
                    cs = self.context.congruent_segments_property(side00, side10, False)
                    if cs:
                        yield (
                            LengthRatioProperty(side01, side11, 1),
                            'Ratios of sides in similar triangles',
                            [st, cs] + neq
                        )
                        continue
                    cs = self.context.congruent_segments_property(side01, side11, False)
                    if cs:
                        yield (
                            LengthRatioProperty(side00, side10, 1),
                            'Ratios of sides in similar triangles',
                            [st, cs] + neq
                        )
                        continue
                    yield (
                        EqualLengthRatiosProperty(side00, side10, side01, side11),
                        'Ratios of sides in similar triangles',
                        [st] + neq
                    )

            for st in self.context.list(SimilarTrianglesProperty):
                st_is_too_old = st.reason.obsolete
                for i in range(0, 3):
                    lr, ratio = self.context.length_ratio_property_and_value(side_of(st.ABC, i), side_of(st.DEF, i), True)
                    if lr is None:
                        continue
                    if ratio == 1 or st_is_too_old and lr.reason.obsolete:
                        break
                    for j in [j for j in range(0, 3) if j != i]:
                        yield (
                            LengthRatioProperty(side_of(st.ABC, j), side_of(st.DEF, j), ratio),
                            'Ratios of sides in similar triangles',
                            [st, lr]
                        )
                    break

            for ct in self.context.list(CongruentTrianglesProperty):
                if ct.reason.obsolete:
                    continue
                for i in range(0, 3):
                    segment0 = side_of(ct.ABC, i)
                    segment1 = side_of(ct.DEF, i)
                    if segment0 != segment1:
                        yield (
                            LengthRatioProperty(segment0, segment1, 1),
                            'Corresponding sides in congruent triangles',
                            [ct]
                        )

            for ct in self.context.list(CongruentTrianglesProperty):
                if ct.reason.obsolete:
                    continue
                yield (
                    SimilarTrianglesProperty(ct.ABC, ct.DEF),
                    'Congruent triangles are similar',
                    [ct]
                )

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
                            _comment('%s = 180º', av.angle),
                            [av]
                        )
                else:
                    second_reason = self.context.angle_value_property(second)
                    if second_reason:
                        if av_is_too_old and second_reason.reason.obsolete:
                            continue
                        yield (
                            AngleValueProperty(third, 180 - av.degree - second_reason.degree),
                            _comment('%s + %s + %s = 180º', third, av.angle, second),
                            [av, second_reason]
                        )
                    else:
                        third_reason = self.context.angle_value_property(third)
                        if third_reason is None or av_is_too_old and third_reason.reason.obsolete:
                            continue
                        yield (
                            AngleValueProperty(second, 180 - av.degree - third_reason.degree),
                            _comment('%s + %s + %s = 180º', second, av.angle, third),
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
                        _comment('%sº - %sº', sa.degree, av0.degree),
                        [sa, av0]
                    )
                elif av1:
                    if sa.reason.obsolete and av1.reason.obsolete:
                        continue
                    yield (
                        AngleValueProperty(sa.angle0, sa.degree - av1.degree),
                        _comment('%sº - %sº', sa.degree, av1.degree),
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
                    _comment('%s + %s', ar.angle0, ar.angle1),
                    [ar, oppo]
                )

            for av in self.context.list(AngleValueProperty):
                if av.reason.obsolete or av.angle.vertex is None:
                    continue
                yield (
                    PointsCollinearityProperty(*av.angle.points, av.degree in (0, 180)),
                    '',#TODO: write comment
                    [av]
                )

            congruent_angles_groups = {}
            for ca in congruent_angles_with_vertex:
                key = frozenset([frozenset(ca.angle0.points), frozenset(ca.angle1.points)])
                lst = congruent_angles_groups.get(key)
                if lst:
                    lst.append(ca)
                else:
                    congruent_angles_groups[key] = [ca]

            for group in congruent_angles_groups.values():
                for ar0, ar1 in itertools.combinations(group, 2):
                    if ar1.angle0 in ar0.angle_set or ar1.angle1 in ar0.angle_set:
                        continue
                    ncl = self.context.not_collinear_property(*ca.angle0.points)
                    if ncl is None:
                        ncl = self.context.not_collinear_property(*ca.angle1.points)
                    if ncl is None or ar0.reason.obsolete and ar1.reason.obsolete and ncl.reason.obsolete:
                        continue
                    if ar0.angle0.points == ar1.angle0.points:
                        tr0 = [ar0.angle0.vertex, ar1.angle0.vertex]
                        tr1 = [ar0.angle1.vertex, ar1.angle1.vertex]
                    else:
                        tr0 = [ar0.angle0.vertex, ar1.angle1.vertex]
                        tr1 = [ar0.angle1.vertex, ar1.angle0.vertex]
                    tr0.append(next(p for p in ar0.angle0.points if p not in tr0))
                    tr1.append(next(p for p in ar0.angle1.points if p not in tr1))
                    yield (
                        SimilarTrianglesProperty(tr0, tr1),
                        'Two pairs of congruent angles, and the triangles are non-degenerate',
                        [ar0, ar1, ncl]
                    )

            def congruent_segments(seg0, seg1):
                if seg0 == seg1:
                    return True
                return self.context.congruent_segments_property(seg0, seg1, True)

            for ca in congruent_angles_with_vertex:
                ncl = self.context.not_collinear_property(*ca.angle0.points)
                if ncl:
                    if not ca.reason.obsolete or not ncl.reason.obsolete:
                        yield (
                            PointsCollinearityProperty(*ca.angle1.points, False),
                            'Transitivity',
                            [ca, ncl]
                        )
                else:
                    ncl = self.context.not_collinear_property(*ca.angle1.points)
                    if ncl and (not ca.reason.obsolete or not ncl.reason.obsolete):
                        yield (
                            PointsCollinearityProperty(*ca.angle0.points, False),
                            'Transitivity',
                            [ca, ncl]
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
                comment = _comment('%s ↑↑ %s', ang.vector0, ang.vector1)
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

            for ca in congruent_angles_with_vertex:
                ca_is_too_old = ca.reason.obsolete
                ang0 = ca.angle0
                ang1 = ca.angle1
                for vec0, vec1 in [(ang0.vector0, ang0.vector1), (ang0.vector1, ang0.vector0)]:
                    rsn0 = congruent_segments(vec0.as_segment, ang1.vector0.as_segment)
                    if rsn0 is None:
                        continue
                    rsn1 = congruent_segments(vec1.as_segment, ang1.vector1.as_segment)
                    if rsn1 is None:
                        continue
                    if ca_is_too_old and (rsn0 == True or rsn0.reason.obsolete) and (rsn1 == True or rsn1.reason.obsolete):
                        continue
                    if rsn0 == True:
                        comment = _comment('Common side %s, pair of congruent sides, and angle between the sides', vec0)
                        premises = [rsn1, ca]
                    elif rsn1 == True:
                        comment = _comment('Common side %s, pair of congruent sides, and angle between the sides', vec1)
                        premises = [rsn0, ca]
                    else:
                        comment = 'Two pairs of congruent sides, and angle between the sides'
                        premises = [rsn0, rsn1, ca]
                    yield (
                        CongruentTrianglesProperty(
                            (ang0.vertex, vec0.points[1], vec1.points[1]),
                            (ang1.vertex, ang1.vector0.end, ang1.vector1.end)
                        ), comment, premises
                    )

            for ca in congruent_angles_with_vertex:
                ca_is_too_old = ca.reason.obsolete
                ang0 = ca.angle0
                ang1 = ca.angle1
                for vec0, vec1 in [(ang0.vector0, ang0.vector1), (ang0.vector1, ang0.vector0)]:
                    elr = self.context.equal_length_ratios_property(vec0.as_segment, vec1.as_segment, ang1.vector0.as_segment, ang1.vector1.as_segment)
                    if elr is None or ca_is_too_old and elr.reason.obsolete:
                        continue
                    yield (
                        SimilarTrianglesProperty(
                            (ang0.vertex, vec0.end, vec1.end),
                            (ang1.vertex, ang1.vector0.end, ang1.vector1.end)
                        ),
                        'Two pairs of sides with the same ratio, and angle between the sides',
                        [elr, ca]
                    )

            for ca in congruent_angles_with_vertex:
                ca_is_too_old = ca.reason.obsolete
                ang0 = ca.angle0
                ang1 = ca.angle1
                for vec0, vec1 in [(ang0.vector0, ang0.vector1), (ang0.vector1, ang0.vector0)]:
                    rsn0, ratio0 = self.context.length_ratio_property_and_value(vec0.as_segment, ang1.vector0.as_segment, True)
                    if rsn0 is None:
                        continue
                    rsn1, ratio1 = self.context.length_ratio_property_and_value(vec1.as_segment, ang1.vector1.as_segment, True)
                    if rsn1 is None or ratio0 != ratio1:
                        continue
                    if ca_is_too_old and rsn0.reason.obsolete and rsn1.reason.obsolete:
                        continue
                    yield (
                        SimilarTrianglesProperty(
                            (ang0.vertex, vec0.end, vec1.end),
                            (ang1.vertex, ang1.vector0.end, ang1.vector1.end)
                        ),
                        'Two pairs of sides with the same ratio, and angle between the sides',
                        [rsn0, rsn1, ca]
                    )

            congruent_segments = [p for p in self.context.list(LengthRatioProperty) if p.value == 1]
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

            for cs in congruent_segments:
                common = common_point(cs.segment0, cs.segment1)
                if common is None:
                    continue
                pt0 = next(pt for pt in cs.segment0.points if pt != common)
                pt1 = next(pt for pt in cs.segment1.points if pt != common)
                ne = self.context.not_equal_property(pt0, pt1)
                if ne is None or cs.reason.obsolete and ne.reason.obsolete:
                    continue
                yield (
                    PointOnPerpendicularBisectorProperty(common, pt0.segment(pt1)),
                    _comment('%s is equidistant from %s and %s', common, pt0, pt1),
                    [cs, ne]
                )

            for cs0, cs1 in itertools.combinations(congruent_segments, 2):
                if cs0.reason.obsolete and cs1.reason.obsolete:
                    continue
                for seg0, seg1 in [(cs0.segment0, cs0.segment1), (cs0.segment1, cs0.segment0)]:
                    common0 = common_point(seg0, cs1.segment0)
                    if common0 is None:
                        continue
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
                            _comment('Common side %s, two pairs of congruent sides', third0),
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

            for ps0, ps1 in itertools.combinations(self.context.list(LengthRatioProperty), 2):
                if ps0.value == 1 or ps0.value != ps1.value:
                    continue
                ps_are_too_old = ps0.reason.obsolete and ps1.reason.obsolete
                common0 = common_point(ps0.segment0, ps1.segment0)
                if common0 is None:
                    continue
                common1 = common_point(ps0.segment1, ps1.segment1)
                if common1 is None:
                    continue
                third0 = other_point(ps0.segment0, common0).vector(other_point(ps1.segment0, common0))
                third1 = other_point(ps0.segment1, common1).vector(other_point(ps1.segment1, common1))
                ncl = self.context.not_collinear_property(common0, *third0.points)
                if ncl is None or ps_are_too_old and ncl.reason.obsolete:
                    continue
                ps2, value2 = self.context.length_ratio_property_and_value(third0.as_segment, third1.as_segment, True)
                if ps2 and value2 == ps0.value:
                    yield (
                        SimilarTrianglesProperty(
                            (common0, *third0.points), (common1, *third1.points)
                        ),
                        'Three pairs of sides with the same ratio',
                        [ps0, ps1, ps2, ncl]
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
                            _comment('%s is same line as %s', other.segment(pt), sos.segment),
                            [sos, col, ne]
                        )

            right_angles = [p for p in self.context.nondegenerate_angle_value_properties() if p.angle.vertex and p.degree == 90]
            for ra0, ra1 in itertools.combinations(right_angles, 2):
                vertex = ra0.angle.vertex
                if vertex != ra1.angle.vertex or ra0.reason.obsolete and ra1.reason.obsolete:
                    continue
                common = next((pt for pt in ra0.angle.endpoints if pt in ra1.angle.endpoints), None)
                if common is None:
                    continue
                first = next(pt for pt in ra0.angle.endpoints if pt != common)
                second = next(pt for pt in ra1.angle.endpoints if pt != common)
                yield (
                    PointsCollinearityProperty(vertex, first, second, True),
                    _comment('There is only one perpendicular to %s at point %s', vertex.segment(common), vertex),
                    [ra0, ra1]
                )

            for sos in self.context.list(SameOrOppositeSideProperty):
                if sos.reason.obsolete:
                    continue
                for pt in sos.points:
                    yield (
                        PointsCollinearityProperty(*sos.segment.points, pt, False),
                        '', #TODO: write comment
                        [sos]
                    )

            for sos in self.context.list(SameOrOppositeSideProperty):
                if sos.reason.obsolete:
                    continue
                cycle0 = Cycle(*sos.segment.points, sos.points[0])
                cycle1 = Cycle(*sos.segment.points, sos.points[1])
                if not sos.same:
                    cycle1 = cycle1.reversed
                yield (
                    SameCyclicOrderProperty(cycle0, cycle1),
                    '', #TODO: write comment
                    [sos]
                )

            for ca in congruent_angles_with_vertex:
                vertex = ca.angle0.vertex
                if vertex != ca.angle1.vertex:
                    continue
                pts0 = ca.angle0.endpoints
                pts1 = ca.angle1.endpoints
                if next((p for p in pts0 if p in pts1), None) is not None:
                    continue
                cycle0 = Cycle(vertex, *pts0)
                cycle1 = Cycle(vertex, *pts1)
                co = self.context.same_cyclic_order_property(cycle0, cycle1)
                if co:
                    if ca.reason.obsolete and co.reason.obsolete:
                        continue
                    yield (
                        AnglesRatioProperty(vertex.angle(pts0[0], pts1[0]), vertex.angle(pts0[1], pts1[1]), 1),
                        'Rotated', #TODO: better comment
                        [ca, co]
                    )
                else:
                    co = self.context.same_cyclic_order_property(cycle0, cycle1.reversed)
                    if co is None or ca.reason.obsolete and co.reason.obsolete:
                        continue
                    yield (
                        AnglesRatioProperty(vertex.angle(pts0[0], pts1[1]), vertex.angle(pts0[1], pts1[0]), 1),
                        'Rotated', #TODO: better comment
                        [ca, co]
                    )

            pb_dict = {}
            for ppb in self.context.list(PointOnPerpendicularBisectorProperty):
                lst = pb_dict.get(ppb.segment)
                if lst is None:
                    lst = [ppb]
                    pb_dict[ppb.segment] = lst
                else:
                    lst.append(ppb)

            for segment, lst in pb_dict.items():
                for ppb0, ppb1 in itertools.combinations(lst, 2):
                    ne = self.context.not_equal_property(ppb0.point, ppb1.point)
                    if ne is None or ppb0.reason.obsolete and ppb1.reason.obsolete and ne.reason.obsolete:
                        continue
                    line = ppb0.point.segment(ppb1.point)
                    yield (
                        SameOrOppositeSideProperty(line, *segment.points, False),
                        _comment('Line %s is the perpendicular bisector of segment %s', line, segment),
                        [ppb0, ppb1, ne]
                    )

                for triple in itertools.combinations(lst, 3):
                    if all(ppb.reason.obsolete for ppb in triple):
                        continue
                    yield (
                        PointsCollinearityProperty(*[ppb.point for ppb in triple], True),
                        _comment('Three points on the perpendicular bisector of %s', segment),
                        list(triple)
                    )

            for lr in self.context.list(LengthRatioProperty):
                ne = self.context.not_equal_property(*lr.segment0.points)
                if ne is None:
                    ne = self.context.not_equal_property(*lr.segment1.points)
                if ne is None or lr.reason.obsolete and ne.reason.obsolete:
                    continue
                yield (
                    RatioOfNonZeroLengthsProperty(lr.segment0, lr.segment1, lr.value),
                    lr.reason.comments,
                    [lr, ne]
                )

        for prop, comment in self.scene.enumerate_predefined_properties():
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
