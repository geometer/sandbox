import itertools
import time

from .core import Constraint
from .property import *
from .reason import Reason
from .scene import Scene
from .stats import Stats
from .util import _comment, divide

# +++++ utility methods +++++
def same_segment(vec0, vec1):
    return vec0 == vec1 or vec0 == vec1.reversed

def same_segment_pair(pair0, pair1):
    return same_segment(pair0[0], pair1[0]) and same_segment(pair0[1], pair1[1]) \
        or same_segment(pair0[0], pair1[1]) and same_segment(pair0[1], pair1[0])

def side_of(triangle, index):
    return triangle[(index + 1) % 3].vector(triangle[(index + 2) % 3])

def angle_of(triangle, index):
    return triangle[index].angle(triangle[(index + 1) % 3], triangle[(index + 2) % 3])

def side_pairs(prop):
    if not hasattr(prop, 'side_pairs'):
        prop.side_pairs = [[side_of(t, i) for t in (prop.ABC, prop.DEF)] for i in range(0, 3)]
    return prop.side_pairs

def angle_pairs(prop):
    if not hasattr(prop, 'angle_pairs'):
        prop.angle_pairs = [{angle_of(t, i) for t in (prop.ABC, prop.DEF)} for i in range(0, 3)]
    return prop.angle_pairs
# ----- utility methods -----

