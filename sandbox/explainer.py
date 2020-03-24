import itertools
import time

from .core import Constraint
from .property import *
from .propertyset import PropertySet
from .reason import Reason
from .scene import Scene
from .stats import Stats
from .util import _comment, divide, side_of, angle_of

class Explainer:
    def __init__(self, scene, properties):
        self.scene = scene
        self.context = PropertySet()
        self.__unexplained = list(properties)
        self.__explanation_time = None
        self.__iteration_step_count = -1

    def __reason(self, prop, comments, premises=None):
        if prop not in self.context:
            prop.reason = Reason(len(self.context), self.__iteration_step_count, comments, premises)
            self.context.add(prop)

    def __refresh_unexplained(self):
        self.__unexplained = [prop for prop in self.__unexplained if prop not in self.context]

    def explain(self):
        start = time.time()
        frozen = self.scene.is_frozen
        if not frozen:
            self.scene.freeze()
        self.__explain_all()
        if not frozen:
            self.scene.unfreeze()
        self.__explanation_time = time.time() - start

    def __congruent_segments_reason(self, seg0, seg1):
        reason = self.context.lengths_ratio_property(seg0, seg1)
        if reason and reason.ratio == 1:
            return reason
        return None

    def __angles_ratio_reasons(self, angle):
        reasons = self.context.list(AnglesRatioProperty, keys=[angle])
        reasons.sort(key=lambda prop: prop.penalty)
        return reasons

    def __explain_all(self):
        def base():
            for cnst in self.scene.constraints(Constraint.Kind.opposite_side):
                line = cnst.params[2]
                self.__reason(
                    SameOrOppositeSideProperty(line.point0.segment(line.point1), cnst.params[0], cnst.params[1], False),
                    cnst.comments
                )
            for cnst in self.scene.constraints(Constraint.Kind.same_side):
                line = cnst.params[2]
                self.__reason(
                    SameOrOppositeSideProperty(line.point0.segment(line.point1), cnst.params[0], cnst.params[1], True),
                    cnst.comments
                )
            for cnst in self.scene.constraints(Constraint.Kind.parallel_vectors):
                self.__reason(ParallelVectorsProperty(*cnst.params), cnst.comments)
            for cnst in self.scene.constraints(Constraint.Kind.angles_ratio):
                self.__reason(
                    AnglesRatioProperty(cnst.params[0], cnst.params[1], cnst.params[2]),
                    cnst.comments
                )

            for prop in list(self.__unexplained):
                if isinstance(prop, AngleValueProperty) and prop.degree == 90:
                    for cnst in self.scene.constraints(Constraint.Kind.perpendicular):
                        line0 = cnst.params[0]
                        line1 = cnst.params[1]
                        if prop.angle.vector0 in line0 and prop.angle.vector1 in line1:
                            self.__reason(prop, cnst.comments)
                            break
                        elif prop.angle.vector0 in line1 and prop.angle.vector1 in line0:
                            self.__reason(prop, cnst.comments)
                            break

        def iteration():
            def is_too_old(prop):
                return prop.reason.generation < self.__iteration_step_count - 1

            def _cs(coef):
                return '' if coef == 1 else ('%s ' % coef)

            for lr0, lr1 in itertools.combinations(self.context.list(LengthsRatioProperty), 2):
                if is_too_old(lr0) and is_too_old(lr1):
                    continue
                if lr0.segment0 == lr1.segment0:
                    coef = divide(lr1.ratio, lr0.ratio)
                    yield (
                        LengthsRatioProperty(lr0.segment1, lr1.segment1, coef),
                        _comment('|%s| = %s|%s| = %s|%s|', lr0.segment1, _cs(divide(1, lr0.ratio)), lr0.segment0, _cs(coef), lr1.segment1),
                        [lr0, lr1]
                    )
                    pass
                elif lr0.segment0 == lr1.segment1:
                    coef = lr1.ratio * lr0.ratio
                    yield (
                        LengthsRatioProperty(lr1.segment0, lr0.segment1, coef),
                        _comment('|%s| = %s|%s| = %s|%s|', lr1.segment0, _cs(lr1.ratio), lr0.segment0, _cs(coef), lr0.segment1),
                        [lr1, lr0]
                    )
                    pass
                elif lr0.segment1 == lr1.segment0:
                    coef = lr1.ratio * lr0.ratio
                    yield (
                        LengthsRatioProperty(lr0.segment0, lr1.segment1, coef),
                        _comment('|%s| = %s|%s| = %s|%s|', lr0.segment0, _cs(lr0.ratio), lr0.segment1, _cs(coef), lr1.segment1),
                        [lr0, lr1]
                    )
                    pass
                elif lr0.segment1 == lr1.segment1:
                    coef = divide(lr0.ratio, lr1.ratio)
                    yield (
                        LengthsRatioProperty(lr0.segment0, lr1.segment0, coef),
                        _comment('|%s| = %s|%s| = %s|%s|', lr0.segment0, _cs(lr0.ratio), lr0.segment1, _cs(coef), lr1.segment0),
                        [lr0, lr1]
                    )
                    pass

            processed = set()
            angle_ratios = list(self.context.list(AnglesRatioProperty))
            angle_ratios.sort(key=lambda prop: len(prop.angle0.points) + len(prop.angle1.points))
            for ar0 in angle_ratios:
                if is_too_old(ar0):
                    continue
                processed.add(ar0)
                angle_ratios0 = list(self.__angles_ratio_reasons(ar0.angle0))
                angle_ratios1 = list(self.__angles_ratio_reasons(ar0.angle1))
                tuples0 = [
                    ((ar.angle0, False, ar) \
                    if ar.angle1 == ar0.angle0 \
                    else (ar.angle1, True, ar))
                    for ar in angle_ratios0
                ]
                used0 = {p[0] for p in tuples0}
                tuples1 = [
                    ((ar.angle0, True, ar) if \
                    ar.angle1 == ar0.angle1 \
                    else (ar.angle1, False, ar)) \
                    for ar in angle_ratios1
                ]
                used1 = {p[0] for p in tuples1}
                tuples0 = [t for t in tuples0 if t[0] not in used1 and t[2] not in processed]
                for tup in tuples0:
                    ar1 = tup[2]
                    #TODO: report contradictions if in used and ratio is different
                    if tup[1]:
                        prop = AnglesRatioProperty(ar0.angle1, tup[0], divide(ar1.ratio, ar0.ratio))
                    else:
                        prop = AnglesRatioProperty(tup[0], ar0.angle1, ar0.ratio * ar1.ratio)
                    #TODO: better comment
                    yield (prop, 'Transitivity', [ar0, ar1])
                tuples1 = [t for t in tuples1 if t[0] not in used0 and t[2] not in processed]
                for tup in tuples1:
                    ar1 = tup[2]
                    if tup[1]:
                        prop = AnglesRatioProperty(ar0.angle0, tup[0], divide(ar0.ratio, ar1.ratio))
                    else:
                        prop = AnglesRatioProperty(ar0.angle0, tup[0], ar0.ratio * ar1.ratio)
                    #TODO: better comment
                    yield (prop, 'Transitivity', [ar0, ar1])

            for ar in [p for p in self.context.list(AnglesRatioProperty) if p.ratio == 1]:
                ar_is_too_old = is_too_old(ar)
                set0 = set()
                set1 = set()
                for sa in self.context.list(SumOfAnglesProperty, keys=[ar.angle0]):
                    if ar_is_too_old and is_too_old(sa):
                        continue
                    set0.add(sa.angle1 if sa.angle0 == ar.angle0 else sa.angle0)
                for sa in self.context.list(SumOfAnglesProperty, keys=[ar.angle1]):
                    if ar_is_too_old and is_too_old(sa):
                        continue
                    set1.add(sa.angle1 if sa.angle0 == ar.angle1 else sa.angle0)
                for angle in set0.difference(set1):
                    if ar.angle1 == angle:
                        #TODO: better comment
                        prop = AngleValueProperty(angle, divide(sa.degree, 2))
                    else:
                        prop = SumOfAnglesProperty(ar.angle1, angle, sa.degree)
                    yield (prop, 'Transitivity', [sa, ar])
                for angle in set1.difference(set0):
                    if ar.angle0 == angle:
                        #TODO: better comment
                        prop = AngleValueProperty(angle, divide(sa.degree, 2))
                    else:
                        prop = SumOfAnglesProperty(ar.angle0, angle, sa.degree)
                    yield (prop, 'Transitivity', [sa, ar])

            for ncl in [p for p in self.context.list(PointsCollinearityProperty) if not p.collinear]:
                ncl_is_too_old = is_too_old(ncl)
                if not ncl_is_too_old:
                    #TODO: better comments
                    yield (PointsCoincidenceProperty(ncl.points[0], ncl.points[1], False), str(ncl), [ncl])
                    yield (PointsCoincidenceProperty(ncl.points[0], ncl.points[2], False), str(ncl), [ncl])
                    yield (PointsCoincidenceProperty(ncl.points[1], ncl.points[2], False), str(ncl), [ncl])

                for segment, pt_ncl in [(side_of(ncl.points, i), ncl.points[i]) for i in range(0, 3)]:
                    for col in [p for p in self.context.list(PointsCollinearityProperty, [segment]) if p.collinear]:
                        reasons_are_too_old = ncl_is_too_old and is_too_old(col)
                        pt_col = next(pt for pt in col.points if pt not in segment.points)
                        if not reasons_are_too_old:
                            yield (PointsCoincidenceProperty(pt_col, pt_ncl, False), [], [ncl, col])
                        for common in segment.points:
                            ne = self.context.not_equal_property(common, pt_col)
                            if ne is None or reasons_are_too_old and is_too_old(ne):
                                continue
                            yield (
                                PointsCollinearityProperty(common, pt_col, pt_ncl, False),
                                _comment(
                                    '%s and %s lie on the line %s %s, %s does not',
                                    common, pt_col, *segment.points, pt_ncl
                                ),
                                [ncl, col, ne]
                            )

            for cl0, cl1 in itertools.combinations([p for p in self.context.list(PointsCollinearityProperty) if p.collinear], 2):
                if len(cl0.point_set.union(cl1.point_set)) != 4:
                    continue
                pt0 = next(pt for pt in cl0.points if pt not in cl1.point_set)
                pt1 = next(pt for pt in cl1.points if pt not in cl0.point_set)
                others = [pt for pt in cl0.points if pt != pt0]
                ncl_pt = others[0]
                ncl = self.context.collinearity_property(pt0, pt1, ncl_pt)
                if ncl is None:
                    ncl_pt = others[1]
                    ncl = self.context.collinearity_property(pt0, pt1, ncl_pt)
                if ncl is None or ncl.collinear or is_too_old(cl0) and is_too_old(cl1) and is_too_old(ncl):
                    continue
                yield (
                    PointsCoincidenceProperty(*others, True),
                    _comment('%s and %s belong to two different lines %s and %s', *others, pt0.segment(ncl_pt), pt1.segment(ncl_pt)),
                    [cl0, cl1, ncl]
                )

            for cs in self.context.list(LengthsRatioProperty):
                vec0 = cs.segment0
                vec1 = cs.segment1

                ne0 = self.context.not_equal_property(*vec0.points)
                ne1 = self.context.not_equal_property(*vec1.points)
                if ne0 is not None and ne1 is None:
                    yield (PointsCoincidenceProperty(*vec1.points, False), _comment('Otherwise, %s = %s', *vec0.points), [cs, ne0])
                elif ne1 is not None and ne0 is None:
                    yield (PointsCoincidenceProperty(*vec0.points, False), _comment('Otherwise, %s = %s', *vec1.points), [cs, ne1])
                elif ne0 is None and ne1 is None:
                    ne = None
                    if vec0.points[0] == vec1.points[0]:
                        ne = self.context.not_equal_property(vec0.points[1], vec1.points[1])
                        mid = vec0.points[0]
                    elif vec0.points[0] == vec1.points[1]:
                        ne = self.context.not_equal_property(vec0.points[1], vec1.points[0])
                        mid = vec0.points[0]
                    elif vec0.points[1] == vec1.points[0]:
                        ne = self.context.not_equal_property(vec0.points[0], vec1.points[1])
                        mid = vec0.points[1]
                    elif vec0.points[1] == vec1.points[1]:
                        ne = self.context.not_equal_property(vec0.points[0], vec1.points[0])
                        mid = vec0.points[1]
                    if ne:
                        yield (PointsCoincidenceProperty(*vec0.points, False), _comment('Otherwise, %s = %s = %s', ne.points[0], mid, ne.points[1]), [cs, ne])
                        yield (PointsCoincidenceProperty(*vec1.points, False), _comment('Otherwise, %s = %s = %s', ne.points[1], mid, ne.points[0]), [cs, ne])

            for pv in self.context.list(ParallelVectorsProperty):
                vec0 = pv.vector0
                vec1 = pv.vector1
                ne0 = self.context.not_equal_property(*vec0.points)
                ne1 = self.context.not_equal_property(*vec1.points)
                if ne0 is not None and ne1 is not None:
                    if is_too_old(pv) and is_too_old(ne0) and is_too_old(ne1):
                        continue
                    for prop in AngleValueProperty.generate(vec0.angle(vec1), 0):
                        yield (prop, [], [pv, ne0, ne1])

            for prop in [p for p in self.context.list(SameOrOppositeSideProperty) if p.same]:
                prop_is_too_old = is_too_old(prop)
                segment = prop.points[0].segment(prop.points[1])
                for col in [p for p in self.context.list(PointsCollinearityProperty, [segment]) if p.collinear]:
                    pt = next(p for p in col.points if p not in prop.points)
                    value = self.context.angle_value_property(pt.angle(*prop.points))
                    if not value or value.degree != 180 or prop_is_too_old and is_too_old(value):
                        continue
                    for old in prop.points:
                        yield (
                            SameOrOppositeSideProperty(prop.segment, old, pt, True),
                            _comment('The segment %s does not cross line %s', segment, prop.segment),
                            [prop, value]
                        )

            for prop in self.context.list(SameOrOppositeSideProperty):
                pt0 = prop.points[0]
                pt1 = prop.points[1]
                crossing, reasons = self.context.intersection_of_lines(prop.segment, pt0.segment(pt1))
                if not crossing:
                    continue
                if is_too_old(prop) and all(is_too_old(p) for p in reasons):
                    continue
                if prop.same:
                    yield (
                        AngleValueProperty(crossing.angle(pt0, pt1), 0),
                        _comment('%s is an intersection of lines %s and %s', crossing, pt0.segment(pt1), prop.segment),
                        [prop] + reasons
                    )
                else:
                    yield (
                        AngleValueProperty(crossing.angle(pt0, pt1), 180),
                        _comment('%s is an intersection of segment %s and line %s', crossing, pt0.segment(pt1), prop.segment),
                        [prop] + reasons
                    )

            for av in [av for av in self.context.list(AngleValueProperty) if av.angle.vertex and av.degree == 180]:
                av_is_too_old = is_too_old(av)
                ang = av.angle
                for ne in self.context.list(PointsCoincidenceProperty, [ang.vertex]):
                    if ne.coincident or av_is_too_old and is_too_old(ne):
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
                if is_too_old(av0) and is_too_old(av1):
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
                av_is_too_old = is_too_old(av)
                ang = av.angle
                for ne in self.context.list(PointsCoincidenceProperty, [ang.vertex]):
                    if ne.coincident or av_is_too_old and is_too_old(ne):
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
                if is_too_old(av0) and is_too_old(av1):
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
                so_is_too_old = is_too_old(so)
                lp0 = so.segment.points[0]
                lp1 = so.segment.points[1]
                ne = self.context.not_equal_property(lp0, lp1)
                if ne is None:
                    continue
                reasons_are_too_old = so_is_too_old and is_too_old(ne)
                for pt0, pt1 in [so.points, reversed(so.points)]:
                    if so.same:
                        sum_reason = self.context[SumOfAnglesProperty(lp0.angle(pt0, lp1), lp1.angle(pt1, lp0), 180)]
                        if sum_reason is None or reasons_are_too_old and is_too_old(sum_reason):
                            continue
                        if sum_reason.degree == 180:
                            for prop in AngleValueProperty.generate(lp0.vector(pt0).angle(lp1.vector(pt1)), 0):
                                yield (prop, 'Zigzag', [so, sum_reason, ne])
                    else:
                        ratio_reason = self.context.angles_ratio_property(lp0.angle(pt0, lp1), lp1.angle(pt1, lp0))
                        if ratio_reason is None or reasons_are_too_old and is_too_old(ratio_reason):
                            continue
                        if ratio_reason.ratio == 1:
                            for prop in AngleValueProperty.generate(lp0.vector(pt0).angle(pt1.vector(lp1)), 0):
                                yield (prop, 'Zigzag', [so, ratio_reason, ne])

            for zero in [av for av in self.context.list(AngleValueProperty) if av.degree == 0]:
                zero_is_too_old = is_too_old(zero)
                for ne in self.context.list(PointsCoincidenceProperty):
                    if ne.coincident or zero_is_too_old and is_too_old(ne):
                        continue
                    vec = ne.points[0].vector(ne.points[1])
                    if vec.as_segment in [zero.angle.vector0.as_segment, zero.angle.vector1.as_segment]:
                        continue
                    for ngl0, cmpl0 in good_angles(vec.angle(zero.angle.vector0)):
                        for ngl1, cmpl1 in good_angles(vec.angle(zero.angle.vector1)):
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
                A = pia.angle.vertex
                if A is None:
                    continue
                B = pia.angle.vector0.end
                C = pia.angle.vector1.end
                D = pia.point
                AD = A.segment(D)
                BC = B.segment(C)
                X, reasons = self.context.intersection_of_lines(AD, BC)
                if X is None or X in (A, B, C, D):
                    continue
                if is_too_old(pia) and all(is_too_old(p) for p in reasons):
                    continue

                comment = _comment('%s is intersection of ray [%s %s) and segment [%s %s]', X, A, D, B, C)
                yield (AngleValueProperty(A.angle(D, X), 0), [comment], [pia] + reasons)
                yield (AngleValueProperty(B.angle(C, X), 0), [comment], [pia] + reasons)
                yield (AngleValueProperty(C.angle(B, X), 0), [comment], [pia] + reasons)
                yield (AngleValueProperty(X.angle(B, C), 180), [comment], [pia] + reasons)

            for pia in self.context.list(PointInsideAngleProperty):
                if is_too_old(pia):
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

                vertex, reasons = self.context.intersection_of_lines(ss0.segment, ss1.segment)
                if vertex is None:
                    continue

                reasons = [ss0, ss1, ncl] + reasons
                if all(is_too_old(p) for p in reasons):
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

                if len({vertex, common, other0, other1}) < 4:
                    continue

                yield (
                    PointInsideAngleProperty(common, vertex.angle(other0, other1)),
                    '', #TODO: write comment
                    reasons
                )

            for ar in self.context.list(AnglesRatioProperty):
                a0 = ar.angle0
                a1 = ar.angle1
                if a0.vertex is None or a0.vertex != a1.vertex:
                    continue
                if a0.vector1.end == a1.vector0.end:
                    angle = a0.vertex.angle(a0.vector0.end, a1.vector1.end)
                    common_point = a0.vector1.end
                elif a0.vector0.end == a1.vector1.end:
                    angle = a0.vertex.angle(a1.vector0.end, a0.vector1.end)
                    common_point = a0.vector0.end
                elif a0.vector0.end == a1.vector0.end:
                    angle = a0.vertex.angle(a1.vector1.end, a0.vector1.end)
                    common_point = a0.vector0.end
                elif a0.vector1.end == a1.vector1.end:
                    angle = a0.vertex.angle(a0.vector0.end, a1.vector0.end)
                    common_point = a0.vector1.end
                else:
                    continue
                inside_angle_reason = \
                    self.context[PointInsideAngleProperty(common_point, angle)]
                if inside_angle_reason is None:
                    #TODO: consider angle difference
                    continue
                sum_reason = self.context.angle_value_property(angle)
                if sum_reason is None or is_too_old(ar) and is_too_old(sum_reason) and is_too_old(inside_angle_reason):
                    continue
                value = sum_reason.degree
                second = divide(value, 1 + ar.ratio)
                first = value - second
                #TODO: write comments
                yield (AngleValueProperty(a0, first), [], [ar, sum_reason, inside_angle_reason])
                yield (AngleValueProperty(a1, second), [], [ar, sum_reason, inside_angle_reason])

            angle_values = [prop for prop in self.context.list(AngleValueProperty) \
                if prop.angle.vertex is not None]

            for av in [av for av in angle_values if av.degree == 0]:
                av_is_too_old = is_too_old(av)
                vertex = av.angle.vertex
                pt0 = av.angle.vector0.end
                pt1 = av.angle.vector1.end
                for vec in (av.angle.vector0, av.angle.vector1):
                    for nc in self.context.list(PointsCollinearityProperty, [vec.as_segment]):
                        if nc.collinear or av_is_too_old and is_too_old(nc):
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
                av_is_too_old = is_too_old(av)
                segment = av.angle.vector0.end.segment(av.angle.vector1.end)
                for ncl in self.context.list(PointsCollinearityProperty, [segment]):
                    if ncl.collinear or av_is_too_old and is_too_old(ncl):
                        continue
                    vertex = next(pt for pt in ncl.points if pt not in segment.points)
                    angle = vertex.angle(*segment.points)
                    yield (
                        PointInsideAngleProperty(av.angle.vertex, angle),
                        _comment('%s lies inside a segment with endoints on sides of %s', av.angle.vertex, angle),
                        [av, ncl]
                    )
                    yield (
                        SameOrOppositeSideProperty(av.angle.vertex.segment(vertex), *segment.points, False),
                        _comment('%s lies inside segment %s, and %s is not on the line %s', av.angle.vertex, segment, vertex, segment),
                        [av, ncl]
                    )

            for sos0, sos1 in itertools.combinations(self.context.list(SameOrOppositeSideProperty), 2):
                if is_too_old(sos0) and is_too_old(sos1):
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

            for ar in self.context.list(AnglesRatioProperty):
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
                if a2_reason is None or is_too_old(ar) and is_too_old(a2_reason):
                    continue
                #a0 + a1 + a2 = 180
                #a0 + a1 = 180 - a2
                a1_value = divide(180 - a2_reason.degree, 1 + ar.ratio)
                a0_value = 180 - a2_reason.degree - a1_value
                comment = _comment('%s + %s + %s = 180º', a0, a1, a2)
                yield (AngleValueProperty(a0, a0_value), comment, [ar, a2_reason])
                yield (AngleValueProperty(a1, a1_value), comment, [ar, a2_reason])

            for ka in self.context.list(AngleValueProperty):
                base = ka.angle
                if ka.degree == 0 or ka.degree >= 90 or base.vertex is None:
                    continue
                ka_is_too_old = is_too_old(ka)
                for vec0, vec1 in [(base.vector0, base.vector1), (base.vector1, base.vector0)]:
                    for col in [p for p in self.context.list(PointsCollinearityProperty, [vec0.as_segment]) if p.collinear]:
                        reasons_are_too_old = ka_is_too_old and is_too_old(col)
                        pt = next(pt for pt in col.points if pt not in vec0.points)
                        for angle in [pt.angle(vec1.end, p) for p in vec0.points]:
                            ka2 = self.context.angle_value_property(angle)
                            if ka2 is None or reasons_are_too_old and is_too_old(ka2):
                                continue
                            if ka2.degree > ka.degree:
                                comment = _comment(
                                    '%s, %s, %s are collinear, %s is acute, and %s > %s',
                                    pt, *vec0.points, base, angle, base
                                )
                                zero = base.vertex.angle(vec0.end, pt)
                                yield (AngleValueProperty(zero, 0), comment, [ka, col, ka2])
                            break

            for iso in self.context.list(IsoscelesTriangleProperty):
                if is_too_old(iso):
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
                    LengthsRatioProperty(
                        iso.apex.segment(iso.base.points[0]),
                        iso.apex.segment(iso.base.points[1]),
                        1
                    ),
                    _comment('Legs of isosceles △ %s %s %s', iso.apex, *iso.base.points),
                    [iso]
                )

            for cs in [p for p in self.context.list(LengthsRatioProperty) if p.ratio == 1]:
                if cs.segment1.points[0] in cs.segment0.points:
                    apex = cs.segment1.points[0]
                    base0 = cs.segment1.points[1]
                elif cs.segment1.points[1] in cs.segment0.points:
                    apex = cs.segment1.points[1]
                    base0 = cs.segment1.points[0]
                else:
                    continue
                base1 = cs.segment0.points[0] if apex == cs.segment0.points[1] else cs.segment0.points[1]
                nc = self.context.not_collinear_property(apex, base0, base1)
                if nc:
                    yield (
                        IsoscelesTriangleProperty(apex, base0.segment(base1)),
                        'Congruent legs',
                        [cs, nc]
                    )

            for ar in self.context.list(AnglesRatioProperty):
                if ar.ratio != 1:
                    continue
                if len(ar.angle0.points) != 3 or ar.angle0.points != ar.angle1.points:
                    continue
                nc = self.context.not_collinear_property(*ar.angle0.points)
                if nc is None:
                    continue
                base = ar.angle0.vertex.segment(ar.angle1.vertex)
                apex = next(pt for pt in ar.angle0.points if pt not in base.points)
                yield (
                    IsoscelesTriangleProperty(apex, base),
                    'Congruent base angles',
                    [cs]
                )

            for iso in self.context.list(IsoscelesTriangleProperty):
                eq = self.__congruent_segments_reason(iso.base, iso.apex.segment(iso.base.points[0]))
                if eq is None or is_too_old(iso) and is_too_old(eq):
                    continue
                yield (
                    EquilateralTriangleProperty((iso.apex, *iso.base.points)),
                    _comment('Isosceles with leg equal to the base'),
                    [iso, eq]
                )

            for equ in self.context.list(EquilateralTriangleProperty):
                if is_too_old(equ):
                    continue
                for i in range(0, 3):
                    yield (
                        AngleValueProperty(angle_of(equ.ABC, i), 60),
                        'Angle of an equilateral triangle',
                        [equ]
                    )

            for ar in self.context.list(AnglesRatioProperty):
                ar_is_too_old = is_too_old(ar)
                value = self.context.angle_value_property(ar.angle0)
                if value:
                    if ar_is_too_old and is_too_old(value):
                        continue
                    if ar.ratio == 1:
                        comment = _comment('%s = %s = %sº', ar.angle1, ar.angle0, value.degree)
                    else:
                        comment = _comment('%s = %s / %s = %sº / %s', ar.angle1, ar.angle0, ar.ratio, value.degree, ar.ratio)
                    yield (
                        AngleValueProperty(ar.angle1, divide(value.degree, ar.ratio)),
                        comment, [ar, value]
                    )
                else:
                    value = self.context.angle_value_property(ar.angle1)
                    if value is None or ar_is_too_old and is_too_old(value):
                        continue
                    if ar.ratio == 1:
                        comment = _comment('%s = %s = %sº', ar.angle0, ar.angle1, value.degree)
                    else:
                        comment = _comment('%s = %s * %s = %sº * %s', ar.angle0, ar.angle1, ar.ratio, value.degree, ar.ratio)
                    yield (
                        AngleValueProperty(ar.angle0, value.degree * ar.ratio),
                        comment, [ar, value]
                    )

            for st in self.context.list(SimilarTrianglesProperty):
                if is_too_old(st):
                    continue
                for i in range(0, 3):
                    angle0 = angle_of(st.ABC, i)
                    angle1 = angle_of(st.DEF, i)
                    if angle0 != angle1:
                        yield (
                            AnglesRatioProperty(angle0, angle1, 1),
                            'Corresponding angles in similar triangles',
                            [st]
                        )

            for st in self.context.list(SimilarTrianglesProperty):
                for i in range(0, 3):
                    cs = self.__congruent_segments_reason(side_of(st.ABC, i), side_of(st.DEF, i))
                    if cs:
                        yield (
                            CongruentTrianglesProperty(st.ABC, st.DEF),
                            'Similar triangles with congruent corresponding sides',
                            [st, cs]
                        )

            for ct in self.context.list(CongruentTrianglesProperty):
                if is_too_old(ct):
                    continue
                for i in range(0, 3):
                    segment0 = side_of(ct.ABC, i)
                    segment1 = side_of(ct.DEF, i)
                    if segment0 != segment1:
                        yield (
                            LengthsRatioProperty(segment0, segment1, 1),
                            'Corresponding sides in congruent triangles',
                            [ct]
                        )

            for ct in self.context.list(CongruentTrianglesProperty):
                if is_too_old(ct):
                    continue
                yield (
                    SimilarTrianglesProperty(ct.ABC, ct.DEF),
                    'Congruent triangles are similar',
                    [ct]
                )

            for av in self.context.list(AngleValueProperty):
                if av.angle.vertex is None:
                    continue
                av_is_too_old = is_too_old(av)

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
                        if av_is_too_old and is_too_old(second_reason):
                            continue
                        yield (
                            AngleValueProperty(third, 180 - av.degree - second_reason.degree),
                            _comment('%s + %s + %s = 180º', third, av.angle, second),
                            [av, second_reason]
                        )
                    else:
                        third_reason = self.context.angle_value_property(third)
                        if third_reason is None or av_is_too_old and is_too_old(third_reason):
                            continue
                        yield (
                            AngleValueProperty(second, 180 - av.degree - third_reason.degree),
                            _comment('%s + %s + %s = 180º', second, av.angle, third),
                            [av, third_reason]
                        )

            for av0, av1 in itertools.combinations( \
                [av for av in self.context.list(AngleValueProperty) if av.degree not in (0, 180)], 2):
                if is_too_old(av0) and is_too_old(av1):
                    continue
                if av0.degree == av1.degree:
                    comment = _comment('Both angle values = %sº', av0.degree)
                else:
                    comment = _comment('%s = %sº, %s = %sº', av0.angle, av0.degree, av1.angle, av1.degree)
                yield (
                    AnglesRatioProperty(av0.angle, av1.angle, divide(av0.degree, av1.degree)),
                    comment,
                    [av0, av1]
                )

            for sa in self.context.list(SumOfAnglesProperty):
                sa_is_too_old = is_too_old(sa)
                av = self.context.angle_value_property(sa.angle0)
                if av:
                    if sa_is_too_old and is_too_old(av):
                        continue
                    yield (
                        AngleValueProperty(sa.angle1, sa.degree - av.degree),
                        _comment('%sº - %sº', sa.degree, av.degree),
                        [sa, av]
                    )
                else:
                    av = self.context.angle_value_property(sa.angle1)
                    if av is None or sa_is_too_old and is_too_old(av):
                        continue
                    yield (
                        AngleValueProperty(sa.angle0, sa.degree - av.degree),
                        _comment('%sº - %sº', sa.degree, av.degree),
                        [sa, av]
                    )

            for ar in [p for p in self.context.list(SumOfAnglesProperty) if p.angle0.vertex is not None and p.angle0.vertex == p.angle1.vertex and p.degree == 180]:
                common = next((pt for pt in ar.angle0.endpoints if pt in ar.angle1.endpoints), None)
                if common is None:
                    continue
                pt0 = next(pt for pt in ar.angle0.endpoints if pt not in ar.angle1.endpoints)
                pt1 = next(pt for pt in ar.angle1.endpoints if pt not in ar.angle0.endpoints)
                oppo = self.context[SameOrOppositeSideProperty(ar.angle0.vertex.segment(common), pt0, pt1, False)]
                if not oppo or oppo.same or is_too_old(ar) and is_too_old(oppo):
                    continue
                yield (
                    AngleValueProperty(ar.angle0.vertex.angle(pt0, pt1), 180),
                    _comment('%s + %s', ar.angle0, ar.angle1),
                    [ar, oppo]
                )

            for av in self.context.list(AngleValueProperty):
                if is_too_old(av) or av.angle.vertex is None:
                    continue
                yield (
                    PointsCollinearityProperty(*av.angle.points, av.degree in (0, 180)),
                    '',#TODO: write comment
                    [av]
                )

            congruent_angles = [ar for ar in self.context.list(AnglesRatioProperty) if ar.ratio == 1 and ar.angle0.vertex and ar.angle1.vertex]
            def pts(prop):
                return {prop.angle0.points, prop.angle1.points}

            processed = set()
            for ar0 in congruent_angles:
                if is_too_old(ar0):
                    continue
                processed.add(ar0)
                pts0 = pts(ar0)
                angles0 = {ar0.angle0, ar0.angle1}
                for ar1 in [ar for ar in congruent_angles if ar not in processed and pts(ar) == pts0]:
                    if ar1.angle0 in angles0 or ar1.angle1 in angles0:
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
                        'Two pairs of congruent angles',
                        [ar0, ar1]
                    )

            def congruent_segments(seg0, seg1):
                if seg0 == seg1:
                    return True
                return self.__congruent_segments_reason(seg0, seg1)

            for ca in congruent_angles:
                ncl = self.context.not_collinear_property(*ca.angle0.points)
                if ncl:
                    if not is_too_old(ca) or not is_too_old(ncl):
                        yield (
                            PointsCollinearityProperty(*ca.angle1.points, False),
                            'Transitivity',
                            [ca, ncl]
                        )
                else:
                    ncl = self.context.not_collinear_property(*ca.angle1.points)
                    if ncl and (not is_too_old(ca) or not is_too_old(ncl)):
                        yield (
                            PointsCollinearityProperty(*ca.angle0.points, False),
                            'Transitivity',
                            [ca, ncl]
                        )

            for zero in [p for p in self.context.list(AngleValueProperty) if p.angle.vertex is None and p.degree == 0]:
                zero_is_too_old = is_too_old(zero)
                ang = zero.angle

                for vec0, vec1 in [(ang.vector0, ang.vector1), (ang.vector1, ang.vector0)]:
                    for i, j in [(0, 1), (1, 0)]:
                        ncl = self.context.not_collinear_property(*vec0.points, vec1.points[i])
                        if ncl is None:
                            continue
                        ne = self.context.not_equal_property(*vec1.points)
                        if ne is None:
                            continue
                        if zero_is_too_old and is_too_old(ncl) and is_too_old(ne):
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
                if is_too_old(zero) and is_too_old(ncl) and is_too_old(ne):
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

            for ca in congruent_angles:
                ncl = self.context.not_collinear_property(*ca.angle0.points)
                if ncl is None:
                    continue
                ca_is_too_old = is_too_old(ca) and is_too_old(ncl)
                ang0 = ca.angle0
                ang1 = ca.angle1
                for seg0, seg1 in [(ang0.vector0.as_segment, ang0.vector1.as_segment), (ang0.vector1.as_segment, ang0.vector0.as_segment)]:
                    rsn0 = congruent_segments(seg0, ang1.vector0.as_segment)
                    if rsn0 is None:
                        continue
                    rsn1 = congruent_segments(seg1, ang1.vector1.as_segment)
                    if rsn1 is None:
                        continue
                    if ca_is_too_old and (rsn0 == True or is_too_old(rsn0)) and (rsn1 == True or is_too_old(rsn1)):
                        continue
                    if rsn0 == True:
                        comment = _comment('Common side %s, pair of congruent sides, and angle between the sides', seg0)
                        premises = [rsn1, ca, ncl]
                    elif rsn1 == True:
                        comment = _comment('Common side %s, pair of congruent sides, and angle between the sides', seg1)
                        premises = [rsn0, ca, ncl]
                    else:
                        comment = 'Two pairs of congruent sides, and angle between the sides'
                        premises = [rsn0, rsn1, ca, ncl]
                    yield (
                        CongruentTrianglesProperty(
                            (ang0.vertex, seg0.points[1], seg1.points[1]),
                            (ang1.vertex, ang1.vector0.end, ang1.vector1.end)
                        ), comment, premises
                    )

            congruent_segments = [p for p in self.context.list(LengthsRatioProperty) if p.ratio == 1]
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
                cs_are_too_old = is_too_old(cs0) and is_too_old(cs1)
                for seg0, seg1 in [(cs0.segment0, cs0.segment1), (cs0.segment1, cs0.segment0)]:
                    common0 = common_point(seg0, cs1.segment0)
                    if common0 is None:
                        continue
                    common1 = common_point(seg1, cs1.segment1)
                    if common1 is None:
                        continue
                    third0 = other_point(seg0, common0).segment(other_point(cs1.segment0, common0))
                    third1 = other_point(seg1, common1).segment(other_point(cs1.segment1, common1))
                    ncl = self.context.not_collinear_property(common0, *third0.points)
                    if ncl is None or cs_are_too_old and is_too_old(ncl):
                        continue
                    prop = CongruentTrianglesProperty(
                        (common0, *third0.points), (common1, *third1.points)
                    )
                    if third0 == third1:
                        yield (
                            prop,
                            _comment('Common side %s, two pairs of congruent sides', third0),
                            [cs0, cs1, ncl]
                        )
                    else:
                        cs2 = self.__congruent_segments_reason(third0, third1)
                        if cs2:
                            yield (
                                prop,
                                'Three pairs of congruent sides',
                                [cs0, cs1, cs2, ncl]
                            )

            for oppo1 in [p for p in self.context.list(SameOrOppositeSideProperty) if not p.same]:
                oppo1_is_too_old = is_too_old(oppo1)
                for vertex, pt1 in [oppo1.segment.points, reversed(oppo1.segment.points)]:
                    for pt0, pt2 in [oppo1.points, reversed(oppo1.points)]:
                        for oppo2 in [p for p in self.context.list(SameOrOppositeSideProperty, [vertex.segment(pt2)]) if not p.same]:
                            if pt1 not in oppo2.points:
                                continue
                            oppos_are_too_old = oppo1_is_too_old and is_too_old(oppo2)
                            pt3 = next(p for p in oppo2.points if p != pt1)
                            angles1 = (vertex.angle(pt0, pt1), vertex.angle(pt2, pt3))
                            angles2 = (vertex.angle(pt0, pt2), vertex.angle(pt1, pt3))
                            ar = self.context.angles_ratio_property(*angles1)
                            if ar:
                                if ar.ratio != 1 or oppos_are_too_old and is_too_old(ar):
                                    continue
                                yield (
                                    AnglesRatioProperty(*angles2, 1),
                                    '',
                                    [oppo1, oppo2, ar]
                                )
                            else:
                                ar = self.context.angles_ratio_property(*angles2)
                                if ar is None or ar.ratio != 1 or oppos_are_too_old and is_too_old(ar):
                                    continue
                                yield (
                                    AnglesRatioProperty(*angles1, 1),
                                    '',
                                    [oppo1, oppo2, ar]
                                )

            for sos in self.context.list(SameOrOppositeSideProperty):
                for col in [p for p in self.context.list(PointsCollinearityProperty) if p.collinear]:
                    if sos.segment.points[0] not in col.points:
                        continue
                    if sos.segment.points[1] not in col.points:
                        continue
                    too_old = is_too_old(sos) and is_too_old(col)
                    other = next(pt for pt in col.points if pt not in sos.segment.points)
                    for pt in sos.segment.points:
                        ne = self.context.not_equal_property(other, pt)
                        if ne is None or too_old and is_too_old(ne):
                            continue
                        yield (
                            SameOrOppositeSideProperty(other.segment(pt), *sos.points, sos.same),
                            _comment('%s is same line as %s', other.segment(pt), sos.segment),
                            [sos, col, ne]
                        )

            right_angles = [p for p in self.context.list(AngleValueProperty) if p.angle.vertex and p.degree == 90]
            for ra0, ra1 in itertools.combinations(right_angles, 2):
                vertex = ra0.angle.vertex
                if vertex != ra1.angle.vertex or is_too_old(ra0) and is_too_old(ra1):
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

        for prop, comment in self.scene.enumerate_predefined_properties():
            self.__reason(prop, comment, [])

        base()
        self.__iteration_step_count = 0
        self.__refresh_unexplained()
        while itertools.count():
            explained_size = len(self.context)
            for prop, comment, premises in iteration():
                self.__reason(prop, comment, premises)
            self.__iteration_step_count += 1
            self.__refresh_unexplained()
            if len(self.context) == explained_size:
                break

    def dump(self):
        if len(self.context) > 0:
            print('Explained:')
            explained = self.context.all
            explained.sort(key=lambda p: p.reason.index)
            for prop in explained:
                print('\t%2d (%d): %s [%s]' % (prop.reason.index, prop.reason.generation, prop, prop.reason))
        if len(self.__unexplained) > 0:
            print('\nNot explained:')
            for prop in self.__unexplained:
                print('\t%s' % prop)

    def stats(self):
        def type_presentation(kind):
            return kind.__doc__.strip() if kind.__doc__ else kind.__name__

        explained_by_kind = {}
        for rsn in self.context.all:
            kind = type(rsn)
            explained_by_kind[kind] = explained_by_kind.get(kind, 0) + 1
        explained_by_kind = [(type_presentation(k), v) for k, v in explained_by_kind.items()]
        explained_by_kind.sort(key=lambda pair: -pair[1])

        unexplained_by_kind = {}
        for prop in self.__unexplained:
            kind = type(prop)
            unexplained_by_kind[kind] = unexplained_by_kind.get(kind, 0) + 1
        unexplained_by_kind = [(type_presentation(k), v) for k, v in unexplained_by_kind.items()]
        unexplained_by_kind.sort(key=lambda pair: -pair[1])

        return Stats([
            ('Total properties', len(self.context) + len(self.__unexplained)),
            ('Explained properties', len(self.context)),
            Stats(explained_by_kind),
            ('Explained property keys', self.context.keys_num()),
            ('Unexplained properties', len(self.__unexplained)),
            Stats(unexplained_by_kind),
            ('Iterations', self.__iteration_step_count),
            ('Explanation time', '%.3f sec' % self.__explanation_time),
        ], 'Explainer stats')

    def guessed(self, obj):
        explained = self.explained(obj)
        if explained:
            return explained

        if isinstance(obj, Scene.Angle):
            for prop in self.__unexplained:
                if isinstance(prop, AngleValueProperty):
                    if obj == prop.angle:
                        return prop.degree
            return None
        raise Exception('Guess not supported for objects of type %s' % type(obj).__name__)

    def explained(self, obj):
        if isinstance(obj, Scene.Angle):
            rsn = self.context.angle_value_property(obj)
            return rsn.degree if rsn else None
        raise Exception('Explanation not supported for objects of type %s' % type(obj).__name__)

    def explanation(self, obj):
        if isinstance(obj, Scene.Angle):
            return self.context.angle_value_property(obj)
        return None
