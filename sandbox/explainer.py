import itertools
import time
import sympy as sp

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
            prop.reason.obsolete = False
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

    def __angles_ratio_reasons(self, angle):
        return self.context.list(AnglesRatioProperty, keys=[angle])

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
            for cnst in self.scene.constraints(Constraint.Kind.angles_ratio):
                self.__reason(
                    AnglesRatioProperty(cnst.params[0], cnst.params[1], cnst.params[2]),
                    cnst.comments
                )

        def iteration():
            for av0, av1 in itertools.combinations(self.context.list(AngleValueProperty), 2):
                if av0.degree == av1.degree or av0.reason.obsolete and av1.reason.obsolete:
                    continue
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
                else:
                    continue

                if vec0.start == vec1.start:
                    prop = PointsCoincidenceProperty(vec0.end, vec1.end, False)
                elif vec0.end == vec1.end:
                    prop = PointsCoincidenceProperty(vec0.start, vec1.start, False)
                else:
                    continue

                yield (prop, _comment('Otherwise, %s = %s', ang0, ang1), [av0, av1])

            def _cs(coef):
                return '' if coef == 1 else ('%s ' % coef)

            for lr0, lr1 in itertools.combinations(self.context.list(LengthRatioProperty), 2):
                if lr0.reason.obsolete and lr1.reason.obsolete:
                    continue
                if lr0.segment0 == lr1.segment0:
                    coef = divide(lr1.value, lr0.value)
                    yield (
                        LengthRatioProperty(lr0.segment1, lr1.segment1, coef),
                        _comment('|%s| = %s|%s| = %s|%s|', lr0.segment1, _cs(divide(1, lr0.value)), lr0.segment0, _cs(coef), lr1.segment1),
                        [lr0, lr1]
                    )
                    pass
                elif lr0.segment0 == lr1.segment1:
                    coef = lr1.value * lr0.value
                    yield (
                        LengthRatioProperty(lr1.segment0, lr0.segment1, coef),
                        _comment('|%s| = %s|%s| = %s|%s|', lr1.segment0, _cs(lr1.value), lr0.segment0, _cs(coef), lr0.segment1),
                        [lr1, lr0]
                    )
                    pass
                elif lr0.segment1 == lr1.segment0:
                    coef = lr1.value * lr0.value
                    yield (
                        LengthRatioProperty(lr0.segment0, lr1.segment1, coef),
                        _comment('|%s| = %s|%s| = %s|%s|', lr0.segment0, _cs(lr0.value), lr0.segment1, _cs(coef), lr1.segment1),
                        [lr0, lr1]
                    )
                    pass
                elif lr0.segment1 == lr1.segment1:
                    coef = divide(lr0.value, lr1.value)
                    yield (
                        LengthRatioProperty(lr0.segment0, lr1.segment0, coef),
                        _comment('|%s| = %s|%s| = %s|%s|', lr0.segment0, _cs(lr0.value), lr0.segment1, _cs(coef), lr1.segment0),
                        [lr0, lr1]
                    )
                    pass

            processed = set()
            for ar0 in self.context.list(AnglesRatioProperty):
                if ar0.reason.obsolete:
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
                        prop = AnglesRatioProperty(ar0.angle1, tup[0], divide(ar1.value, ar0.value))
                    else:
                        prop = AnglesRatioProperty(tup[0], ar0.angle1, ar0.value * ar1.value)
                    #TODO: better comment
                    yield (prop, 'Transitivity', [ar0, ar1])
                tuples1 = [t for t in tuples1 if t[0] not in used0 and t[2] not in processed]
                for tup in tuples1:
                    ar1 = tup[2]
                    if tup[1]:
                        prop = AnglesRatioProperty(ar0.angle0, tup[0], divide(ar0.value, ar1.value))
                    else:
                        prop = AnglesRatioProperty(ar0.angle0, tup[0], ar0.value * ar1.value)
                    #TODO: better comment
                    yield (prop, 'Transitivity', [ar0, ar1])

            for ar in [p for p in self.context.list(AnglesRatioProperty) if p.value == 1]:
                set0 = set()
                set1 = set()
                for sa in self.context.list(SumOfAnglesProperty, keys=[ar.angle0]):
                    if ar.reason.obsolete and sa.reason.obsolete:
                        continue
                    set0.add(sa.angle1 if sa.angle0 == ar.angle0 else sa.angle0)
                for sa in self.context.list(SumOfAnglesProperty, keys=[ar.angle1]):
                    if ar.reason.obsolete and sa.reason.obsolete:
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
                if not ncl.reason.obsolete:
                    #TODO: better comments
                    yield (PointsCoincidenceProperty(ncl.points[0], ncl.points[1], False), str(ncl), [ncl])
                    yield (PointsCoincidenceProperty(ncl.points[0], ncl.points[2], False), str(ncl), [ncl])
                    yield (PointsCoincidenceProperty(ncl.points[1], ncl.points[2], False), str(ncl), [ncl])

                for segment, pt_ncl in [(side_of(ncl.points, i), ncl.points[i]) for i in range(0, 3)]:
                    for col in [p for p in self.context.list(PointsCollinearityProperty, [segment]) if p.collinear]:
                        reasons_are_too_old = ncl.reason.obsolete and col.reason.obsolete
                        pt_col = next(pt for pt in col.points if pt not in segment.points)
                        if not reasons_are_too_old:
                            yield (PointsCoincidenceProperty(pt_col, pt_ncl, False), [], [ncl, col])
                        for common in segment.points:
                            ne = self.context.not_equal_property(common, pt_col)
                            if ne is None or reasons_are_too_old and ne.reason.obsolete:
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
                if ncl is None or ncl.collinear or cl0.reason.obsolete and cl1.reason.obsolete and ncl.reason.obsolete:
                    continue
                yield (
                    PointsCoincidenceProperty(*others, True),
                    _comment('%s and %s belong to two different lines %s and %s', *others, pt0.segment(ncl_pt), pt1.segment(ncl_pt)),
                    [cl0, cl1, ncl]
                )

            for cs in self.context.list(LengthRatioProperty):
                seg0 = cs.segment0
                seg1 = cs.segment1

                ne0 = self.context.not_equal_property(*seg0.points)
                ne1 = self.context.not_equal_property(*seg1.points)
                if ne0 is not None and ne1 is None:
                    yield (PointsCoincidenceProperty(*seg1.points, False), _comment('Otherwise, %s = %s', *seg0.points), [cs, ne0])
                elif ne1 is not None and ne0 is None:
                    yield (PointsCoincidenceProperty(*seg0.points, False), _comment('Otherwise, %s = %s', *seg1.points), [cs, ne1])
                elif ne0 is None and ne1 is None:
                    ne = None
                    if seg0.points[0] == seg1.points[0]:
                        ne = self.context.not_equal_property(seg0.points[1], seg1.points[1])
                        mid = seg0.points[0]
                    elif seg0.points[0] == seg1.points[1]:
                        ne = self.context.not_equal_property(seg0.points[1], seg1.points[0])
                        mid = seg0.points[0]
                    elif seg0.points[1] == seg1.points[0]:
                        ne = self.context.not_equal_property(seg0.points[0], seg1.points[1])
                        mid = seg0.points[1]
                    elif seg0.points[1] == seg1.points[1]:
                        ne = self.context.not_equal_property(seg0.points[0], seg1.points[0])
                        mid = seg0.points[1]
                    if ne:
                        yield (PointsCoincidenceProperty(*seg0.points, False), _comment('Otherwise, %s = %s = %s', ne.points[0], mid, ne.points[1]), [cs, ne])
                        yield (PointsCoincidenceProperty(*seg1.points, False), _comment('Otherwise, %s = %s = %s', ne.points[1], mid, ne.points[0]), [cs, ne])

            for pv in self.context.list(ParallelVectorsProperty):
                vec0 = pv.vector0
                vec1 = pv.vector1
                ne0 = self.context.not_equal_property(*vec0.points)
                ne1 = self.context.not_equal_property(*vec1.points)
                if ne0 is not None and ne1 is not None:
                    if pv.reason.obsolete and ne0.reason.obsolete and ne1.reason.obsolete:
                        continue
                    for prop in AngleValueProperty.generate(vec0, vec1, 0):
                        yield (
                            prop,
                            _comment('Non-zero parallel vectors %s and %s', vec0, vec1),
                            [pv, ne0, ne1]
                        )

            for pv in self.context.list(PerpendicularVectorsProperty):
                vec0 = pv.vector0
                vec1 = pv.vector1
                ne0 = self.context.not_equal_property(*vec0.points)
                ne1 = self.context.not_equal_property(*vec1.points)
                if ne0 is not None and ne1 is not None:
                    if pv.reason.obsolete and ne0.reason.obsolete and ne1.reason.obsolete:
                        continue
                    for prop in AngleValueProperty.generate(vec0, vec1, 90):
                        yield (
                            prop,
                            _comment('Non-zero perpendicular vectors %s and %s', vec0, vec1),
                            [pv, ne0, ne1]
                        )

            for prop in [p for p in self.context.list(SameOrOppositeSideProperty) if p.same]:
                prop_is_too_old = prop.reason.obsolete
                segment = prop.points[0].segment(prop.points[1])
                for col in [p for p in self.context.list(PointsCollinearityProperty, [segment]) if p.collinear]:
                    pt = next(p for p in col.points if p not in prop.points)
                    value = self.context.angle_value_property(pt.angle(*prop.points))
                    if not value or value.degree != 180 or prop_is_too_old and value.reason.obsolete:
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
                if prop.reason.obsolete and all(p.reason.obsolete for p in reasons):
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

            for ra in [av for av in self.context.list(AngleValueProperty) if av.degree == 90]:
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
                                yield (prop, 'Zigzag', [so, sum_reason, ne])
                    else:
                        ratio_reason = self.context.angles_ratio_property(lp0.angle(pt0, lp1), lp1.angle(pt1, lp0))
                        if ratio_reason is None or reasons_are_too_old and ratio_reason.reason.obsolete:
                            continue
                        if ratio_reason.value == 1:
                            for prop in AngleValueProperty.generate(lp0.vector(pt0), pt1.vector(lp1), 0):
                                yield (prop, 'Zigzag', [so, ratio_reason, ne])

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
                if sum_reason is None or ar.reason.obsolete and sum_reason.reason.obsolete and inside_angle_reason.reason.obsolete:
                    continue
                value = sum_reason.degree
                second = divide(value, 1 + ar.value)
                first = value - second
                #TODO: write comments
                yield (AngleValueProperty(a0, first), [], [ar, sum_reason, inside_angle_reason])
                yield (AngleValueProperty(a1, second), [], [ar, sum_reason, inside_angle_reason])

            angle_values = [prop for prop in self.context.list(AngleValueProperty) \
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
                if a2_reason is None or ar.reason.obsolete and a2_reason.reason.obsolete:
                    continue
                #a0 + a1 + a2 = 180
                #a0 + a1 = 180 - a2
                a1_value = divide(180 - a2_reason.degree, 1 + ar.value)
                a0_value = 180 - a2_reason.degree - a1_value
                comment = _comment('%s + %s + %s = 180º', a0, a1, a2)
                yield (AngleValueProperty(a0, a0_value), comment, [ar, a2_reason])
                yield (AngleValueProperty(a1, a1_value), comment, [ar, a2_reason])

            for ka in self.context.list(AngleValueProperty):
                base = ka.angle
                if ka.degree == 0 or ka.degree >= 90 or base.vertex is None:
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
                cs2 = self.context.congruent_segments_property(common.segment(pt0), pt0.segment(pt1))
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
                nc = self.context.not_collinear_property(apex, base0, base1)
                if nc and not (cs.reason.obsolete and nc.reason.obsolete):
                    yield (
                        IsoscelesTriangleProperty(apex, base0.segment(base1)),
                        'Congruent legs',
                        [cs, nc]
                    )

            for ar in self.context.list(AnglesRatioProperty):
                if ar.value != 1:
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

            for equ in self.context.list(EquilateralTriangleProperty):
                if equ.reason.obsolete:
                    continue
                for i in range(0, 3):
                    yield (
                        AngleValueProperty(angle_of(equ.ABC, i), 60),
                        _comment('Angle of equilateral △ %s %s %s', *equ.ABC),
                        [equ]
                    )
                for i, j in itertools.combinations(range(0, 3), 2):
                    yield (
                        LengthRatioProperty(side_of(equ.ABC, i), side_of(equ.ABC, j), 1),
                        _comment('Sides of equilateral △ %s %s %s', *equ.ABC),
                        [equ]
                    )

            for ar in self.context.list(AnglesRatioProperty):
                ar_is_too_old = ar.reason.obsolete
                value = self.context.angle_value_property(ar.angle0)
                if value:
                    if ar_is_too_old and value.reason.obsolete:
                        continue
                    if ar.value == 1:
                        comment = _comment('%s = %s = %sº', ar.angle1, ar.angle0, value.degree)
                    else:
                        comment = _comment('%s = %s / %s = %sº / %s', ar.angle1, ar.angle0, ar.value, value.degree, ar.value)
                    yield (
                        AngleValueProperty(ar.angle1, divide(value.degree, ar.value)),
                        comment, [ar, value]
                    )
                else:
                    value = self.context.angle_value_property(ar.angle1)
                    if value is None or ar_is_too_old and value.reason.obsolete:
                        continue
                    if ar.value == 1:
                        comment = _comment('%s = %s = %sº', ar.angle0, ar.angle1, value.degree)
                    else:
                        comment = _comment('%s = %s * %s = %sº * %s', ar.angle0, ar.angle1, ar.value, value.degree, ar.value)
                    yield (
                        AngleValueProperty(ar.angle0, value.degree * ar.value),
                        comment, [ar, value]
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
                ncl = self.context.not_collinear_property(*st.ABC)
                if ncl is None:
                    ncl = self.context.not_collinear_property(*st.DEF)
                if ncl is None or st.reason.obsolete and ncl.reason.obsolete:
                    continue
                for i in range(0, 3):
                    angle0 = angle_of(st.ABC, i)
                    angle1 = angle_of(st.DEF, i)
                    if angle0 != angle1:
                        yield (
                            AnglesRatioProperty(angle0, angle1, 1),
                            'Corresponding angles in similar non-degenerate triangles',
                            [st, ncl]
                        )

            for st in self.context.list(SimilarTrianglesProperty):
                st_is_too_old = st.reason.obsolete
                for i in range(0, 3):
                    cs = self.context.congruent_segments_property(side_of(st.ABC, i), side_of(st.DEF, i))
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

            def all_combinations(four):
                return (
                    four,
                    (four[0], four[2], four[1], four[3]),
                    (four[1], four[0], four[3], four[2]),
                    (four[1], four[3], four[0], four[2]),
                    (four[2], four[0], four[3], four[1]),
                    (four[2], four[3], four[0], four[1]),
                    (four[3], four[1], four[2], four[0]),
                    (four[3], four[2], four[1], four[0])
                )

            def half_combinations(four):
                return (
                    four,
                    (four[0], four[2], four[1], four[3]),
                    (four[1], four[3], four[0], four[2]),
                    (four[2], four[3], four[0], four[1])
                )

            for segment0, segment1, comment, premises in self.context.length_ratios_equal_to_one():
                if all(prop.reason.obsolete for prop in premises):
                    continue
                yield (
                    LengthRatioProperty(segment0, segment1, 1),
                    comment,
                    premises
                )

            for st in self.context.list(SimilarTrianglesProperty):
                if st.reason.obsolete:
                    continue
                for i, j in itertools.combinations(range(0, 3), 2):
                    side00 = side_of(st.ABC, i)
                    side01 = side_of(st.ABC, j)
                    side10 = side_of(st.DEF, i)
                    side11 = side_of(st.DEF, j)
                    if side00 == side10:
                        yield (
                            LengthRatioProperty(side01, side11, 1),
                            'Ratios of sides in similar triangles',
                            [st]
                        )
                        continue
                    if side01 == side11:
                        yield (
                            LengthRatioProperty(side00, side10, 1),
                            'Ratios of sides in similar triangles',
                            [st]
                        )
                        continue
                    cs = self.context.congruent_segments_property(side00, side10)
                    if cs:
                        yield (
                            LengthRatioProperty(side01, side11, 1),
                            'Ratios of sides in similar triangles',
                            [st, cs]
                        )
                        continue
                    cs = self.context.congruent_segments_property(side01, side11)
                    if cs:
                        yield (
                            LengthRatioProperty(side00, side10, 1),
                            'Ratios of sides in similar triangles',
                            [st, cs]
                        )
                        continue
                    yield (
                        EqualLengthRatiosProperty(side00, side10, side01, side11),
                        'Ratios of sides in similar triangles',
                        [st]
                    )

            for st in self.context.list(SimilarTrianglesProperty):
                st_is_too_old = st.reason.obsolete
                for i in range(0, 3):
                    lr, ratio = self.context.lengths_ratio_property_and_value(side_of(st.ABC, i), side_of(st.DEF, i))
                    if lr is None:
                        continue
                    if ratio == 1 or st_is_too_old and lr.reason.obsolete:
                        break
                    for j in [j for j in range(0, 3) if j != i]:
                        yield (
                            LengthRatioProperty(side_of(st.ABC, j), side_of(st.DEF, j), ratio),
                            'Sides ratio in similar triangles',
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

            for av in self.context.list(AngleValueProperty):
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

            for av0, av1 in itertools.combinations( \
                [av for av in self.context.list(AngleValueProperty) if av.degree not in (0, 180)], 2):
                if av0.reason.obsolete and av1.reason.obsolete:
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
                sa_is_too_old = sa.reason.obsolete
                av = self.context.angle_value_property(sa.angle0)
                if av:
                    if sa_is_too_old and av.reason.obsolete:
                        continue
                    yield (
                        AngleValueProperty(sa.angle1, sa.degree - av.degree),
                        _comment('%sº - %sº', sa.degree, av.degree),
                        [sa, av]
                    )
                else:
                    av = self.context.angle_value_property(sa.angle1)
                    if av is None or sa_is_too_old and av.reason.obsolete:
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

            congruent_angles = [ar for ar in self.context.list(AnglesRatioProperty) if ar.value == 1 and ar.angle0.vertex and ar.angle1.vertex]
            congruent_angles_groups = {}
            for ca in congruent_angles:
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
                return self.context.congruent_segments_property(seg0, seg1)

            for ca in congruent_angles:
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

            for ca in congruent_angles:
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

            for ca in congruent_angles:
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

            for ca in congruent_angles:
                ca_is_too_old = ca.reason.obsolete
                ang0 = ca.angle0
                ang1 = ca.angle1
                for vec0, vec1 in [(ang0.vector0, ang0.vector1), (ang0.vector1, ang0.vector0)]:
                    rsn0, ratio0 = self.context.lengths_ratio_property_and_value(vec0.as_segment, ang1.vector0.as_segment)
                    if rsn0 is None:
                        continue
                    rsn1, ratio1 = self.context.lengths_ratio_property_and_value(vec1.as_segment, ang1.vector1.as_segment)
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
                        cs2 = self.context.congruent_segments_property(third0.as_segment, third1.as_segment)
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
                ps2 = self.context.congruent_segments_property(third0.as_segment, third1.as_segment)
                if ps2 and ps2.value == ps0.value:
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

            right_angles = [p for p in self.context.list(AngleValueProperty) if p.angle.vertex and p.degree == 90]
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

            for av0 in [p for p in self.context.list(AngleValueProperty) if p.angle.vertex and p.degree not in (0, 180)]:
                triangle = (av0.angle.vertex, *av0.angle.endpoints)
                av1 = self.context.angle_value_property(angle_of(triangle, 1))
                if av1 is None or av0.reason.obsolete and av1.reason.obsolete:
                    continue
                sines = (
                    sp.sin(sp.pi * av0.degree / 180),
                    sp.sin(sp.pi * av1.degree / 180),
                    sp.sin(sp.pi * (180 - av0.degree - av1.degree) / 180)
                )
                sides = [side_of(triangle, i) for i in range(0, 3)]
                for (sine0, side0), (sine1, side1) in itertools.combinations(zip(sines, sides), 2):
                    yield (
                        LengthRatioProperty(side0, side1, sine0 / sine1),
                        _comment('Law of sines for △ %s %s %s', *triangle),
                        [av0, av1]
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

            for ca in [p for p in self.context.list(AnglesRatioProperty) if p.value == 1]:
                vertex = ca.angle0.vertex
                if vertex is None or vertex != ca.angle1.vertex:
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

        for prop, comment in self.scene.enumerate_predefined_properties():
            self.__reason(prop, comment, [])

        base()
        self.__iteration_step_count = 0
        self.__refresh_unexplained()
        while itertools.count():
            explained_size = len(self.context)
            for prop, comment, premises in iteration():
                self.__reason(prop, comment, premises)
            for prop in self.context.all:
                prop.reason.obsolete = prop.reason.generation < self.__iteration_step_count
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

        unexplained_by_kind = {}
        for prop in self.__unexplained:
            kind = type(prop)
            unexplained_by_kind[kind] = unexplained_by_kind.get(kind, 0) + 1
        unexplained_by_kind = [(type_presentation(k), v) for k, v in unexplained_by_kind.items()]
        unexplained_by_kind.sort(key=lambda pair: -pair[1])

        return Stats([
            ('Total properties', len(self.context) + len(self.__unexplained)),
            ('Explained properties', len(self.context)),
            self.context.stats(),
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
