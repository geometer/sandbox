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
                                self.__reason(prop, ['%s ⟂ %s' % (line0.label, line1.label)] + cnst.comments)
                        elif vector_on_line(prop.angle.vector0, line1):
                            if vector_on_line(prop.angle.vector1, line0):
                                self.__reason(prop, ['%s ⟂ %s' % (line0.label, line1.label)] + cnst.comments)

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

            for index in range(0, len(same_side_reasons)):
                rsn0 = same_side_reasons[index]
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

            right_angles = [exp for exp in self.explained if isinstance(exp.property, RightAngleProperty)]
            for prop in list(self.unexplained):
                if isinstance(prop, EqualAnglesProperty):
                    roots = [exp for exp in right_angles if exp.property.angle in [prop.angle0, prop.angle1]]
                    if len(roots) == 2:
                        self.__reason(prop, 'both 90º', roots=roots)

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