class Explainer:
    def __init__(self, scene, properties):
        self.scene = scene
        self.__explained = self.scene.predefined_properties()
        self.__unexplained = list(properties)
        self.__explanation_time = None
        self.__iteration_step_count = -1

    def __reason(self, prop, comments, premises=None):
        if prop not in self.__explained:
            prop.reason = Reason(len(self.__explained), self.__iteration_step_count, comments, premises)
            self.__explained.add(prop)

    def __refresh_unexplained(self):
        self.__unexplained = [prop for prop in self.__unexplained if prop not in self.__explained]

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
        key = frozenset([pt0, pt1])
        return next((r for r in self.__explained.list(NotEqualProperty, keys=[key])), None)

    def __not_collinear_reason(self, pt0, pt1, pt2):
        key = frozenset([pt0, pt1, pt2])
        return next((r for r in self.__explained.list(NonCollinearProperty, keys=[key])), None)

    def __angle_value_reason(self, angle):
        return self.__explained[AngleValueProperty(angle, 0)]

    def __congruent_segments_reason(self, vec0, vec1):
        return self.__explained[CongruentSegmentProperty(vec0, vec1)]

    def __angle_ratio_reasons(self, angle):
        return self.__explained.list(AnglesRatioProperty, keys=[angle])

    def __explain_all(self):
        def base():
            for cnst in self.scene.constraints(Constraint.Kind.collinear):
                self.__reason(CollinearProperty(*cnst.params), cnst.comments)
            for cnst in self.scene.constraints(Constraint.Kind.opposite_side):
                self.__reason(
                    OppositeSideProperty(cnst.params[2], cnst.params[0], cnst.params[1]),
                    cnst.comments
                )
            for cnst in self.scene.constraints(Constraint.Kind.same_side):
                self.__reason(
                    SameSideProperty(cnst.params[2], cnst.params[0], cnst.params[1]),
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
                if isinstance(prop, CollinearProperty):
                    line = self.scene.get_line(*prop.points[:2])
                    if line and prop.points[2] in line:
                        self.__reason(prop, 'Given')
                        continue
                elif isinstance(prop, AngleValueProperty) and prop.degree == 0:
                    for cnst in self.scene.constraints(Constraint.Kind.same_direction):
                        if prop.angle == cnst.params[0].angle(*cnst.params[1:]):
                             self.__reason(prop, cnst.comments)
                             break
                elif isinstance(prop, AngleValueProperty) and prop.degree == 90:
                    for cnst in self.scene.constraints(Constraint.Kind.perpendicular):
                        line0 = cnst.params[0]
                        line1 = cnst.params[1]
                        if prop.angle.vector0 in line0 and prop.angle.vector1 in line1:
                            self.__reason(prop, cnst.comments)
                            break
                        elif prop.angle.vector0 in line1 and prop.angle.vector1 in line0:
                            self.__reason(prop, cnst.comments)
                            break
                elif isinstance(prop, CongruentSegmentProperty):
                    found = False
                    points0 = prop.vector0.points
                    points1 = prop.vector1.points
                    centre = next((p for p in points0 if p in points1), None)
                    if centre is not None:
                        pt0 = next((p for p in points0 if p != centre), None)
                        pt1 = next((p for p in points1 if p != centre), None)
                        for circle in self.scene.circles():
                            if circle.centre == centre and pt0 in circle and pt1 in circle:
                                self.__reason(prop, 'Two radiuses of the same circle')
                                found = True
                                break

                    if found:
                        continue

                    for cnst in self.scene.constraints(Constraint.Kind.distances_ratio):
                        if cnst.params[2] == 1:
                            if same_segment_pair(cnst.params[0:2], (prop.vector0, prop.vector1)):
                                self.__reason(prop, 'Given')
                                break

        def iteration():
            def is_too_old(prop):
                return prop.reason.generation < self.__iteration_step_count - 1

            for ncl in self.__explained.list(NonCollinearProperty):
                def extra_comments(pt, pt0, pt1):
                    return [_comment('%s lies on the line %s %s', pt, pt0, pt1)]

                def add_reasons(pt0, pt1, pt2):
                    line = self.scene.get_line(pt0, pt1)
                    if line:
                        for pt in line.all_points:
                            self.__reason(
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
                            self.__reason(
                                NonCollinearProperty(ptX, ptY, pt2),
                                _comment(
                                    '%s and %s lie on the line %s %s, %s does not',
                                    ptX, ptY, pt0, pt1, pt2
                                ),
                                [ncl, ne]
                            )

                self.__reason(NotEqualProperty(ncl.points[0], ncl.points[1]), str(ncl))
                self.__reason(NotEqualProperty(ncl.points[0], ncl.points[2]), str(ncl))
                self.__reason(NotEqualProperty(ncl.points[1], ncl.points[2]), str(ncl))
                add_reasons(ncl.points[0], ncl.points[1], ncl.points[2])
                add_reasons(ncl.points[1], ncl.points[2], ncl.points[0])
                add_reasons(ncl.points[2], ncl.points[0], ncl.points[1])

                ncl_set = set(ncl.points)
                for col in self.__explained.list(CollinearProperty):
                    col_set = set(col.points)
                    intr = col_set.intersection(ncl_set)
                    if len(intr) == 2:
                        pt0 = col_set.difference(ncl_set).pop()
                        pt1 = ncl_set.difference(col_set).pop()
                        self.__reason(NotEqualProperty(pt0, pt1), [], [ncl, col])
                        for common in intr:
                            ne = self.__not_equal_reason(common, pt1)
                            if ne:
                                self.__reason(
                                    NonCollinearProperty(common, pt0, pt1),
                                    _comment(
                                        '%s and %s lie on the line %s %s, %s does not',
                                        common, pt0, *intr, pt1
                                    ),
                                    [ncl, col, ne]
                                )

            for cs in self.__explained.list(CongruentSegmentProperty):
                vec0 = cs.vector0
                vec1 = cs.vector1

                ne0 = self.__not_equal_reason(*vec0.points)
                ne1 = self.__not_equal_reason(*vec1.points)
                if ne0 is not None and ne1 is None:
                    self.__reason(NotEqualProperty(*vec1.points), _comment('Otherwise, %s = %s', *vec0.points), [cs, ne0])
                elif ne1 is not None and ne0 is None:
                    self.__reason(NotEqualProperty(*vec0.points), _comment('Otherwise, %s = %s', *vec1.points), [cs, ne1])
                elif ne0 is None and ne1 is None:
                    ne = None
                    if vec0.start == vec1.start:
                        ne = self.__not_equal_reason(vec0.end, vec1.end)
                        mid = vec0.start
                    elif vec0.start == vec1.end:
                        ne = self.__not_equal_reason(vec0.end, vec1.start)
                        mid = vec0.start
                    elif vec0.end == vec1.start:
                        ne = self.__not_equal_reason(vec0.start, vec1.end)
                        mid = vec0.end
                    elif vec0.end == vec1.end:
                        ne = self.__not_equal_reason(vec0.start, vec1.start)
                        mid = vec0.end
                    if ne:
                        self.__reason(NotEqualProperty(*vec0.points), _comment('Otherwise, %s = %s = %s', ne.points[0], mid, ne.points[1]), [cs, ne])
                        self.__reason(NotEqualProperty(*vec1.points), _comment('Otherwise, %s = %s = %s', ne.points[1], mid, ne.points[0]), [cs, ne])

            for pv in self.__explained.list(ParallelVectorsProperty):
                vec0 = pv.vector0
                vec1 = pv.vector1
                ne0 = self.__not_equal_reason(*vec0.points)
                ne1 = self.__not_equal_reason(*vec1.points)
                if ne0 is not None and ne1 is not None:
                    for prop in AngleValueProperty.generate(vec0.angle(vec1), 0):
                        self.__reason(prop, [], [pv, ne0, ne1])

            same_side_reasons = self.__explained.list(SameSideProperty)
            for rsn in same_side_reasons:
                pt0 = rsn.points[0]
                pt1 = rsn.points[1]
                line2 = self.scene.get_line(pt0, pt1)
                if line2 is None:
                    continue
                crossing = self.scene.get_intersection(rsn.line, line2)
                if crossing:
                    self.__reason(AngleValueProperty(crossing.angle(pt0, pt1), 0), rsn.reason.comments, [rsn])

            for rsn0, rsn1 in itertools.combinations(same_side_reasons, 2):
                AB = rsn0.line
                AC = rsn1.line
                if AB == AC:
                    continue
                A = self.scene.get_intersection(AB, AC)
                if A is None:
                    continue
                pt00 = rsn0.points[0]
                pt01 = rsn0.points[1]
                pt10 = rsn1.points[0]
                pt11 = rsn1.points[1]
                if pt00 == pt10:
                    B, C, D = pt11, pt01, pt00
                elif pt01 == pt10:
                    B, C, D = pt11, pt00, pt01
                elif pt00 == pt11:
                    B, C, D = pt10, pt01, pt00
                elif pt01 == pt11:
                    B, C, D = pt10, pt00, pt01
                else:
                    continue
                if B == C or B not in AB or C not in AC:
                    continue
                AD = self.scene.get_line(A, D)
                BC = self.scene.get_line(B, C)
                if AD is None or BC is None:
                    continue
                X = self.scene.get_intersection(AD, BC)
                if X is not None and X not in (A, B, C, D):
                    comment = _comment('%s is intersection of [%s %s) and [%s %s]', X, A, D, B, C)
                    self.__reason(AngleValueProperty(A.angle(D, X), 0), [comment], [rsn0, rsn1])
                    self.__reason(AngleValueProperty(B.angle(C, X), 0), [comment], [rsn0, rsn1])
                    self.__reason(AngleValueProperty(C.angle(B, X), 0), [comment], [rsn0, rsn1])
                    self.__reason(AngleValueProperty(X.angle(B, C), 180), [comment], [rsn0, rsn1])

            same_direction = [rsn for rsn in self.__explained.list(AngleValueProperty) if \
                rsn.degree == 0 and rsn.angle.vertex is not None]

            for sd in same_direction:
                vertex = sd.angle.vertex
                pt0 = sd.angle.vector0.end
                pt1 = sd.angle.vector1.end
                for nc in self.__explained.list(NonCollinearProperty):
                    params = set(nc.points)
                    if vertex in params:
                        params.remove(vertex)
                        if pt0 in params and pt1 not in params:
                            params.remove(pt0)
                            line = self.scene.get_line(vertex, params.pop())
                            if line:
                                self.__reason(SameSideProperty(line, pt0, pt1), [str(sd), str(nc)], [sd, nc])
                        elif pt1 in params and pt0 not in params:
                            params.remove(pt1)
                            line = self.scene.get_line(vertex, params.pop())
                            if line:
                                self.__reason(SameSideProperty(line, pt0, pt1), [str(sd), str(nc)], [sd, nc])

            for sd in same_direction:
                angle = sd.angle
                vec0 = angle.vector0
                vec1 = angle.vector1

                for ne in self.__explained.list(NotEqualProperty, keys=[angle.vertex]):
                    vector = ne.points[0].vector(ne.points[1])
                    if vector.start != angle.vertex:
                        vector = vector.reversed
                    if len(set(vector.points + vec0.points)) < 3 or len(set(vector.points + vec1.points)) < 3:
                        continue
                    self.__reason(AnglesRatioProperty(vec0.angle(vector), vec1.angle(vector), 1), [], [sd])

            def same_dir(vector):
                yield (vector, [])
                for sd in same_direction:
                    vertex = sd.angle.vertex
                    pt0 = sd.angle.vector0.end
                    pt1 = sd.angle.vector1.end
                    if vertex == vector.start:
                        if pt0 == vector.end:
                            yield (vertex.vector(pt1), [sd])
                        elif pt1 == vector.end:
                            yield (vertex.vector(pt0), [sd])
                    if vertex == vector.end:
                        if pt0 == vector.start:
                            yield (pt1.vector(vertex), [sd])
                        elif pt1 == vector.start:
                            yield (pt0.vector(vertex), [sd])

            def point_inside_angle(point, angle):
                if angle.vertex is None:
                    return False

                line = angle.vector1.line()
                if line is None:
                    return False
                keys = [frozenset([point, angle.vector0.end, line])]
                if next((r for r in self.__explained.list(SameSideProperty, keys=keys)), None) is None:
                    return False

                line = angle.vector0.line()
                if line is None:
                    return False
                keys = [frozenset([point, angle.vector1.end, line])]
                if next((r for r in self.__explained.list(SameSideProperty, keys=keys)), None) is None:
                    return False

                return True

            for ar in self.__explained.list(AnglesRatioProperty):
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
                if not point_inside_angle(common_point, angle):
                    #TODO: consider angle difference
                    continue
                sum_reason = self.__angle_value_reason(angle)
                if sum_reason is None:
                    continue
                value = sum_reason.degree
                second = divide(value, 1 + ar.ratio)
                first = value - second
                #TODO: write comments
                self.__reason(AngleValueProperty(a0, first), [], premises=[ar, sum_reason])
                self.__reason(AngleValueProperty(a1, second), [], premises=[ar, sum_reason])

            for ar in self.__explained.list(AnglesRatioProperty):
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
                a2_reason = self.__angle_value_reason(a2)
                if a2_reason is None:
                    continue
                #a0 + a1 + a2 = 180
                #a0 + a1 = 180 - a2
                a1_value = divide(180 - a2_reason.degree, 1 + ar.ratio)
                a0_value = 180 - a2_reason.degree - a1_value
                comment = _comment('%s + %s + %s = 180º', a0, a1, a2)
                self.__reason(AngleValueProperty(a0, a0_value), comment, premises=[ar, a2_reason])
                self.__reason(AngleValueProperty(a1, a1_value), comment, premises=[ar, a2_reason])

            for ka in self.__explained.list(AngleValueProperty):
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
                                ka2 = self.__angle_value_reason(angle)
                                if ka2 is None:
                                    continue
                                if ka2.degree > ka.degree:
                                    comment = _comment(
                                        '%s, %s, %s are collinear, %s is acute, and %s > %s',
                                        pt, *vec0.points, base, angle, base
                                    )
                                    zero = base.vertex.angle(vec0.end, pt)
                                    self.__reason(AngleValueProperty(zero, 0), comment, [ka, ka2])
                                break

            for iso in self.__explained.list(IsoscelesTriangleProperty):
                if is_too_old(iso):
                    continue
                self.__reason(
                    AnglesRatioProperty(
                        iso.base[0].angle(iso.apex, iso.base[1]),
                        iso.base[1].angle(iso.apex, iso.base[0]),
                        1
                    ),
                    _comment('Base angles of isosceles △ %s %s %s', iso.apex, *iso.base),
                    [iso]
                )
                self.__reason(
                    CongruentSegmentProperty(
                        iso.apex.vector(iso.base[0]),
                        iso.apex.vector(iso.base[1])
                    ),
                    _comment('Legs of isosceles △ %s %s %s', iso.apex, *iso.base),
                    [iso]
                )

            for cs in self.__explained.list(CongruentSegmentProperty):
                if cs.vector1.start in cs.vector0.points:
                    apex = cs.vector1.start
                    base0 = cs.vector1.end
                elif cs.vector1.end in cs.vector0.points:
                    apex = cs.vector1.end
                    base0 = cs.vector1.start
                else:
                    continue
                base1 = cs.vector0.start if apex == cs.vector0.end else cs.vector0.end
                nc = self.__not_collinear_reason(apex, base0, base1)
                if nc:
                    self.__reason(
                        IsoscelesTriangleProperty(apex, (base0, base1)),
                        'Congruent legs',
                        [cs, nc]
                    )

            for ar in self.__explained.list(AnglesRatioProperty):
                if ar.ratio != 1:
                    continue
                if len(ar.angle0.points) != 3 or ar.angle0.points != ar.angle1.points:
                    continue
                nc = self.__not_collinear_reason(*ar.angle0.points)
                if nc is None:
                    continue
                base = (ar.angle0.vertex, ar.angle1.vertex)
                apex = next(pt for pt in ar.angle0.points if pt not in base)
                self.__reason(
                    IsoscelesTriangleProperty(apex, base),
                    'Congruent base angles',
                    [cs]
                )

            for ar in self.__explained.list(AnglesRatioProperty):
                value = self.__angle_value_reason(ar.angle0)
                if value:
                    if ar.ratio == 1:
                        comment = _comment('%s = %s = %sº', ar.angle1, ar.angle0, value.degree)
                    else:
                        comment = _comment('%s = %s / %s = %sº / %s', ar.angle1, ar.angle0, ar.ratio, value.degree, ar.ratio)
                    self.__reason(
                        AngleValueProperty(ar.angle1, divide(value.degree, ar.ratio)),
                        comment, [ar, value]
                    )
                value = self.__angle_value_reason(ar.angle1)
                if value:
                    if ar.ratio == 1:
                        comment = _comment('%s = %s = %sº', ar.angle0, ar.angle1, value.degree)
                    else:
                        comment = _comment('%s = %s * %s = %sº * %s', ar.angle0, ar.angle1, ar.ratio, value.degree, ar.ratio)
                    self.__reason(
                        AngleValueProperty(ar.angle0, value.degree * ar.ratio),
                        comment, [ar, value]
                    )

            for st in self.__explained.list(SimilarTrianglesProperty):
                if is_too_old(st):
                    continue
                for i in range(0, 3):
                    angle0 = angle_of(st.ABC, i)
                    angle1 = angle_of(st.DEF, i)
                    if angle0 != angle1:
                        self.__reason(
                            AnglesRatioProperty(angle0, angle1, 1),
                            'Corresponding angles in similar triangles',
                            [st]
                        )

            for st in self.__explained.list(SimilarTrianglesProperty):
                for i in range(0, 3):
                    cs = self.__congruent_segments_reason(side_of(st.ABC, i), side_of(st.DEF, i))
                    if cs:
                        self.__reason(
                            CongruentTrianglesProperty(st.ABC, st.DEF),
                            'Similar triangles with congruent corresponding sides',
                            [st, cs]
                        )

            for ct in self.__explained.list(CongruentTrianglesProperty):
                if is_too_old(ct):
                    continue
                for i in range(0, 3):
                    segment0 = side_of(ct.ABC, i)
                    segment1 = side_of(ct.DEF, i)
                    if not same_segment(segment0, segment1):
                        self.__reason(
                            CongruentSegmentProperty(segment0, segment1),
                            'Corresponding sides in congruent triangles',
                            [ct]
                        )

            for ct in self.__explained.list(CongruentTrianglesProperty):
                if is_too_old(ct):
                    continue
                self.__reason(
                    SimilarTrianglesProperty(ct.ABC, ct.DEF),
                    'Congruent triangles are similar',
                    [ct]
                )

            for av in self.__explained.list(AngleValueProperty):
                if is_too_old(av):
                    continue
                if av.angle.vertex is None:
                    continue

                second = av.angle.vector0.end.angle(av.angle.vertex, av.angle.vector1.end)
                third = av.angle.vector1.end.angle(av.angle.vertex, av.angle.vector0.end)
                if av.degree == 180:
                    for ang in second, third:
                        self.__reason(
                            AngleValueProperty(ang, 0),
                            _comment('%s = 180º', av.angle),
                            [av]
                        )
                else:
                    second_reason = self.__angle_value_reason(second)
                    if second_reason:
                        self.__reason(
                            AngleValueProperty(third, 180 - av.degree - second_reason.degree),
                            _comment('%s + %s + %s = 180º', third, av.angle, second),
                            [av, second_reason]
                        )
                    else:
                        third_reason = self.__angle_value_reason(third)
                        if third_reason:
                            self.__reason(
                                AngleValueProperty(second, 180 - av.degree - third_reason.degree),
                                _comment('%s + %s + %s = 180º', second, av.angle, third),
                                [av, third_reason]
                            )

            for av0, av1 in itertools.combinations( \
                [av for av in self.__explained.list(AngleValueProperty) if av.degree not in (0, 180)], 2):
                if all(is_too_old(prop) for prop in [av0, av1]):
                    continue
                if av0.degree == av1.degree:
                    comment = _comment('Both angle values = %sº', av0.degree)
                else:
                    comment = _comment('%s = %sº, %s = %sº', av0.angle, av0.degree, av1.angle, av1.degree)
                self.__reason(
                    AnglesRatioProperty(av0.angle, av1.angle, divide(av0.degree, av1.degree)),
                    comment,
                    [av0, av1]
                )

            for zero in [av for av in self.__explained.list(AngleValueProperty) if av.degree == 0]:
                zero_is_too_old = is_too_old(zero)
                for ne in self.__explained.list(NotEqualProperty):
                    if zero_is_too_old and is_too_old(ne):
                        continue
                    vec = ne.points[0].vector(ne.points[1])
                    if same_segment(vec, zero.angle.vector0) or same_segment(vec, zero.angle.vector1):
                        continue
                    for ngl0, cmpl0 in good_angles(vec.angle(zero.angle.vector0)):
                        for ngl1, cmpl1 in good_angles(vec.angle(zero.angle.vector1)):
                            if cmpl0 == cmpl1:
                                #TODO: better comment
                                self.__reason(AnglesRatioProperty(ngl0, ngl1, 1), 'Same angle', [zero, ne])
                            else:
                                #TODO: better comment
                                self.__reason(SumOfAnglesProperty(ngl0, ngl1, 180), 'Pair of parallel and pair of antiparallel sides', [zero, ne])

            processed = set()
            for ar0 in self.__explained.list(AnglesRatioProperty):
                if is_too_old(ar0):
                    continue
                processed.add(ar0)
                angle_ratios0 = list(self.__angle_ratio_reasons(ar0.angle0))
                angle_ratios1 = list(self.__angle_ratio_reasons(ar0.angle1))
                used0 = {(ar.angle0 if ar.angle1 == ar0.angle0 else ar.angle1) for ar in angle_ratios0}
                used1 = {(ar.angle0 if ar.angle1 == ar0.angle1 else ar.angle1) for ar in angle_ratios1}
                for ar1 in angle_ratios0:
                    if ar1 in processed:
                        continue
                    prop = None
                    #TODO: report contradictions if in used and ratio is different
                    if ar0.angle0 == ar1.angle0 and ar1.angle1 not in used1:
                        prop = AnglesRatioProperty(ar0.angle1, ar1.angle1, divide(ar1.ratio, ar0.ratio))
                    elif ar1.angle0 not in used1:
                        prop = AnglesRatioProperty(ar1.angle0, ar0.angle1, ar0.ratio * ar1.ratio)
                    if prop:
                        #TODO: better comment
                        self.__reason(prop, 'Transitivity', [ar0, ar1])
                for ar1 in self.__angle_ratio_reasons(ar0.angle1):
                    if ar1 in processed:
                        continue
                    prop = None
                    if ar0.angle1 == ar1.angle1 and ar1.angle0 not in used0:
                        prop = AnglesRatioProperty(ar0.angle0, ar1.angle0, divide(ar0.ratio, ar1.ratio))
                    elif ar1.angle1 not in used0:
                        prop = AnglesRatioProperty(ar0.angle0, ar1.angle1, ar0.ratio * ar1.ratio)
                    if prop:
                        #TODO: better comment
                        self.__reason(prop, 'Transitivity', [ar0, ar1])

            for ar in [p for p in self.__explained.list(AnglesRatioProperty) if p.ratio == 1]:
                ar_is_too_old = is_too_old(ar)
                set0 = set()
                set1 = set()
                for sa in self.__explained.list(SumOfAnglesProperty, keys=[ar.angle0]):
                    if ar_is_too_old and is_too_old(sa):
                        continue
                    set0.add(sa.angle1 if sa.angle0 == ar.angle0 else sa.angle0)
                for sa in self.__explained.list(SumOfAnglesProperty, keys=[ar.angle1]):
                    if ar_is_too_old and is_too_old(sa):
                        continue
                    set1.add(sa.angle1 if sa.angle0 == ar.angle1 else sa.angle0)
                for angle in set0.difference(set1):
                    prop = SumOfAnglesProperty(ar.angle1, angle, sa.degree)
                    self.__reason(prop, 'Transitivity', [sa, ar])
                for angle in set1.difference(set0):
                    prop = SumOfAnglesProperty(ar.angle0, angle, sa.degree)
                    self.__reason(prop, 'Transitivity', [sa, ar])

            for sa in self.__explained.list(SumOfAnglesProperty):
                av = self.__angle_value_reason(sa.angle0)
                if av:
                    #TODO: report contradiction if value is already known
                    #TODO: report contradiction if the sum is greater than the summand
                    self.__reason(
                        AngleValueProperty(sa.angle1, sa.degree - av.degree),
                        _comment('%sº - %sº', sa.degree, av.degree),
                        [sa, av]
                    )
                else:
                    av = self.__angle_value_reason(sa.angle1)
                    if av:
                        #TODO: report contradiction if the sum is greater than the summand
                        self.__reason(
                            AngleValueProperty(sa.angle0, sa.degree - av.degree),
                            _comment('%sº - %sº', sa.degree, av.degree),
                            [sa, av]
                        )

            angle_ratios = [ar for ar in self.__explained.list(AnglesRatioProperty) if ar.ratio == 1 and ar.angle0.vertex and ar.angle1.vertex]
            def pts(prop):
                return {prop.angle0.points, prop.angle1.points}

            processed = set()
            for ar0 in angle_ratios:
                if is_too_old(ar0):
                    continue
                processed.add(ar0)
                pts0 = pts(ar0)
                angles0 = {ar0.angle0, ar0.angle1}
                for ar1 in [ar for ar in angle_ratios if ar not in processed and pts(ar) == pts0]:
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
                    self.__reason(
                        SimilarTrianglesProperty(tr0, tr1),
                        'Two pairs of congruent angles',
                        [ar0, ar1]
                    )

            for prop in list(self.__unexplained):
                if isinstance(prop, CongruentTrianglesProperty):
                    congruent_angles = [ar for ar in self.__explained.list(AnglesRatioProperty, prop.keys([3])) if ar.ratio == 1]
                    congruent_segments = self.__explained.list(CongruentSegmentProperty, prop.keys([2]))
                    sides = []
                    for i in range(0, 3):
                        left = side_of(prop.ABC, i)
                        right = side_of(prop.DEF, i)
                        if same_segment(left, right):
                            sides.append(left)
                            continue
                        for cs in congruent_segments:
                            if same_segment_pair((left, right), (cs.vector0, cs.vector1)):
                                sides.append(cs)
                                break
                        else:
                            sides.append(None)

                    if all(e is not None for e in sides):
                        premises = [e for e in sides if isinstance(e, Property)]
                        common = [e for e in sides if not isinstance(e, Property)]
                        if len(premises) == 3:
                            self.__reason(prop, 'Three pairs of congruent sides', premises)
                        else: # len(premises) == 2
                            self.__reason(prop, _comment('Common side %s, two pairs of congruent sides', common[0]), premises)
                        continue

                    if any(e is not None for e in sides):
                        angles = []
                        for i in range(0, 3):
                            left = angle_of(prop.ABC, i)
                            right = angle_of(prop.DEF, i)
                            if left == right:
                                angles.append(left)
                                continue
                            pair = {left, right}
                            for ca in congruent_angles:
                                if pair == {ca.angle0, ca.angle1}:
                                    angles.append(ca)
                                    break
                            else:
                                angles.append(None)

                        for i in range(0, 3):
                            reasons = [angles[j] if j == i else sides[j] for j in range(0, 3)]
                            if all(e is not None for e in reasons):
                                premises = [e for e in reasons if isinstance(e, Property)]
                                #TODO: better comment
                                self.__reason(prop, 'Two sides and angle between the sides', premises)
                                break

        base()
        self.__iteration_step_count = 0
        self.__refresh_unexplained()
        while itertools.count():
            explained_size = len(self.__explained)
            iteration()
            self.__iteration_step_count += 1
            self.__refresh_unexplained()
            if len(self.__explained) == explained_size:
                break

    def dump(self):
        if len(self.__explained) > 0:
            print('Explained:')
            explained = self.__explained.all
            explained.sort(key=lambda p: p.reason.index)
            for prop in explained:
                print('\t%2d: %s [%s]' % (prop.reason.index, prop, prop.reason))
        if len(self.__unexplained) > 0:
            print('\nNot explained:')
            for prop in self.__unexplained:
                print('\t%s' % prop)

    def stats(self):
        def type_presentation(kind):
            return kind.__doc__.strip() if kind.__doc__ else kind.__name__

        explained_by_kind = {}
        for rsn in self.__explained.all:
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
            ('Total properties', len(self.__explained) + len(self.__unexplained)),
            ('Explained properties', len(self.__explained)),
            Stats(explained_by_kind),
            ('Explained property keys', self.__explained.keys_num()),
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
            rsn = self.__angle_value_reason(obj)
            return rsn.degree if rsn else None
        raise Exception('Explanation not supported for objects of type %s' % type(obj).__name__)

    def explanation(self, obj):
        if isinstance(obj, Scene.Angle):
            return self.__angle_value_reason(obj)
        return None
