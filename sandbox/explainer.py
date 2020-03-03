import sympy as sp

from .core import Constraint, _comment
from .hunter import *
from .property import *

class Explainer:
    class Reason:
        def __init__(self, index, prop, comments, roots):
            self.index = index
            self.property = prop
            if not isinstance(comments, (list, tuple)):
                self.comments = [comments]
            else:
                self.comments = list(comments)
            self.roots = roots

        def __str__(self):
            if self.roots:
                return '%s (%s)' % (
                    ', '.join([str(com) for com in self.comments]),
                    ', '.join(['*%d' % rsn.index for rsn in self.roots])
                )
            else:
                return ', '.join([str(com) for com in self.comments])

    def __init__(self, scene, properties):
        self.scene = scene
        self.properties = properties
        self.explained = []
        self.unexplained = list(properties)

    def __reason(self, prop, comments, roots=None):
        self.explained.append(Explainer.Reason(len(self.explained), prop, comments, roots))
        if prop in self.unexplained:
            self.unexplained.remove(prop)

    def __add(self, prop, comments, roots=None):
        if prop not in self.properties:
            self.properties.append(prop)
            self.__reason(prop, comments, roots)

    def explain(self):
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
                                not_equal(pt, pt2, cnst.comments + [_comment('%s lies on the line %s %s', pt, pt0, pt1)])
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

            for prop in list(self.unexplained):
                if isinstance(prop, CollinearProperty):
                    for line in self.scene.lines():
                        if all(p in line for p in prop.points):
                            self.__reason(prop, 'Given')
                            break
                elif isinstance(prop, AngleValueProperty) and prop.degree == 0:
                    def is_angle(angle, vertex, points):
                        return angle.vector0.start == vertex and angle.vector1.start == vertex and set([angle.vector0.end, angle.vector1.end]) == set(points)
                    for cnst in self.scene.constraints(Constraint.Kind.same_direction):
                        if is_angle(prop.angle, cnst.params[0], cnst.params[1:]):
                             self.__reason(prop, cnst.comments)
                elif isinstance(prop, AngleValueProperty) and prop.degree == 90:
                    for cnst in self.scene.constraints(Constraint.Kind.perpendicular):
                        line0 = cnst.params[0]
                        line1 = cnst.params[1]
                        if prop.angle.vector0 in line0:
                            if prop.angle.vector1 in line1:
                                self.__reason(prop, cnst.comments)
                        elif prop.angle.vector0 in line1:
                            if prop.angle.vector1 in line0:
                                self.__reason(prop, cnst.comments)
                elif isinstance(prop, CongruentSegmentProperty):
                    for cnst in self.scene.constraints(Constraint.Kind.distances_ratio):
                        if cnst.params[4] == cnst.params[5]:
                            first = set(cnst.params[0:2])
                            second = set(cnst.params[2:4])
                            if first == set(prop.AB) and second == set(prop.CD):
                                self.__reason(prop, 'Given')
                            elif first == set(prop.CD) and second == set(prop.AB):
                                self.__reason(prop, 'Given')

        def iteration():
            same_side_reasons = [rsn for rsn in self.explained if isinstance(rsn.property, SameSideProperty)]
            for rsn in same_side_reasons:
                pt0 = rsn.property.points[0]
                pt1 = rsn.property.points[1]
                line2 = self.scene.get_line(pt0, pt1)
                if line2 is None:
                    continue
                crossing = self.scene.get_intersection(rsn.property.line, line2)
                if crossing:
                    self.__add(SameDirectionProperty(crossing, pt0, pt1), rsn.comments)

            for index, rsn0 in enumerate(same_side_reasons):
                for rsn1 in same_side_reasons[index + 1:]:
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

            same_direction = [exp for exp in self.explained if isinstance(exp.property, SameDirectionProperty)]
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

            for prop in list(self.unexplained):
                if isinstance(prop, CongruentAnglesProperty):
                    found = False
                    for v0, sd0 in same_dir(prop.angle0.vector0):
                        lst = list(same_dir(prop.angle0.vector1))
                        def add_reason(vector0, vector1):
                            if v0 == vector0:
                                try:
                                    found = next(p for p in lst if p[0] == vector1)
                                    self.__reason(prop, 'Same angle', roots=sd0 + found[1])
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

                    known_angles = [exp for exp in self.explained if isinstance(exp.property, AngleValueProperty)]
                    roots = [exp for exp in known_angles if exp.property.angle in [prop.angle0, prop.angle1]]
                    if len(roots) == 2 and roots[0].property.degree == roots[1].property.degree:
                        self.__reason(prop, _comment('Both angle values = %sº', roots[0].property.degree), roots=roots)
                        found = True
                    # TODO: report contradiction, if not angle values are not equal

                    if found:
                        continue

                    similar_triangles = [exp for exp in self.explained if isinstance(exp.property, SimilarTrianglesProperty)]
                    def match(angle, triangle):
                        both = set([angle, angle.reversed])
                        for i in range(0, 3):
                            if triangle[i].angle(triangle[(i + 1) % 3], triangle[(i + 2) % 3]) in both:
                                return i

                        return None

                    for st in similar_triangles:
                        ind = match(prop.angle0, st.property.ABC)
                        if ind is not None and ind == match(prop.angle1, st.property.DEF):
                            self.__reason(prop, 'Corr. angles in similar triangles', roots=[st])
                            found = True
                            break
                        ind = match(prop.angle1, st.property.ABC)
                        if ind is not None and ind == match(prop.angle0, st.property.DEF):
                            self.__reason(prop, 'Corr. angles in similar triangles', roots=[st])
                            found = True
                            break

                    if found:
                        continue

                    equal_angles = [exp for exp in self.explained if isinstance(exp.property, CongruentAnglesProperty)]
                    for index, ea0 in enumerate(equal_angles):
                        if prop.angle0 == ea0.property.angle0:
                            look_for = [prop.angle1, ea0.property.angle1]
                        elif prop.angle1 == ea0.property.angle0:
                            look_for = [prop.angle0, ea0.property.angle1]
                        elif prop.angle0 == ea0.property.angle1:
                            look_for = [prop.angle1, ea0.property.angle0]
                        elif prop.angle1 == ea0.property.angle1:
                            look_for = [prop.angle0, ea0.property.angle0]
                        else:
                            continue

                        for ea1 in equal_angles[index + 1:]:
                            if ea1.property.angle0 in look_for and ea1.property.angle1 in look_for:
                                self.__reason(prop, 'transitivity', roots=[ea0, ea1])
                                found = True
                                break

                        if found:
                            break

                elif isinstance(prop, SimilarTrianglesProperty):
                    equal_angles = [exp for exp in self.explained if isinstance(exp.property, CongruentAnglesProperty)]
                    def match(angle, triangle):
                        both = set([angle, angle.reversed])
                        for i in range(0, 3):
                            if triangle[i].angle(triangle[(i + 1) % 3], triangle[(i + 2) % 3]) in both:
                                return i

                        return None

                    roots = []
                    for ea in equal_angles:
                        ind = match(ea.property.angle0, prop.ABC)
                        if ind is not None and ind == match(ea.property.angle1, prop.DEF):
                            roots.append(ea)
                        ind = match(ea.property.angle1, prop.ABC)
                        if ind is not None and ind == match(ea.property.angle0, prop.DEF):
                            roots.append(ea)
                    if len(roots) == 3:
                        self.__reason(prop, 'three angles', roots=roots)
                    elif len(roots) == 2:
                        self.__reason(prop, 'two angles', roots=roots)
                elif isinstance(prop, CongruentTrianglesProperty):
                    similar_triangles = [exp for exp in self.explained if isinstance(exp.property, SimilarTrianglesProperty)]
                    equal_distances = [exp for exp in self.explained if isinstance(exp.property, CongruentSegmentProperty)]
                    for st in similar_triangles:
                        if (st.property.ABC == prop.ABC and st.property.DEF == prop.DEF) or \
                           (st.property.ABC == prop.DEF and st.property.DEF == prop.ABC):
                            break
                    else:
                        continue
                    for ed in equal_distances:
                        def index(two, three):
                            if set(two).issubset(set(three)):
                                for i in range(0, 3):
                                    if three[i] not in two:
                                        return i
                            return None

                        ind = index(ed.property.AB, prop.ABC)
                        if ind is not None and ind == index(ed.property.CD, prop.DEF):
                            self.__reason(prop, 'Similar triangles with equal side', roots=[st, ed])
                            break
                        ind = index(ed.property.AB, prop.DEF)
                        if ind is not None and ind == index(ed.property.CD, prop.ABC):
                            self.__reason(prop, 'Similar triangles with equal side', roots=[st, ed])

                elif isinstance(prop, CongruentSegmentProperty):
                    equal_triangles = [exp for exp in self.explained if isinstance(exp.property, CongruentTrianglesProperty)]
                    def index(two, three):
                        if set(two).issubset(set(three)):
                            for i in range(0, 3):
                                if three[i] not in two:
                                    return i
                        return None
                    for et in equal_triangles:
                        ind = index(prop.AB, et.property.ABC)
                        if ind is not None and ind == index(prop.CD, et.property.DEF):
                            self.__reason(prop, 'Corr. sides in equal triangles', roots=[et])
                            break
                        ind = index(prop.CD, et.property.ABC)
                        if ind is not None and ind == index(prop.AB, et.property.DEF):
                            self.__reason(prop, 'Corr. sides in equal triangles', roots=[et])

                elif isinstance(prop, IsoscelesTriangleProperty):
                    equal_distances = [exp for exp in self.explained if isinstance(exp.property, CongruentSegmentProperty)]
                    for ed in equal_distances:
                        pts = ed.property.AB + ed.property.CD
                        if pts.count(prop.A) == 2 and prop.BC[0] in pts and prop.BC[1] in pts:
                            self.__reason(prop, 'Two equal sides', roots=[ed])

                elif isinstance(prop, AngleValueProperty):
                    found = False
                    if prop.degree == 0:
                        same_direction = [exp for exp in self.explained if isinstance(exp.property, SameDirectionProperty)]
                        for sd in same_direction:
                            if prop.angle.vector0.start == sd.property.start and prop.angle.vector1.start == sd.property.start and set([prop.angle.vector0.end, prop.angle.vector1.end]) == set(sd.property.points):
                                self.__reason(prop, 'TBW', roots=[sd])
                                found = True
                                break

                    if found:
                        continue

                    equal_angles = [exp for exp in self.explained if isinstance(exp.property, CongruentAnglesProperty)]
                    angle_values = [exp for exp in self.explained if isinstance(exp.property, AngleValueProperty)]
                    for ea in equal_angles:
                        if ea.property.angle0 == prop.angle:
                            for av in angle_values:
                                if av.property.angle == ea.property.angle1:
                                    #TODO: report contradiction if degrees are different
                                    self.__reason(prop, _comment('%s = %s = %sº', prop.angle, av.property.angle, av.property.degree), roots=[ea, av])
                                    found = True
                                    break
                            if found:
                                break
                        elif ea.property.angle1 == prop.angle:
                            for av in angle_values:
                                if av.property.angle == ea.property.angle0:
                                    #TODO: report contradiction if degrees are different
                                    self.__reason(prop, _comment('%s = %s = %sº', prop.angle, av.property.angle, av.property.degree), roots=[ea, av])
                                    found = True
                                    break
                            if found:
                                break

                    if found:
                        continue

                    isosceles = [exp for exp in self.explained if isinstance(exp.property, IsoscelesTriangleProperty)]
                    values = [exp for exp in self.explained if isinstance(exp.property, AngleValueProperty)]
                    def is_angle(angle, vertex, points):
                        return angle.vector0.start == vertex and angle.vector1.start == vertex and set([angle.vector0.end, angle.vector1.end]) == set(points)
                    for iso in isosceles:
                        if is_angle(prop.angle, iso.property.BC[0], [iso.property.A, iso.property.BC[1]]):
                            break
                        if is_angle(prop.angle, iso.property.BC[1], [iso.property.A, iso.property.BC[0]]):
                            break
                    else:
                        continue
                    for val in values:
                        if is_angle(val.property.angle, iso.property.A, iso.property.BC):
                            self.__reason(prop, _comment('Base angle of isosceles △ %s %s %s with apex angle %s', iso.property.A, *iso.property.BC, val.property.degree), roots=[iso, val])
                        # TODO: check sum of angles; report contradiction if found


        base()
        while len(self.unexplained) > 0:
            explained_size = len(self.explained)
            iteration()
            if len(self.explained) == explained_size:
                break

    def dump(self):
        print('Explained:')
        for exp in self.explained:
            print('\t%2d: %s [%s]' % (exp.index, exp.property, exp))
        print('\nNot explained:')
        explained = [rsn.property for rsn in self.explained]
        for prop in self.properties:
            if not prop in explained:
                print('\t%s' % prop)
        print('\nTotal properties: %d, explained: %d, not explained: %d' % (len(self.properties), len(self.explained), len(self.unexplained)))

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
