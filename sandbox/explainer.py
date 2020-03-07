import itertools
import time

from .core import Constraint, _comment
from .property import *
from .scene import Scene

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
        self.__explained.add(Explainer.Reason(len(self.__explained), prop, comments, premises))

    def __refresh_unexplained(self):
        self.__unexplained = [prop for prop in self.__unexplained if prop not in self.__explained]

    def __add(self, prop, comments, premises=None):
        if prop not in self.__explained:
            self.__reason(prop, comments, premises)

    def explain(self):
        start = time.time()
        self.__explain_all()
        self.__explanation_time = time.time() - start

    def __explain_all(self):
        def base():
            def not_equal(pt0, pt1, comments):
                if not pt0.auxiliary and not pt1.auxiliary:
                    self.__add(NotEqualProperty(pt0, pt1), comments)
            for cnst in self.scene.constraints(Constraint.Kind.not_equal):
                not_equal(cnst.params[0], cnst.params[1], cnst.comments)
            for cnst in self.scene.constraints(Constraint.Kind.not_collinear):
                def adjust(pt0, pt1, pt2):
                    line = self.scene.get_line(pt0, pt1)
                    if line:
                        for pt in line.all_points:
                            if pt == pt0 or pt == pt1:
                                not_equal(pt, pt2, cnst.comments)
                            else:
                                not_equal(pt, pt2, cnst.comments + [_comment('%s lies on the line %s', pt, line)])
                adjust(cnst.params[0], cnst.params[1], cnst.params[2])
                adjust(cnst.params[1], cnst.params[2], cnst.params[0])
                adjust(cnst.params[2], cnst.params[0], cnst.params[1])

            for cnst in self.scene.constraints(Constraint.Kind.same_direction):
                self.__add(
                    SameDirectionProperty(cnst.params[0], cnst.params[1], cnst.params[2]),
                    cnst.comments
                )

            for cnst in self.scene.constraints(Constraint.Kind.opposite_side):
                self.__add(
                    OppositeSideProperty(cnst.params[2], cnst.params[0], cnst.params[1]),
                    cnst.comments
                )
            for cnst in self.scene.constraints(Constraint.Kind.same_side):
                self.__add(
                    SameSideProperty(cnst.params[2], cnst.params[0], cnst.params[1]),
                    cnst.comments
                )
            for cnst in self.scene.constraints(Constraint.Kind.angles_ratio):
                self.__add(
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

        def iteration():
            same_side_reasons = self.__explained.list(SameSideProperty)
            for rsn in same_side_reasons:
                pt0 = rsn.property.points[0]
                pt1 = rsn.property.points[1]
                line2 = self.scene.get_line(pt0, pt1)
                if line2 is None:
                    continue
                crossing = self.scene.get_intersection(rsn.property.line, line2)
                if crossing:
                    self.__add(SameDirectionProperty(crossing, pt0, pt1), rsn.comments)

            for rsn0, rsn1 in itertools.combinations(same_side_reasons, 2):
                AB = rsn0.property.line
                AC = rsn1.property.line
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
                if X:
                    comments = rsn0.comments
                    for com in rsn1.comments:
                        if not com in comments:
                            comments.append(com)
                    self.__add(SameDirectionProperty(X, A, D), comments)
                    self.__add(SameDirectionProperty(A, D, X), comments)
                    self.__add(SameDirectionProperty(B, C, X), comments)
                    self.__add(SameDirectionProperty(C, B, X), comments)

            same_direction = self.__explained.list(SameDirectionProperty)
            def same_dir(vector):
                yield (vector, [])
                for sd in same_direction:
                    if sd.property.start == vector.start:
                        if sd.property.points[0] == vector.end:
                            yield (sd.property.start.vector(sd.property.points[1]), [sd])
                        elif sd.property.points[1] == vector.end:
                            yield (sd.property.start.vector(sd.property.points[0]), [sd])
                    if sd.property.start == vector.end:
                        if sd.property.points[0] == vector.start:
                            yield (sd.property.points[1].vector(sd.property.start), [sd])
                        elif sd.property.points[1] == vector.start:
                            yield (sd.property.points[0].vector(sd.property.start), [sd])

            for prop in list(self.__unexplained):
                if isinstance(prop, AnglesRatioProperty) and prop.ratio == 1:
                    found = False
                    for v0, sd0 in same_dir(prop.angle0.vector0):
                        lst = list(same_dir(prop.angle0.vector1))
                        def add_reason(vector0, vector1):
                            if v0 == vector0:
                                try:
                                    found = next(p for p in lst if p[0] == vector1)
                                    self.__reason(prop, 'Same angle', premises=sd0 + found[1])
                                    return True
                                except:
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

                    known_angles = self.__explained.list(AngleValueProperty, prop.keys())
                    premises = [exp for exp in known_angles if exp.property.angle in [prop.angle0, prop.angle1]]
                    if len(premises) == 2 and premises[0].property.degree == premises[1].property.degree:
                        self.__reason(prop, _comment('Both angle values = %sº', premises[0].property.degree), premises=premises)
                        found = True
                    # TODO: report contradiction, if not angle values are not equal

                    if found:
                        continue

                    similar_triangles = self.__explained.list(SimilarTrianglesProperty, prop.keys())
                    pair = (prop.angle0, prop.angle1)
                    for st in similar_triangles:
                        if any(same_pair(pair, ap) for ap in angle_pairs(st.property)):
                            self.__reason(prop, 'Corresponding angles in similar triangles', premises=[st])
                            found = True
                            break

                    if found:
                        continue

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
                    similar_triangles = self.__explained.list(SimilarTrianglesProperty, prop.keys([3]))
                    equal_distances = self.__explained.list(CongruentSegmentProperty, prop.keys([2]))
                    for st in similar_triangles:
                        if (st.property.ABC == prop.ABC and st.property.DEF == prop.DEF) or \
                           (st.property.ABC == prop.DEF and st.property.DEF == prop.ABC):
                            break
                    else:
                        continue
                    for ed in equal_distances:
                        pair = (ed.property.vector0, ed.property.vector1)
                        if any(same_pair(pair, sp) for sp in side_pairs(prop)):
                            self.__reason(prop, 'Similar triangles with equal side', premises=[st, ed])

                elif isinstance(prop, CongruentSegmentProperty):
                    equal_triangles = self.__explained.list(CongruentTrianglesProperty, prop.keys())
                    pair = (prop.vector0, prop.vector1)
                    for et in equal_triangles:
                        if any(same_pair(pair, sp) for sp in side_pairs(et.property)):
                            self.__reason(prop, 'Corresponding sides in equal triangles', premises=[et])
                            break

                elif isinstance(prop, IsoscelesTriangleProperty):
                    sides = (prop.A.vector(prop.BC[0]), prop.A.vector(prop.BC[1]))
                    equal_distances = self.__explained.list(CongruentSegmentProperty, prop.keys([2]))
                    for ed in equal_distances:
                        if same_pair(sides, (ed.property.vector0, ed.property.vector1)):
                            self.__reason(prop, 'Two equal sides', premises=[ed])

                elif isinstance(prop, AngleValueProperty):
                    found = False
                    if prop.degree == 0:
                        same_direction = self.__explained.list(SameDirectionProperty)
                        for sd in same_direction:
                            if prop.angle.vector0.start == sd.property.start and prop.angle.vector1.start == sd.property.start and set([prop.angle.vector0.end, prop.angle.vector1.end]) == set(sd.property.points):
                                self.__reason(prop, 'TBW', premises=[sd])
                                found = True
                                break

                    if found:
                        continue

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
        for exp in self.__explained.all:
            print('\t%2d: %s [%s]' % (exp.index, exp.property, exp))
        print('\nNot explained:')
        for prop in self.__unexplained:
            print('\t%s' % prop)

    def stats(self):
        return [
            ('Total properties', len(self.__explained) + len(self.__unexplained)),
            ('Explained properties', len(self.__explained)),
            ('Explained property keys', self.__explained.keys_num()),
            ('Unexplained properties', len(self.__unexplained)),
            ('Iterations', self.__iteration_step_count),
            ('Explanation time', '%.3f sec' % self.__explanation_time),
        ]

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
    def __init__(self, point0, point1):
        self.points = [point0, point1]

    @property
    def description(self):
        return _comment('%s != %s', *self.points)

    def __eq__(self, other):
        return isinstance(other, NotEqualProperty) and set(self.points) == set(other.points)

class SameDirectionProperty(Property):
    def __init__(self, start, point0, point1):
        self.start = start
        self.points = [point0, point1]

    @property
    def description(self):
        return _comment('%s, %s in the same direction from %s', *self.points, self.start)

    def __eq__(self, other):
        if not isinstance(other, SameDirectionProperty):
            return False
        return self.start == other.start and set(self.points) == set(other.points)

class OppositeSideProperty(Property):
    def __init__(self, line, point0, point1):
        self.line = line
        self.points = [point0, point1]

    @property
    def description(self):
        return _comment('%s, %s located on opposite sides of %s', *self.points, self.line)

    def __eq__(self, other):
        if not isinstance(other, OppositeSideProperty):
            return False
        return self.line == other.line and set(self.points) == set(other.points)

class SameSideProperty(Property):
    def __init__(self, line, point0, point1):
        self.line = line
        self.points = [point0, point1]

    @property
    def description(self):
        return _comment('%s, %s located on the same side of %s', *self.points, self.line)

    def __eq__(self, other):
        if not isinstance(other, SameSideProperty):
            return False
        return self.line == other.line and set(self.points) == set(other.points)
