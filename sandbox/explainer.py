import itertools
import time
import numpy as np
import sympy as sp

from .core import Constraint, _comment
from .property import *
from .scene import Scene
from .stats import Stats

# +++++ utility methods +++++
def same(obj0, obj1): #same segment or angle
    return obj0 == obj1 or obj0 == obj1.reversed

def same_pair(pair0, pair1):
    return same(pair0[0], pair1[0]) and same(pair0[1], pair1[1]) \
        or same(pair0[0], pair1[1]) and same(pair0[1], pair1[0])

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
        prop.angle_pairs = [[angle_of(t, i) for t in (prop.ABC, prop.DEF)] for i in range(0, 3)]
    return prop.angle_pairs
# ----- utility methods -----

class Explainer:
    class Reason:
        def __init__(self, index, prop, comments, premises):
            self.index = index
            self.property = prop
            if not isinstance(comments, (list, tuple)):
                self.comments = [comments]
            else:
                self.comments = list(comments)
            self.premises = premises

        def __str__(self):
            if self.premises:
                return '%s (%s)' % (
                    ', '.join([str(com) for com in self.comments]),
                    ', '.join(['*%d' % rsn.index for rsn in self.premises])
                )
            else:
                return ', '.join([str(com) for com in self.comments])

    class ReasonSet:
        class ByType:
            def __init__(self):
                self.all = []
                self.by_key_map = {}

        def __init__(self):
            self.by_type_map = {}

        def add(self, reason):
            key = type(reason.property)
            by_type = self.by_type_map.get(key)
            if by_type is None:
                by_type = Explainer.ReasonSet.ByType()
                self.by_type_map[key] = by_type
            by_type.all.append(reason)
            for key in reason.property.keys():
                arr = by_type.by_key_map.get(key)
                if arr is None:
                    arr = [reason]
                    by_type.by_key_map[key] = arr
                else:
                    arr.append(reason)

        def list(self, property_type, keys=None):
            by_type = self.by_type_map.get(property_type)
            if not by_type:
                return []
            if keys:
                assert isinstance(keys, list)
                sublists = [by_type.by_key_map.get(k) for k in keys]
                return list(set(itertools.chain(*[l for l in sublists if l])))
            else:
                return by_type.all

        def __len__(self):
            return sum(len(by_type.all) for by_type in self.by_type_map.values())

        @property
        def all(self):
            return list(itertools.chain(*[by_type.all for by_type in self.by_type_map.values()]))

        def __contains__(self, prop):
            return any(prop == rsn.property for rsn in self.list(type(prop), prop.keys()))

        def keys_num(self):
            return sum(len(by_type.by_key_map) for by_type in self.by_type_map.values())

    def __init__(self, scene, properties):
        self.scene = scene
        self.__explained = Explainer.ReasonSet()
        self.__unexplained = list(properties)
        self.__explanation_time = None
        self.__iteration_step_count = None

    def __reason(self, prop, comments, premises=None):
        if prop not in self.__explained:
            self.__explained.add(Explainer.Reason(len(self.__explained), prop, comments, premises))

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

    def __explain_all(self):
        def base():
            for cnst in self.scene.constraints(Constraint.Kind.not_equal):
                self.__reason(NotEqualProperty(cnst.params[0], cnst.params[1]), cnst.comments)
            for cnst in self.scene.constraints(Constraint.Kind.not_collinear):
                self.__reason(NonCollinearProperty(*cnst.params), cnst.comments)
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
                    for line in self.scene.lines():
                        if all(p in line for p in prop.points):
                            self.__reason(prop, 'Given')
                            break
                elif isinstance(prop, AngleValueProperty) and prop.degree == 0:
                    for cnst in self.scene.constraints(Constraint.Kind.same_direction):
                        if same(prop.angle, cnst.params[0].angle(*cnst.params[1:])):
                             self.__reason(prop, cnst.comments)
                elif isinstance(prop, AngleValueProperty) and prop.degree == 90:
                    for cnst in self.scene.constraints(Constraint.Kind.perpendicular):
                        line0 = cnst.params[0]
                        line1 = cnst.params[1]
                        if prop.angle.vector0 in line0 and prop.angle.vector1 in line1:
                            self.__reason(prop, cnst.comments)
                        elif prop.angle.vector0 in line1 and prop.angle.vector1 in line0:
                            self.__reason(prop, cnst.comments)
                elif isinstance(prop, CongruentSegmentProperty):
                    for cnst in self.scene.constraints(Constraint.Kind.distances_ratio):
                        if cnst.params[2] == 1:
                            if same_pair(cnst.params[0:2], (prop.vector0, prop.vector1)):
                                self.__reason(prop, 'Given')

        def not_equal_reason(pt0, pt1):
            key = frozenset([pt0, pt1])
            return next((r for r in self.__explained.list(NotEqualProperty, keys=[key])), None)

        def iteration():
            for ncl in self.__explained.list(NonCollinearProperty):
                def extra_comments(pt, pt0, pt1):
                    return [_comment('%s lies on the line %s %s', pt, pt0, pt1)]

                def add_reasons(pt0, pt1, pt2):
                    line = self.scene.get_line(pt0, pt1)
                    if line:
                        for pt in line.all_points:
                            if pt in (pt0, pt1):
                                self.__reason(NotEqualProperty(pt, pt2), str(ncl.property))
                            else:
                                self.__reason(NotEqualProperty(pt, pt2), [str(ncl.property)] + extra_comments(pt, pt0, pt1))
                        for ptX, ptY in itertools.combinations(line.all_points, 2):
                            ne = not_equal_reason(ptX, ptY)
                            if ne is None:
                                continue
                            comments = [str(ncl.property)]
                            if not ptX in (pt0, pt1):
                                comments += extra_comments(ptX, pt0, pt1)
                            if not ptY in (pt0, pt1):
                                comments += extra_comments(ptY, pt0, pt1)
                            self.__reason(NonCollinearProperty(ptX, ptY, pt2), comments, [ncl, ne])

                add_reasons(ncl.property.points[0], ncl.property.points[1], ncl.property.points[2])
                add_reasons(ncl.property.points[1], ncl.property.points[2], ncl.property.points[0])
                add_reasons(ncl.property.points[2], ncl.property.points[0], ncl.property.points[1])

            for cs in self.__explained.list(CongruentSegmentProperty):
                vec0 = cs.property.vector0
                vec1 = cs.property.vector1

                ne0 = not_equal_reason(*vec0.points)
                ne1 = not_equal_reason(*vec1.points)
                if ne0 is not None and ne1 is None:
                    self.__reason(NotEqualProperty(*vec1.points), [], [cs, ne0])
                elif ne1 is not None and ne0 is None:
                    self.__reason(NotEqualProperty(*vec0.points), [], [cs, ne1])
                elif ne0 is None and ne1 is None:
                    ne = None
                    if vec0.start == vec1.start:
                        ne = not_equal_reason(vec0.end, vec1.end)
                    elif vec0.start == vec1.end:
                        ne = not_equal_reason(vec0.end, vec1.start)
                    elif vec0.end == vec1.start:
                        ne = not_equal_reason(vec0.start, vec1.end)
                    elif vec0.end == vec1.end:
                        ne = not_equal_reason(vec0.start, vec1.start)
                    if ne:
                        self.__reason(NotEqualProperty(*vec0.points), [], [cs, ne])
                        self.__reason(NotEqualProperty(*vec1.points), [], [cs, ne])

            for pv in self.__explained.list(ParallelVectorsProperty):
                vec0 = pv.property.vector0
                vec1 = pv.property.vector1
                ne0 = not_equal_reason(*vec0.points)
                ne1 = not_equal_reason(*vec1.points)
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
                pt0 = rsn.property.points[0]
                pt1 = rsn.property.points[1]
                line2 = self.scene.get_line(pt0, pt1)
                if line2 is None:
                    continue
                crossing = self.scene.get_intersection(rsn.property.line, line2)
                if crossing:
                    self.__reason(AngleValueProperty(crossing.angle(pt0, pt1), 0), rsn.comments, [rsn])

            for rsn0, rsn1 in itertools.combinations(same_side_reasons, 2):
                AB = rsn0.property.line
                AC = rsn1.property.line
                if AB == AC:
                    continue
                A = self.scene.get_intersection(AB, AC)
                if A is None:
                    continue
                pt00 = rsn0.property.points[0]
                pt01 = rsn0.property.points[1]
                pt10 = rsn1.property.points[0]
                pt11 = rsn1.property.points[1]
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
                rsn.property.degree == 0 and rsn.property.angle.vertex is not None]

            for sd in same_direction:
                vertex = sd.property.angle.vertex
                pt0 = sd.property.angle.vector0.end
                pt1 = sd.property.angle.vector1.end
                for nc in self.__explained.list(NonCollinearProperty):
                    params = set(nc.property.points)
                    if vertex in params:
                        params.remove(vertex)
                        if pt0 in params and pt1 not in params:
                            params.remove(pt0)
                            line = self.scene.get_line(vertex, params.pop())
                            if line:
                                self.__reason(SameSideProperty(line, pt0, pt1), [str(sd.property), str(nc.property)], [sd, nc])
                        elif pt1 in params and pt0 not in params:
                            params.remove(pt1)
                            line = self.scene.get_line(vertex, params.pop())
                            if line:
                                self.__reason(SameSideProperty(line, pt0, pt1), [str(sd.property), str(nc.property)], [sd, nc])

            for sd in same_direction:
                angle = sd.property.angle
                vec0 = angle.vector0
                vec1 = angle.vector1

                for ne in self.__explained.list(NotEqualProperty, keys=[angle.vertex]):
                    vector = ne.property.points[0].vector(ne.property.points[1])
                    if vector.start != angle.vertex:
                        vector = vector.reversed
                    if len(set(vector.points + vec0.points)) < 3 or len(set(vector.points + vec1.points)) < 3:
                        continue
                    self.__reason(AnglesRatioProperty(vec0.angle(vector), vec1.angle(vector), 1), [], [sd])

            def same_dir(vector):
                yield (vector, [])
                for sd in same_direction:
                    vertex = sd.property.angle.vertex
                    pt0 = sd.property.angle.vector0.end
                    pt1 = sd.property.angle.vector1.end
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
                a0 = ar.property.angle0
                a1 = ar.property.angle1
                if a0.vertex is None or a0.vertex != a1.vertex:
                    continue
                if a0.vector1.end == a1.vector0.end:
                    angle = a0.vertex.angle(a0.vector0.end, a1.vector1.end) #a0 + a1
                    is_sum = True
                    if not point_inside_angle(a0.vector1.end, angle):
                        continue
                elif a0.vector0.end == a1.vector1.end:
                    angle = a0.vertex.angle(a1.vector0.end, a0.vector1.end) #a0 + a1
                    is_sum = True
                    if not point_inside_angle(a0.vector0.end, angle):
                        continue
                elif a0.vector0.end == a1.vector0.end:
                    angle = a0.vertex.angle(a1.vector1.end, a0.vector1.end) #a0 - a1
                    is_sum = False
                    continue
                elif a0.vector1.end == a1.vector1.end:
                    angle = a0.vertex.angle(a0.vector0.end, a1.vector0.end) #a0 - a1
                    is_sum = False
                    continue
                else:
                    continue
                for ka in self.__explained.list(AngleValueProperty):
                    if ka.property.angle == angle:
                        value = ka.property.degree
                        break
                    elif ka.property.angle == angle.reversed:
                        value = -ka.property.degree
                        break
                else:
                    continue
                if is_sum:
                    if ar.property.ratio == -1:
                        continue
                    second = value / (1 + ar.property.ratio)
                    first = value - second
                else:
                    if ar.property.ratio == 1:
                        continue
                    second = value / (ar.property.ratio - 1)
                    first = value + second
                #TODO: write comments
                self.__reason(AngleValueProperty(a0, first), [], premises=[ar, ka])
                self.__reason(AngleValueProperty(a1, second), [], premises=[ar, ka])

            for ka in self.__explained.list(AngleValueProperty):
                base = ka.property.angle
                if ka.property.degree == 0 or ka.property.degree == 180 or base.vertex is None:
                    continue
                for vec0, vec1, sign in [(base.vector0, base.vector1, 1), (base.vector1, base.vector0, -1)]:
                    line = vec0.line()
                    if line:
                        for pt in line.all_points:
                            if pt in vec0.points:
                                continue
                            angle_to_look = pt.angle(vec1.end, base.vertex)
                            keys = keys_for_angle(angle_to_look)
                            for ka2 in self.__explained.list(AngleValueProperty, keys):
                                if not same(ka2.property.angle, angle_to_look):
                                    continue
                                if ka2.property.angle == angle_to_look:
                                    degree2 = ka2.property.degree * sign
                                else:
                                    degree2 = -ka2.property.degree * sign
                                # angles have same sign
                                if ka.property.degree * degree2 < 0:
                                    #TODO: replace degree2 with 180 - degree2 (?)
                                    break
                                found = base.vertex.angle(vec0.end, pt)
                                angle_sum = np.abs(ka.property.degree + degree2)
                                if angle_sum < 180:
                                    comment = _comment(
                                        '%s lies on the side %s of %s; %s + %s < 180º',
                                        pt, vec0, base, base, angle_to_look
                                    )
                                    self.__reason(AngleValueProperty(found, 0), comment, [ka, ka2])
                                elif angle_sum > 180:
                                    #TODO: add properties
                                    pass
                                else:
                                    #TODO: add property: pt == base.vertex
                                    pass
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
                        if prop.angle0 == kr.property.angle0:
                            candidates0.append((kr, kr.property.angle1, kr.property.ratio))
                        elif prop.angle0.reversed == kr.property.angle0:
                            candidates0.append((kr, kr.property.angle1, -kr.property.ratio))
                        elif prop.angle0 == kr.property.angle1:
                            candidates0.append((kr, kr.property.angle0, sp.sympify(1) / kr.property.ratio))
                        elif prop.angle0.reversed == kr.property.angle1:
                            candidates0.append((kr, kr.property.angle0, sp.sympify(-1) / kr.property.ratio))
                        elif prop.angle1 == kr.property.angle0:
                            candidates1.append((kr, kr.property.angle1, sp.sympify(1) / kr.property.ratio))
                        elif prop.angle1.reversed == kr.property.angle0:
                            candidates1.append((kr, kr.property.angle1, sp.sympify(-1) / kr.property.ratio))
                        elif prop.angle1 == kr.property.angle1:
                            candidates1.append((kr, kr.property.angle0, kr.property.ratio))
                        elif prop.angle1.reversed == kr.property.angle1:
                            candidates1.append((kr, kr.property.angle0, -kr.property.ratio))
                    for c0, c1 in itertools.product(candidates0, candidates1):
                        if c0[1] == c1[1]:
                            #TODO: Better way to report contradiction
                            assert c0[2] * c1[2] == prop.ratio
                            self.__reason(prop, 'Transitivity', [c0[0], c1[0]])
                            found = True
                            break
                        elif c0[1] == c1[1].reversed:
                            #TODO: Better way to report contradiction
                            assert c0[2] * c1[2] == -prop.ratio
                            self.__reason(prop, 'Transitivity', [c0[0], c1[0]])
                            found = True
                            break

                    if found:
                        continue

                    try:
                        known_angles = self.__explained.list(AngleValueProperty, prop.keys())
                        left = next(exp for exp in known_angles if exp.property.angle == prop.angle0)
                        right = next(exp for exp in known_angles if exp.property.angle == prop.angle1)
                        # TODO: report contradiction, if angle ratio differs
                        if left.property.degree == right.property.degree:
                            self.__reason(prop, _comment('Both angle values = %sº', left.property.degree), premises=[left, right])
                        else:
                            self.__reason(prop, _comment('%s = %sº, %s = %sº', left.property.angle, left.property.degree, right.property.angle, right.property.degree), premises=[left, right])
                        found = True
                    except StopIteration:
                        pass

                    if found:
                        continue

                    if prop.ratio == 1:
                        similar_triangles = self.__explained.list(SimilarTrianglesProperty, prop.keys())
                        pair = (prop.angle0, prop.angle1)
                        for st in similar_triangles:
                            if any(same_pair(pair, ap) for ap in angle_pairs(st.property)):
                                self.__reason(prop, 'Corresponding angles in similar triangles', premises=[st])
                                found = True
                                break

                        if found:
                            continue

                    if prop.ratio == 1:
                        congruent_angles = [rsn for rsn in self.__explained.list(AnglesRatioProperty, prop.keys()) if rsn.property.ratio == 1]
                        for index, ca0 in enumerate(congruent_angles):
                            if prop.angle0 == ca0.property.angle0:
                                look_for = [prop.angle1, ca0.property.angle1]
                            elif prop.angle1 == ca0.property.angle0:
                                look_for = [prop.angle0, ca0.property.angle1]
                            elif prop.angle0 == ca0.property.angle1:
                                look_for = [prop.angle1, ca0.property.angle0]
                            elif prop.angle1 == ca0.property.angle1:
                                look_for = [prop.angle0, ca0.property.angle0]
                            else:
                                continue

                            for ca1 in congruent_angles[index + 1:]:
                                if ca1.property.angle0 in look_for and ca1.property.angle1 in look_for:
                                    self.__reason(prop, 'transitivity', premises=[ca0, ca1])
                                    found = True
                                    break

                            if found:
                                break

                elif isinstance(prop, SimilarTrianglesProperty):
                    try:
                        congruent = next(ct for ct in \
                            self.__explained.list(CongruentTrianglesProperty, prop.keys()) if \
                                (ct.property.ABC == prop.ABC and ct.property.DEF == prop.DEF) or \
                                (ct.property.ABC == prop.DEF and ct.property.DEF == prop.ABC))
                        self.__reason(prop, 'Congruent triangles are similar', premises=[congruent])
                        continue
                    except StopIteration:
                        pass

                    congruent_angles = [rsn for rsn in self.__explained.list(AnglesRatioProperty, prop.keys([3])) if rsn.property.ratio == 1]
                    premises = []
                    for ca in congruent_angles:
                        pair = (ca.property.angle0, ca.property.angle1)
                        if any(same_pair(pair, ap) for ap in angle_pairs(prop)):
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
                        if same(left, right):
                            common_sides.append(left)
                        else:
                            for ed in equal_distances:
                                if same_pair((left, right), (ed.property.vector0, ed.property.vector1)):
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
                        if (st.property.ABC == prop.ABC and st.property.DEF == prop.DEF) or \
                           (st.property.ABC == prop.DEF and st.property.DEF == prop.ABC):
                            break
                    else:
                        continue
                    for ed in equal_distances:
                        pair = (ed.property.vector0, ed.property.vector1)
                        if any(same_pair(pair, sp) for sp in side_pairs(prop)):
                            self.__reason(prop, 'Similar triangles with congruent side', premises=[st, ed])

                elif isinstance(prop, CongruentSegmentProperty):
                    pair = (prop.vector0, prop.vector1)
                    try:
                        ct = next(rsn for rsn in \
                            self.__explained.list(CongruentTrianglesProperty, prop.keys()) if \
                                any(same_pair(pair, sp) for sp in side_pairs(rsn.property)))
                        self.__reason(prop, 'Corresponding sides in congruent triangles', premises=[ct])
                        continue
                    except StopIteration:
                        pass

                    key = frozenset([*prop.vector0.points, *prop.vector1.points])
                    if len(key) == 3:
                        try:
                            it = next(rsn for rsn in \
                                self.__explained.list(IsoscelesTriangleProperty, [key]) if \
                                    same_pair(pair, (rsn.property.A.vector(rsn.property.BC[0]), rsn.property.A.vector(rsn.property.BC[1]))))
                            self.__reason(prop, _comment('Legs of isosceles △ %s %s %s', it.property.A, *it.property.BC), premises=[it])
                            continue
                        except StopIteration:
                            pass

                elif isinstance(prop, IsoscelesTriangleProperty):
                    try:
                        angles = (prop.BC[0].angle(prop.BC[1], prop.A), prop.BC[1].angle(prop.A, prop.BC[0]))
                        ca = next(rsn for rsn in \
                            self.__explained.list(AnglesRatioProperty, prop.keys([3])) if \
                                rsn.property.ratio == 1 and \
                                same_pair(angles, (rsn.property.angle0, rsn.property.angle1)))
                        self.__reason(prop, 'Congruent base angles', premises=[ca])
                        continue
                    except StopIteration:
                        pass

                    try:
                        sides = (prop.A.vector(prop.BC[0]), prop.A.vector(prop.BC[1]))
                        cs = next(rsn for rsn in \
                            self.__explained.list(CongruentSegmentProperty, prop.keys([2])) if \
                                same_pair(sides, (rsn.property.vector0, rsn.property.vector1)))
                        self.__reason(prop, 'Congruent legs', premises=[cs])
                        continue
                    except StopIteration:
                        pass

                elif isinstance(prop, AngleValueProperty):
                    found = False

                    congruent_angles = [rsn for rsn in self.__explained.list(AnglesRatioProperty, prop.keys()) if rsn.property.ratio == 1]
                    for ca in congruent_angles:
                        if ca.property.angle0 == prop.angle:
                            angle_values = self.__explained.list(AngleValueProperty, keys_for_angle(ca.property.angle1))
                            for av in angle_values:
                                if av.property.angle == ca.property.angle1:
                                    #TODO: report contradiction if degrees are different
                                    self.__reason(prop, _comment('%s = %s = %sº', prop.angle, av.property.angle, av.property.degree), premises=[ca, av])
                                    found = True
                                    break
                            if found:
                                break
                        elif ca.property.angle1 == prop.angle:
                            angle_values = self.__explained.list(AngleValueProperty, keys_for_angle(ca.property.angle0))
                            for av in angle_values:
                                if av.property.angle == ca.property.angle0:
                                    #TODO: report contradiction if degrees are different
                                    self.__reason(prop, _comment('%s = %s = %sº', prop.angle, av.property.angle, av.property.degree), premises=[ca, av])
                                    found = True
                                    break
                            if found:
                                break

                    if found:
                        continue

                    if prop.angle.vertex is not None:
                        angle = prop.angle
                        first = angle.vector0.end.angle(angle.vector1.end, angle.vertex)
                        second = angle.vector1.end.angle(angle.vertex, angle.vector0.end)
                        pairs = []
                        for ka in self.__explained.list(AngleValueProperty, keys_for_angle(angle)):
                            if ka.property.angle in (first, second):
                                pairs.append((ka.property.degree, ka))
                            if ka.property.angle.reversed in (first, second):
                                pairs.append((-ka.property.degree, ka))
                        if len(pairs) >= 2:
                            #TODO: Better way to report contradiction
                            assert np.abs(prop.degree + pairs[0][0] + pairs[1][0]) == 180
                            self.__reason(prop, _comment('%s + %s + %s = 180º', angle, first, second), [pairs[0][1], pairs[1][1]])

                    if found:
                        continue

                    isosceles = self.__explained.list(IsoscelesTriangleProperty, prop.keys())
                    values = self.__explained.list(AngleValueProperty, prop.keys())
                    for iso in isosceles:
                        if same(prop.angle, iso.property.BC[0].angle(iso.property.A, iso.property.BC[1])):
                            break
                        if same(prop.angle, iso.property.BC[1].angle(iso.property.A, iso.property.BC[0])):
                            break
                    else:
                        continue
                    for val in values:
                        if same(val.property.angle, iso.property.A.angle(*iso.property.BC)):
                            self.__reason(prop, _comment('Base angle of isosceles △ %s %s %s with apex angle %s', iso.property.A, *iso.property.BC, val.property.degree), premises=[iso, val])
                        # TODO: check sum of angles; report contradiction if found


        base()
        self.__iteration_step_count = 0
        self.__refresh_unexplained()
        while len(self.__unexplained) > 0:
            explained_size = len(self.__explained)
            iteration()
            self.__iteration_step_count += 1
            self.__refresh_unexplained()
            if len(self.__explained) == explained_size:
                break

    def dump(self):
        print('Explained:')
        explained = self.__explained.all
        explained.sort(key=lambda rsn: rsn.index)
        for rsn in explained:
            print('\t%2d: %s [%s]' % (rsn.index, rsn.property, rsn))
        print('\nNot explained:')
        for prop in self.__unexplained:
            print('\t%s' % prop)

    def stats(self):
        def type_presentation(kind):
            return kind.__doc__.strip() if kind.__doc__ else kind.__name__

        explained_by_kind = {}
        for rsn in self.__explained.all:
            kind = type(rsn.property)
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
                    if prop.angle == obj:
                        return prop.degree
                    if prop.angle.reversed == obj:
                        return -prop.degree
            return None
        raise Exception('Guess not supported for objects of type %s' % type(obj).__name__)

    def explained(self, obj):
        if isinstance(obj, Scene.Angle):
            for exp in self.__explained.list(AngleValueProperty):
                if exp.property.angle == obj:
                    return exp.property.degree
                if exp.property.angle.reversed == obj:
                    return -exp.property.degree
            return None
        raise Exception('Explanation not supported for objects of type %s' % type(obj).__name__)

    def explanation(self, obj):
        if isinstance(obj, Scene.Angle):
            for exp in self.__explained.list(AngleValueProperty):
                if obj in (exp.property.angle, exp.property.angle.reversed):
                    return exp
        return None

