from .core import Constraint, ParametrizedString
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
                    ', '.join(self.comments),
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
                                not_equal(pt, pt2, cnst.comments + [ParametrizedString('%s lies on the line %s %s', pt, pt0, pt1)])
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
                if isinstance(prop, RightAngleProperty):
                    for cnst in self.scene.constraints(Constraint.Kind.perpendicular):
                        line0 = cnst.params[0]
                        line1 = cnst.params[1]
                        def vector_on_line(vector, line):
                            return vector.start in line and vector.end in line

                        if vector_on_line(prop.angle.vector0, line0):
                            if vector_on_line(prop.angle.vector1, line1):
                                self.__reason(prop, [ParametrizedString('%s ⟂ %s', line0.label, line1.label)] + cnst.comments)
                        elif vector_on_line(prop.angle.vector0, line1):
                            if vector_on_line(prop.angle.vector1, line0):
                                self.__reason(prop, [ParametrizedString('%s ⟂ %s', line0.label, line1.label)] + cnst.comments)

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

            same_direction = [exp.property for exp in self.explained if isinstance(exp.property, SameDirectionProperty)]
            def same_dir(vector):
                for sd in same_direction:
                    if sd.start == vector.start:
                        if sd.points[0] == vector.end:
                            yield Vector(sd.start, sd.points[1], vector.placement)
                        elif sd.points[1] == vector.end:
                            yield Vector(sd.start, sd.points[0], vector.placement)
                    if sd.start == vector.end:
                        if sd.points[0] == vector.start:
                            yield Vector(sd.points[1], sd.start, vector.placement)
                        elif sd.points[1] == vector.start:
                            yield Vector(sd.points[0], sd.start, vector.placement)

            right_angles = [exp for exp in self.explained if isinstance(exp.property, RightAngleProperty)]
            for prop in list(self.unexplained):
                if isinstance(prop, EqualAnglesProperty):
                    found = False
                    for v0 in same_dir(prop.angle0.vector0):
                        #TODO: roots
                        if v0 == prop.angle1.vector0 and prop.angle1.vector1 in same_dir(prop.angle0.vector1):
                            self.__reason(prop, 'same angle')
                            found = True
                            break
                        elif v0 == prop.angle1.vector1 and prop.angle1.vector0 in same_dir(prop.angle0.vector1):
                            self.__reason(prop, 'same angle')
                            found = True
                            break
                        elif v0 == prop.angle1.vector0.reversed and prop.angle1.vector1.reversed in same_dir(prop.angle0.vector1):
                            self.__reason(prop, 'same angle')
                            found = True
                            break
                        elif v0 == prop.angle1.vector1.reversed and prop.angle1.vector0.reversed in same_dir(prop.angle0.vector1):
                            self.__reason(prop, 'same angle')
                            found = True
                            break

                    if found:
                        continue

                    roots = [exp for exp in right_angles if exp.property.angle in [prop.angle0, prop.angle1]]
                    if len(roots) == 2:
                        self.__reason(prop, 'both 90º', roots=roots)
                        found = True

                    if found:
                        continue

                    similar_triangles = [exp for exp in self.explained if isinstance(exp.property, SimilarTrianglesProperty)]
                    def match(angle, triangle):
                        pts = [angle.vector0.start, angle.vector1.start, angle.vector0.end, angle.vector1.end]
                        if set(pts) == set(triangle):
                            if angle.vector0.start == angle.vector1.start:
                                return triangle.index(angle.vector0.start)
                            elif angle.vector0.end == angle.vector1.end:
                                return triangle.index(angle.vector0.end)
                        return None

                    for st in similar_triangles:
                        ind = match(prop.angle0, st.property.ABC)
                        if ind is not None and ind == match(prop.angle1, st.property.DEF):
                            self.__reason(prop, 'corr. angles in similar triangles', roots=[st])
                            found = True
                            break
                        ind = match(prop.angle1, st.property.ABC)
                        if ind is not None and ind == match(prop.angle0, st.property.DEF):
                            self.__reason(prop, 'corr. angles in similar triangles', roots=[st])
                            found = True
                            break

                    if found:
                        continue

                    equal_angles = [exp for exp in self.explained if isinstance(exp.property, EqualAnglesProperty)]
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
                    equal_angles = [exp for exp in self.explained if isinstance(exp.property, EqualAnglesProperty)]
                    def match(angle, triangle):
                        pts = [angle.vector0.start, angle.vector1.start, angle.vector0.end, angle.vector1.end]
                        if set(pts) == set(triangle):
                            if angle.vector0.start == angle.vector1.start:
                                return triangle.index(angle.vector0.start)
                            elif angle.vector0.end == angle.vector1.end:
                                return triangle.index(angle.vector0.end)
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

        base()
        while len(self.unexplained) > 0:
            total = len(self.properties)
            explained_size = len(self.explained)
            iteration()
            if len(self.properties) == total and len(self.explained) == explained_size:
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
        print('\nTotal properties: %d, explained: %d' % (len(self.properties), len(self.explained)))

class NotEqualProperty(Property):
    def __init__(self, point0, point1):
        self.points = [point0, point1]

    def __str__(self):
        return '%s != %s' % tuple(p.label for p in self.points)

    def __eq__(self, other):
        return isinstance(other, NotEqualProperty) and set(self.points) == set(other.points)

class SameDirectionProperty(Property):
    def __init__(self, start, point0, point1):
        self.start = start
        self.points = [point0, point1]

    def __str__(self):
        return '%s, %s in the same direction from %s' % tuple(p.label for p in self.points + [self.start])

    def __eq__(self, other):
        if not isinstance(other, SameDirectionProperty):
            return False
        return self.start == other.start and set(self.points) == set(other.points)

class OppositeSideProperty(Property):
    def __init__(self, line, point0, point1):
        self.line = line
        self.points = [point0, point1]

    def __str__(self):
        return '%s, %s located on opposite sides of %s' % tuple(p.label for p in self.points + [self.line])

    def __eq__(self, other):
        if not isinstance(other, OppositeSideProperty):
            return False
        return self.line == other.line and set(self.points) == set(other.points)

class SameSideProperty(Property):
    def __init__(self, line, point0, point1):
        self.line = line
        self.points = [point0, point1]

    def __str__(self):
        return '%s, %s located on the same side of %s' % tuple(p.label for p in self.points + [self.line])

    def __eq__(self, other):
        if not isinstance(other, SameSideProperty):
            return False
        return self.line == other.line and set(self.points) == set(other.points)
