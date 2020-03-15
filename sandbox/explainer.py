import itertools
import time
import sympy as sp

from .core import Constraint
from .property import *
from .reason import Reason
from .scene import Scene
from .stats import Stats
from .util import _comment

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
        self.__iteration_step_count = None

    def __reason(self, prop, comments, premises=None):
        if prop not in self.__explained:
            prop.reason = Reason(len(self.__explained), comments, premises)
            self.__explained.add(prop)

    def __refresh_unexplained(self):
        test = set(self.__explained.all)
        self.__unexplained = [prop for prop in self.__unexplained if prop not in test]

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

    def __angle_value_reason(self, angle):
        keys = keys_for_angle(angle)
        return next((p for p in self.__explained.list(AngleValueProperty, keys) \
            if p.angle == angle), None)

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
            for ncl in self.__explained.list(NonCollinearProperty):
                def extra_comments(pt, pt0, pt1):
                    return [_comment('%s lies on the line %s %s', pt, pt0, pt1)]

                def add_reasons(pt0, pt1, pt2):
                    line = self.scene.get_line(pt0, pt1)
                    if line:
                        for pt in line.all_points:
                            if pt in (pt0, pt1):
                                self.__reason(NotEqualProperty(pt, pt2), str(ncl))
                            else:
                                self.__reason(NotEqualProperty(pt, pt2), [str(ncl)] + extra_comments(pt, pt0, pt1))
                        for ptX, ptY in itertools.combinations(line.all_points, 2):
                            ne = self.__not_equal_reason(ptX, ptY)
                            if ne is None:
                                continue
                            comments = [str(ncl)]
                            if not ptX in (pt0, pt1):
                                comments += extra_comments(ptX, pt0, pt1)
                            if not ptY in (pt0, pt1):
                                comments += extra_comments(ptY, pt0, pt1)
                            self.__reason(NonCollinearProperty(ptX, ptY, pt2), comments, [ncl, ne])

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
                    if vec0.end == vec1.end:
                        self.__reason(AngleValueProperty(vec0.reversed.angle(vec1.reversed), 0), [], [pv, ne0, ne1])
                    elif vec0.start == vec1.end:
                        self.__reason(AngleValueProperty(vec0.angle(vec1.reversed), 180), [], [pv, ne0, ne1])
                    elif vec0.end == vec1.start:
                        self.__reason(AngleValueProperty(vec0.reversed.angle(vec1), 180), [], [pv, ne0, ne1])
                    else:
                        self.__reason(AngleValueProperty(vec0.angle(vec1), 0), [], [pv, ne0, ne1])

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
                second = value / sp.sympify(1 + ar.ratio)
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
                a1_value = (180 - a2_reason.degree) / sp.sympify(1 + ar.ratio) 
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
                            angles_to_look = [pt.angle(vec1.end, p) for p in vec0.points]
                            keys = []
                            for a in angles_to_look:
                                for k in keys_for_angle(a):
                                    keys.append(k)
                            for ka2 in self.__explained.list(AngleValueProperty, keys):
                                second = next((a for a in angles_to_look if ka2.angle == a), None)
                                if second is None:
                                    continue
                                if ka2.degree > ka.degree:
                                    comment = _comment(
                                        '%s, %s, %s are collinear, %s is acute, and %s > %s',
                                        pt, *vec0.points, base, second, base
                                    )
                                    zero = base.vertex.angle(vec0.end, pt)
                                    self.__reason(AngleValueProperty(zero, 0), comment, [ka, ka2])
                                break

            for prop in list(self.__unexplained):
                if isinstance(prop, AnglesRatioProperty):
                    found = False

                    if prop.ratio == 1:
                        for v0, sd0 in same_dir(prop.angle0.vector0):
                            lst = list(same_dir(prop.angle0.vector1))
                            def add_reason(vector0, vector1):
                                if v0 == vector0:
                                    try:
                                        found = next(p for p in lst if p[0] == vector1)
                                        self.__reason(prop, 'Same angle', premises=sd0 + found[1])
                                        return True
                                    except StopIteration:
                                        pass
                                return False

                            a10 = prop.angle1.vector0
                            a11 = prop.angle1.vector1
                            found = \
                                add_reason(a10, a11) or \
                                add_reason(a11, a10) or \
                                add_reason(a10.reversed, a11.reversed) or \
                                add_reason(a11.reversed, a10.reversed)
                            if found:
                                break

                        if found:
                            continue

                    known_ratios = self.__explained.list(AnglesRatioProperty, keys=prop.keys())
                    candidates0 = []
                    candidates1 = []
                    for kr in known_ratios:
                        if prop.angle0 == kr.angle0:
                            candidates0.append((kr, kr.angle1, kr.ratio))
                        elif prop.angle0 == kr.angle1:
                            candidates0.append((kr, kr.angle0, sp.sympify(1) / kr.ratio))
                        elif prop.angle1 == kr.angle0:
                            candidates1.append((kr, kr.angle1, sp.sympify(1) / kr.ratio))
                        elif prop.angle1 == kr.angle1:
                            candidates1.append((kr, kr.angle0, kr.ratio))
                    for c0, c1 in itertools.product(candidates0, candidates1):
                        if c0[1] == c1[1]:
                            #TODO: Better way to report contradiction
                            assert c0[2] * c1[2] == prop.ratio
                            self.__reason(prop, 'Transitivity', [c0[0], c1[0]])
                            found = True
                            break

                    if found:
                        continue

                    try:
                        known_angles = self.__explained.list(AngleValueProperty, prop.keys())
                        left = next(exp for exp in known_angles if exp.angle == prop.angle0)
                        right = next(exp for exp in known_angles if exp.angle == prop.angle1)
                        # TODO: report contradiction, if angle ratio differs
                        if left.degree == right.degree:
                            self.__reason(prop, _comment('Both angle values = %sº', left.degree), premises=[left, right])
                        else:
                            self.__reason(prop, _comment('%s = %sº, %s = %sº', left.angle, left.degree, right.angle, right.degree), premises=[left, right])
                        found = True
                    except StopIteration:
                        pass

                    if found:
                        continue

                    if prop.ratio == 1:
                        similar_triangles = self.__explained.list(SimilarTrianglesProperty, prop.keys())
                        pair = {prop.angle0, prop.angle1}
                        for st in similar_triangles:
                            if pair in angle_pairs(st):
                                self.__reason(prop, 'Corresponding angles in similar triangles', premises=[st])
                                found = True
                                break

                        if found:
                            continue

                    if prop.ratio == 1:
                        congruent_angles = [rsn for rsn in self.__explained.list(AnglesRatioProperty, prop.keys()) if rsn.ratio == 1]
                        for index, ca0 in enumerate(congruent_angles):
                            if prop.angle0 == ca0.angle0:
                                look_for = {prop.angle1, ca0.angle1}
                            elif prop.angle1 == ca0.angle0:
                                look_for = {prop.angle0, ca0.angle1}
                            elif prop.angle0 == ca0.angle1:
                                look_for = {prop.angle1, ca0.angle0}
                            elif prop.angle1 == ca0.angle1:
                                look_for = {prop.angle0, ca0.angle0}
                            else:
                                continue

                            for ca1 in congruent_angles[index + 1:]:
                                if {ca1.angle0, ca1.angle1} == look_for:
                                    self.__reason(prop, 'transitivity', premises=[ca0, ca1])
                                    found = True
                                    break

                            if found:
                                break

                elif isinstance(prop, SimilarTrianglesProperty):
                    try:
                        congruent = next(ct for ct in \
                            self.__explained.list(CongruentTrianglesProperty, prop.keys()) if \
                                (ct.ABC == prop.ABC and ct.DEF == prop.DEF) or \
                                (ct.ABC == prop.DEF and ct.DEF == prop.ABC))
                        self.__reason(prop, 'Congruent triangles are similar', premises=[congruent])
                        continue
                    except StopIteration:
                        pass

                    congruent_angles = [rsn for rsn in self.__explained.list(AnglesRatioProperty, prop.keys([3])) if rsn.ratio == 1]
                    premises = []
                    for ca in congruent_angles:
                        pair = {ca.angle0, ca.angle1}
                        if pair in angle_pairs(prop):
                            premises.append(ca)

                    if len(premises) == 3:
                        self.__reason(prop, 'three angles', premises=premises)
                    elif len(premises) == 2:
                        self.__reason(prop, 'two angles', premises=premises)
                elif isinstance(prop, CongruentTrianglesProperty):
                    equal_distances = self.__explained.list(CongruentSegmentProperty, prop.keys([2]))
                    common_sides = []
                    premises = []
                    for i in range(0, 3):
                        left = side_of(prop.ABC, i)
                        right = side_of(prop.DEF, i)
                        if same_segment(left, right):
                            common_sides.append(left)
                        else:
                            for ed in equal_distances:
                                if same_segment_pair((left, right), (ed.vector0, ed.vector1)):
                                    premises.append(ed)
                                    break
                        if len(common_sides) + len(premises) < i + 1:
                            break
                    else:
                        if len(premises) == 3:
                            self.__reason(prop, 'Three pairs of congruent sides', premises=premises)
                        else: # len(premises) == 2
                            self.__reason(prop, _comment('Common side %s, two pairs of congruent sides', common_sides[0]), premises=premises)
                        continue

                    similar_triangles = self.__explained.list(SimilarTrianglesProperty, prop.keys([3]))
                    for st in similar_triangles:
                        if (st.ABC == prop.ABC and st.DEF == prop.DEF) or \
                           (st.ABC == prop.DEF and st.DEF == prop.ABC):
                            break
                    else:
                        continue
                    for ed in equal_distances:
                        pair = (ed.vector0, ed.vector1)
                        if any(same_segment_pair(pair, sp) for sp in side_pairs(prop)):
                            self.__reason(prop, 'Similar triangles with congruent side', premises=[st, ed])
                            break

                elif isinstance(prop, CongruentSegmentProperty):
                    pair = (prop.vector0, prop.vector1)
                    try:
                        ct = next(rsn for rsn in \
                            self.__explained.list(CongruentTrianglesProperty, prop.keys()) if \
                                any(same_segment_pair(pair, sp) for sp in side_pairs(rsn)))
                        self.__reason(prop, 'Corresponding sides in congruent triangles', premises=[ct])
                        continue
                    except StopIteration:
                        pass

                    key = frozenset([*prop.vector0.points, *prop.vector1.points])
                    if len(key) == 3:
                        try:
                            it = next(rsn for rsn in \
                                self.__explained.list(IsoscelesTriangleProperty, [key]) if \
                                    same_segment_pair(pair, (rsn.A.vector(rsn.BC[0]), rsn.A.vector(rsn.BC[1]))))
                            self.__reason(prop, _comment('Legs of isosceles △ %s %s %s', it.A, *it.BC), premises=[it])
                            continue
                        except StopIteration:
                            pass

                elif isinstance(prop, IsoscelesTriangleProperty):
                    try:
                        angles = {prop.BC[0].angle(prop.BC[1], prop.A), \
                            prop.BC[1].angle(prop.A, prop.BC[0])}
                        ca = next(rsn for rsn in \
                            self.__explained.list(AnglesRatioProperty, prop.keys([3])) if \
                                rsn.ratio == 1 and angles == {rsn.angle0, rsn.angle1})
                        self.__reason(prop, 'Congruent base angles', premises=[ca])
                        continue
                    except StopIteration:
                        pass

                    try:
                        sides = (prop.A.vector(prop.BC[0]), prop.A.vector(prop.BC[1]))
                        cs = next(rsn for rsn in \
                            self.__explained.list(CongruentSegmentProperty, prop.keys([2])) if \
                                same_segment_pair(sides, (rsn.vector0, rsn.vector1)))
                        self.__reason(prop, 'Congruent legs', premises=[cs])
                        continue
                    except StopIteration:
                        pass

                elif isinstance(prop, AngleValueProperty):
                    found = False

                    congruent_angles = [rsn for rsn in self.__explained.list(AnglesRatioProperty, prop.keys()) if rsn.ratio == 1]
                    for ca in congruent_angles:
                        if ca.angle0 == prop.angle:
                            value = self.__angle_value_reason(ca.angle1)
                        elif ca.angle1 == prop.angle:
                            value = self.__angle_value_reason(ca.angle0)
                        else:
                            continue
                        if value:
                            #TODO: report contradiction if degrees are different
                            self.__reason(prop, _comment('%s = %s = %sº', prop.angle, value.angle, value.degree), premises=[ca, value])
                            found = True
                            break

                    if found:
                        continue

                    if prop.angle.vertex is not None:
                        angle = prop.angle
                        first = angle.vector0.end.angle(angle.vector1.end, angle.vertex)
                        second = angle.vector1.end.angle(angle.vertex, angle.vector0.end)
                        pairs = []
                        for ka in self.__explained.list(AngleValueProperty, keys_for_angle(angle)):
                            if ka.angle in (first, second):
                                pairs.append((ka.degree, ka))
                        if len(pairs) >= 2:
                            #TODO: Better way to report contradiction
                            assert prop.degree + pairs[0][0] + pairs[1][0] == 180
                            self.__reason(prop, _comment('%s + %s + %s = 180º', angle, first, second), [pairs[0][1], pairs[1][1]])

                    if found:
                        continue

                    isosceles = self.__explained.list(IsoscelesTriangleProperty, prop.keys())
                    values = self.__explained.list(AngleValueProperty, prop.keys())
                    for iso in isosceles:
                        if prop.angle == iso.BC[0].angle(iso.A, iso.BC[1]):
                            break
                        if prop.angle == iso.BC[1].angle(iso.A, iso.BC[0]):
                            break
                    else:
                        continue
                    for val in values:
                        if val.angle == iso.A.angle(*iso.BC):
                            self.__reason(prop, _comment('Base angle of isosceles △ %s %s %s with apex angle %sº', iso.A, *iso.BC, val.degree), premises=[iso, val])
                        # TODO: check sum of angles; report contradiction if found


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