class NotEqualProperty(Property):
    """
    The distance between two points is non-zero
    """
    def __init__(self, point0, point1):
        self.points = [point0, point1]

    def keys(self):
        return [frozenset(self.points), *self.points]

    @property
    def description(self):
        return _comment('%s != %s', *self.points)

    def __eq__(self, other):
        return isinstance(other, NotEqualProperty) and set(self.points) == set(other.points)

class OppositeSideProperty(Property):
    """
    Two points are located on opposite sides of the line
    """
    def __init__(self, line, point0, point1):
        self.line = line
        self.points = [point0, point1]

    def keys(self):
        return [frozenset([self.line] + self.points)]

    @property
    def description(self):
        return _comment('%s, %s located on opposite sides of %s', *self.points, self.line)

    def __eq__(self, other):
        if not isinstance(other, OppositeSideProperty):
            return False
        return self.line == other.line and set(self.points) == set(other.points)

class SameSideProperty(Property):
    """
    Two points are located on the same side of the line
    """
    def __init__(self, line, point0, point1):
        self.line = line
        self.points = [point0, point1]

    def keys(self):
        return [frozenset([self.line] + self.points)]

    @property
    def description(self):
        return _comment('%s, %s located on the same side of %s', *self.points, self.line)

    def __eq__(self, other):
        if not isinstance(other, SameSideProperty):
            return False
        return self.line == other.line and set(self.points) == set(other.points)
