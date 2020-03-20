import itertools
import time

from .core import Constraint
from .property import *
from .reason import Reason
from .scene import Scene
from .stats import Stats
from .util import _comment, divide, side_of, angle_of

class Explainer:
    def __init__(self, scene, properties):
        self.scene = scene
        self.context = self.scene.predefined_properties()
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

    def __not_equal_reason(self, pt0, pt1):
        return self.context[NotEqualProperty(pt0, pt1)]

    def __not_collinear_reason(self, pt0, pt1, pt2):
        return self.context[NonCollinearProperty(pt0, pt1, pt2)]

    def __congruent_segments_reason(self, seg0, seg1):
        return self.context[CongruentSegmentProperty(seg0, seg1)]

    def __angle_ratio_reasons(self, angle):
        return self.context.list(AnglesRatioProperty, keys=[angle])

    def __explain_all(self):
        def base():
            for cnst in self.scene.constraints(Constraint.Kind.collinear):
                self.__reason(CollinearProperty(*cnst.params), cnst.comments)
            for cnst in self.scene.constraints(Constraint.Kind.opposite_side):
                self.__reason(
                    SameOrOppositeSideProperty(cnst.params[2], cnst.params[0], cnst.params[1], False),
                    cnst.comments
                )
            for cnst in self.scene.constraints(Constraint.Kind.inside_angle):
                self.__reason(
                    PointInsideAngleProperty(cnst.params[0], cnst.params[1]),
                    cnst.comments
                )
            for cnst in self.scene.constraints(Constraint.Kind.same_side):
                self.__reason(
                    SameOrOppositeSideProperty(cnst.params[2], cnst.params[0], cnst.params[1], True),
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

            processed = set()
            for ar0 in self.context.list(AnglesRatioProperty):
                if is_too_old(ar0):
                    continue
                processed.add(ar0)
                angle_ratios0 = list(self.__angle_ratio_reasons(ar0.angle0))
                angle_ratios1 = list(self.__angle_ratio_reasons(ar0.angle1))
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

            for ncl in self.context.list(NonCollinearProperty):
                if not is_too_old(ncl):
                    def extra_comments(pt, pt0, pt1):
                        return [_comment('%s lies on the line %s %s', pt, pt0, pt1)]

                    def add_reasons(pt0, pt1, pt2):
                        line = self.scene.get_line(pt0, pt1)
                        if line:
                            for pt in line.all_points:
                                yield (
                                    NotEqualProperty(pt, pt2),
                                    _comment(
                                        '%s lies on the line %s %s, %s does not',
                                        pt, pt0, pt1, pt2
                                    ),
                                    [ncl]
                                )
                            for ptX, ptY in itertools.combinations(line.all_points, 2):
                                ne = self.__not_equal_reason(ptX, ptY)
                                if ne is None:
                                    continue
                                comments = [str(ncl)]
                                if not ptX in (pt0, pt1):
                                    comments += extra_comments(ptX, pt0, pt1)
                                if not ptY in (pt0, pt1):
                                    comments += extra_comments(ptY, pt0, pt1)
                                yield (
                                    NonCollinearProperty(ptX, ptY, pt2),
                                    _comment(
                                        '%s and %s lie on the line %s %s, %s does not',
                                        ptX, ptY, pt0, pt1, pt2
                                    ),
                                    [ncl, ne]
                                )

                    #TODO: better comments
                    yield (NotEqualProperty(ncl.points[0], ncl.points[1]), str(ncl), [ncl])
                    yield (NotEqualProperty(ncl.points[0], ncl.points[2]), str(ncl), [ncl])
                    yield (NotEqualProperty(ncl.points[1], ncl.points[2]), str(ncl), [ncl])
                    add_reasons(ncl.points[0], ncl.points[1], ncl.points[2])
                    add_reasons(ncl.points[1], ncl.points[2], ncl.points[0])
                    add_reasons(ncl.points[2], ncl.points[0], ncl.points[1])

                ncl_set = set(ncl.points)
                for col in self.context.list(CollinearProperty):
                    col_set = set(col.points)
                    intr = col_set.intersection(ncl_set)
                    if len(intr) == 2:
                        pt0 = col_set.difference(ncl_set).pop()
                        pt1 = ncl_set.difference(col_set).pop()
                        yield (NotEqualProperty(pt0, pt1), [], [ncl, col])
                        for common in intr:
                            ne = self.__not_equal_reason(common, pt1)
                            if ne:
                                yield (
                                    NonCollinearProperty(common, pt0, pt1),
                                    _comment(
                                        '%s and %s lie on the line %s %s, %s does not',
                                        common, pt0, *intr, pt1
                                    ),
                                    [ncl, col, ne]
                                )

            for cs in self.context.list(CongruentSegmentProperty):
                vec0 = cs.segment0
                vec1 = cs.segment1

                ne0 = self.__not_equal_reason(*vec0.points)
                ne1 = self.__not_equal_reason(*vec1.points)
                if ne0 is not None and ne1 is None:
                    yield (NotEqualProperty(*vec1.points), _comment('Otherwise, %s = %s', *vec0.points), [cs, ne0])
                elif ne1 is not None and ne0 is None:
                    yield (NotEqualProperty(*vec0.points), _comment('Otherwise, %s = %s', *vec1.points), [cs, ne1])
                elif ne0 is None and ne1 is None:
                    ne = None
                    if vec0.points[0] == vec1.points[0]:
                        ne = self.__not_equal_reason(vec0.points[1], vec1.points[1])
                        mid = vec0.points[0]
                    elif vec0.points[0] == vec1.points[1]:
                        ne = self.__not_equal_reason(vec0.points[1], vec1.points[0])
                        mid = vec0.points[0]
                    elif vec0.points[1] == vec1.points[0]:
                        ne = self.__not_equal_reason(vec0.points[0], vec1.points[1])
                        mid = vec0.points[1]
                    elif vec0.points[1] == vec1.points[1]:
                        ne = self.__not_equal_reason(vec0.points[0], vec1.points[0])
                        mid = vec0.points[1]
                    if ne:
                        yield (NotEqualProperty(*vec0.points), _comment('Otherwise, %s = %s = %s', ne.points[0], mid, ne.points[1]), [cs, ne])
                        yield (NotEqualProperty(*vec1.points), _comment('Otherwise, %s = %s = %s', ne.points[1], mid, ne.points[0]), [cs, ne])

            for pv in self.context.list(ParallelVectorsProperty):
                vec0 = pv.vector0
                vec1 = pv.vector1
                ne0 = self.__not_equal_reason(*vec0.points)
                ne1 = self.__not_equal_reason(*vec1.points)
                if ne0 is not None and ne1 is not None:
                    if is_too_old(pv) and is_too_old(ne0) and is_too_old(ne1):
                        continue
                    for prop in AngleValueProperty.generate(vec0.angle(vec1), 0):
                        yield (prop, [], [pv, ne0, ne1])

            for prop in [p for p in self.context.list(SameOrOppositeSideProperty) if p.same]:
                prop_is_too_old = is_too_old(prop)
                for pt in self.scene.points(skip_auxiliary=True):
                    if pt in prop.points:
                        continue
                    value = self.context.angle_value_reason(pt.angle(*prop.points))
                    if not value or value.degree != 180 or prop_is_too_old and is_too_old(value):
                        continue
                    segment = prop.points[0].segment(prop.points[1])
                    for old in prop.points:
                        yield (
                            SameOrOppositeSideProperty(prop.line, old, pt, True),
                            _comment('The segment %s does not cross line %s', segment, prop.line),
                            [prop, value]
                        )

            for prop in self.context.list(SameOrOppositeSideProperty):
                if is_too_old(prop):
                    continue
                pt0 = prop.points[0]
                pt1 = prop.points[1]
                crossing = self.scene.get_intersection(prop.line, pt0.line_through(pt1))
                if not crossing:
                    continue
                if prop.same:
                    yield (
                        AngleValueProperty(crossing.angle(pt0, pt1), 0),
                        _comment('%s is an intersection of straighit line containing segment %s and line %s', crossing, pt0.segment(pt1), prop.line),
                        [prop]
                    )
                else:
                    yield (
                        AngleValueProperty(crossing.angle(pt0, pt1), 180),
                        _comment('%s is an intersection of segment %s and line %s', crossing, pt0.segment(pt1), prop.line),
                        [prop]
                    )

            for av in [av for av in self.context.list(AngleValueProperty) if av.angle.vertex and av.degree == 180]:
                av_is_too_old = is_too_old(av)
                ang = av.angle
                for ne in self.context.list(NotEqualProperty, [ang.vertex]):
                    if av_is_too_old and is_too_old(ne):
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
                for ne in self.context.list(NotEqualProperty, [ang.vertex]):
                    if av_is_too_old and is_too_old(ne):
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

            for zero in [av for av in self.context.list(AngleValueProperty) if av.degree == 0]:
                zero_is_too_old = is_too_old(zero)
                for ne in self.context.list(NotEqualProperty):
                    if zero_is_too_old and is_too_old(ne):
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
                if is_too_old(pia):
                    continue
                A = pia.angle.vertex
                if A is None:
                    continue
                B = pia.angle.vector0.end
                C = pia.angle.vector1.end
                D = pia.point
                AD = A.line_through(D)
                BC = B.line_through(C)
                X = self.scene.get_intersection(AD, BC)
                if X is not None and X not in (A, B, C, D):
                    comment = _comment('%s is intersection of ray [%s %s) and segment [%s %s]', X, A, D, B, C)
                    yield (AngleValueProperty(A.angle(D, X), 0), [comment], [pia])
                    yield (AngleValueProperty(B.angle(C, X), 0), [comment], [pia])
                    yield (AngleValueProperty(C.angle(B, X), 0), [comment], [pia])
                    yield (AngleValueProperty(X.angle(B, C), 180), [comment], [pia])

            for pia in self.context.list(PointInsideAngleProperty):
                if is_too_old(pia):
                    continue
                yield (
                    SameOrOppositeSideProperty(pia.angle.vector0.line(), pia.point, pia.angle.vector1.end, True),
                    '', #TODO: write comment
                    [pia]
                )
                yield (
                    SameOrOppositeSideProperty(pia.angle.vector1.line(), pia.point, pia.angle.vector0.end, True),
                    '', #TODO: write comment
                    [pia]
                )

            for ss0, ss1 in itertools.combinations([p for p in self.context.list(SameOrOppositeSideProperty) if p.same], 2):
                if is_too_old(ss0) and is_too_old(ss1):
                    continue

                if ss0.line == ss1.line:
                    continue

                vertex = self.scene.get_intersection(ss0.line, ss1.line)
                if vertex is None:
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

                if other0 not in ss1.line or other1 not in ss0.line:
                    continue

                if len({vertex, common, other0, other1}) < 4:
                    continue

                yield (
                    PointInsideAngleProperty(common, vertex.angle(other0, other1)),
                    '', #TODO: write comment
                    [ss0, ss1]
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
                sum_reason = self.context.angle_value_reason(angle)
                if sum_reason is None:
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
                    for nc in self.context.list(NonCollinearProperty, [vec.as_segment]):
                        if av_is_too_old and is_too_old(nc):
                            continue
                        line = vertex.line_through(
                            next(pt for pt in nc.points if pt not in vec.points)
                        )
                        yield (
                            SameOrOppositeSideProperty(line, pt0, pt1, True),
                            [str(av), str(nc)], #TODO: better comment
                            [av, nc]
                        )

            for av in [av for av in angle_values if av.degree == 180]:
                av_is_too_old = is_too_old(av)
                segment = av.angle.vector0.end.segment(av.angle.vector1.end)
                for ncl in self.context.list(NonCollinearProperty, [segment]):
                    if av_is_too_old and is_too_old(ncl):
                        continue
                    vertex = next(pt for pt in ncl.points if pt not in segment.points)
                    angle = vertex.angle(*segment.points)
                    yield (
                        PointInsideAngleProperty(av.angle.vertex, angle),
                        _comment('%s lies inside a segment with endoints on sides of %s', av.angle.vertex, angle),
                        [av, ncl]
                    )
                    yield (
                        SameOrOppositeSideProperty(av.angle.vertex.line_through(vertex), *segment.points, False),
                        _comment('%s lies inside segment %s, and %s is not on the line %s', av.angle.vertex, segment, vertex, segment),
                        [av, ncl]
                    )

            for sos0, sos1 in itertools.combinations(self.context.list(SameOrOppositeSideProperty), 2):
                if is_too_old(sos0) and is_too_old(sos1):
                    continue
                if sos0.line != sos1.line:
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
                yield (
                    SameOrOppositeSideProperty(sos0.line, other0, other1, sos0.same == sos1.same),
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
                a2_reason = self.context.angle_value_reason(a2)
                if a2_reason is None:
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
                for vec0, vec1 in [(base.vector0, base.vector1), (base.vector1, base.vector0)]:
                    line = vec0.line()
                    if line:
                        for pt in line.all_points:
                            if pt in vec0.points:
                                continue
                            for angle in [pt.angle(vec1.end, p) for p in vec0.points]:
                                ka2 = self.context.angle_value_reason(angle)
                                if ka2 is None:
                                    continue
                                if ka2.degree > ka.degree:
                                    comment = _comment(
                                        '%s, %s, %s are collinear, %s is acute, and %s > %s',
                                        pt, *vec0.points, base, angle, base
                                    )
                                    zero = base.vertex.angle(vec0.end, pt)
                                    yield (AngleValueProperty(zero, 0), comment, [ka, ka2])
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
                    CongruentSegmentProperty(
                        iso.apex.segment(iso.base.points[0]),
                        iso.apex.segment(iso.base.points[1])
                    ),
                    _comment('Legs of isosceles △ %s %s %s', iso.apex, *iso.base.points),
                    [iso]
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

            for cs in self.context.list(CongruentSegmentProperty):
                if cs.segment1.points[0] in cs.segment0.points:
                    apex = cs.segment1.points[0]
                    base0 = cs.segment1.points[1]
                elif cs.segment1.points[1] in cs.segment0.points:
                    apex = cs.segment1.points[1]
                    base0 = cs.segment1.points[0]
                else:
                    continue
                base1 = cs.segment0.points[0] if apex == cs.segment0.points[1] else cs.segment0.points[1]
#                nc = self.__not_collinear_reason(apex, base0, base1)
#                if nc:
                yield (
                    IsoscelesTriangleProperty(apex, base0.segment(base1)),
                    'Congruent legs',
#                    [cs, nc]
                    [cs]
                )

            for ar in self.context.list(AnglesRatioProperty):
                if ar.ratio != 1:
                    continue
                if len(ar.angle0.points) != 3 or ar.angle0.points != ar.angle1.points:
                    continue
                nc = self.__not_collinear_reason(*ar.angle0.points)
                if nc is None:
                    continue
                base = ar.angle0.vertex.segment(ar.angle1.vertex)
                apex = next(pt for pt in ar.angle0.points if pt not in base.points)
                yield (
                    IsoscelesTriangleProperty(apex, base),
                    'Congruent base angles',
                    [cs]
                )

            for ar in self.context.list(AnglesRatioProperty):
                value = self.context.angle_value_reason(ar.angle0)
                if value:
                    if ar.ratio == 1:
                        comment = _comment('%s = %s = %sº', ar.angle1, ar.angle0, value.degree)
                    else:
                        comment = _comment('%s = %s / %s = %sº / %s', ar.angle1, ar.angle0, ar.ratio, value.degree, ar.ratio)
                    yield (
                        AngleValueProperty(ar.angle1, divide(value.degree, ar.ratio)),
                        comment, [ar, value]
                    )
                value = self.context.angle_value_reason(ar.angle1)
                if value:
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
                            CongruentSegmentProperty(segment0, segment1),
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
                if is_too_old(av):
                    continue
                if av.angle.vertex is None:
                    continue

                second = av.angle.vector0.end.angle(av.angle.vertex, av.angle.vector1.end)
                third = av.angle.vector1.end.angle(av.angle.vertex, av.angle.vector0.end)
                if av.degree == 180:
                    for ang in second, third:
                        yield (
                            AngleValueProperty(ang, 0),
                            _comment('%s = 180º', av.angle),
                            [av]
                        )
                else:
                    second_reason = self.context.angle_value_reason(second)
                    if second_reason:
                        yield (
                            AngleValueProperty(third, 180 - av.degree - second_reason.degree),
                            _comment('%s + %s + %s = 180º', third, av.angle, second),
                            [av, second_reason]
                        )
                    else:
                        third_reason = self.context.angle_value_reason(third)
                        if third_reason:
                            yield (
                                AngleValueProperty(second, 180 - av.degree - third_reason.degree),
                                _comment('%s + %s + %s = 180º', second, av.angle, third),
                                [av, third_reason]
                            )

            for av0, av1 in itertools.combinations( \
                [av for av in self.context.list(AngleValueProperty) if av.degree not in (0, 180)], 2):
                if all(is_too_old(prop) for prop in [av0, av1]):
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
                av = self.context.angle_value_reason(sa.angle0)
                if av:
                    #TODO: report contradiction if value is already known
                    #TODO: report contradiction if the sum is greater than the summand
                    yield (
                        AngleValueProperty(sa.angle1, sa.degree - av.degree),
                        _comment('%sº - %sº', sa.degree, av.degree),
                        [sa, av]
                    )
                else:
                    av = self.context.angle_value_reason(sa.angle1)
                    if av:
                        #TODO: report contradiction if the sum is greater than the summand
                        yield (
                            AngleValueProperty(sa.angle0, sa.degree - av.degree),
                            _comment('%sº - %sº', sa.degree, av.degree),
                            [sa, av]
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

            def congruent_vectors(vec0, vec1):
                if vec0 == vec1:
                    return True
                return self.__congruent_segments_reason(vec0.as_segment, vec1.as_segment)

            for ca in congruent_angles:
                ca_is_too_old = is_too_old(ca)
                ang0 = ca.angle0
                ang1 = ca.angle1
                for vec0, vec1 in [(ang0.vector0, ang0.vector1), (ang0.vector1, ang0.vector0)]:
                    rsn0 = congruent_vectors(vec0, ang1.vector0)
                    if rsn0 is None:
                        continue
                    rsn1 = congruent_vectors(vec1, ang1.vector1)
                    if rsn1 is None:
                        continue
                    if ca_is_too_old and (rsn0 == True or is_too_old(rsn0)) and (rsn1 == True or is_too_old(rsn1)):
                        continue
                    prop = CongruentTrianglesProperty(
                        (ang0.vertex, vec0.end, vec1.end),
                        (ang1.vertex, ang1.vector0.end, ang1.vector1.end)
                    )
                    if self.context[prop] is not None:
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
                    yield (prop, comment, premises)

            congruent_segments = self.context.list(CongruentSegmentProperty)
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

            processed = set()
            for cs0 in congruent_segments:
                if is_too_old(cs0):
                    continue
                processed.add(cs0)
                pairs = [(cs0.segment0, cs0.segment1), (cs0.segment1, cs0.segment0)]
                for cs1 in [cs for cs in congruent_segments if cs not in processed]:
                    for seg0, seg1 in pairs:
                        common0 = common_point(seg0, cs1.segment0)
                        if common0 is None:
                            continue
                        common1 = common_point(seg1, cs1.segment1)
                        if common1 is None:
                            continue
                        third0 = other_point(seg0, common0).segment(other_point(cs1.segment0, common0))
                        third1 = other_point(seg1, common1).segment(other_point(cs1.segment1, common1))
                        prop = CongruentTrianglesProperty(
                            (common0, *third0.points), (common1, *third1.points)
                        )
                        if third0 == third1:
                            yield (
                                prop,
                                _comment('Common side %s, two pairs of congruent sides', third0),
                                [cs0, cs1]
                            )
                        else:
                            cs2 = self.__congruent_segments_reason(third0, third1)
                            if cs2:
                                yield (
                                    prop,
                                    'Three pairs of congruent sides',
                                    [cs0, cs1, cs2]
                                )

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
            rsn = self.context.angle_value_reason(obj)
            return rsn.degree if rsn else None
        raise Exception('Explanation not supported for objects of type %s' % type(obj).__name__)

    def explanation(self, obj):
        if isinstance(obj, Scene.Angle):
            return self.context.angle_value_reason(obj)
        return None
