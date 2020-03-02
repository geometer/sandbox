import numpy as np

from . import Scene, iterative_placement
from .placement import Placement
from .property import *
from .core import _comment

ERROR = np.float128(5e-6)

class Vector:
    def __init__(self, start: Scene.Point, end: Scene.Point, placement: Placement):
        self.start = start
        self.end = end
        self.placement = placement
        self.__length = placement.distance(start, end)

    def length(self):
        return self.__length

    def angle(self, other):
        return self.placement.angle(self.start, self.end, other.start, other.end)

    @property
    def reversed(self):
        return Vector(self.end, self.start, self.placement)

    def __eq__(self, other) -> bool:
        return self.start == other.start and self.end == other.end

    def __str__(self):
        return str(_comment('%s %s', self.start, self.end))

class Angle:
    def __init__(self, vector0: Vector, vector1: Vector):
        if vector0.end == vector1.end:
            self.vector0 = vector0.reversed
            self.vector1 = vector1.reversed
        elif vector0.start == vector1.end:
            self.vector0 = vector0
            self.vector1 = vector1.reversed
        elif vector0.end == vector1.start:
            self.vector0 = vector0.reversed
            self.vector1 = vector1
        else:
            self.vector0 = vector0
            self.vector1 = vector1
        self.__arc = self.vector0.angle(self.vector1)

    def reversed(self):
        return Angle(self.vector1, self.vector0)

    def arc(self):
        return self.__arc

    def abs_arc(self):
        return np.fabs(self.__arc)

    def __str__(self):
        if self.vector0.start == self.vector1.start:
            return '∠ %s %s %s' % (self.vector0.end.label, self.vector0.start.label, self.vector1.end.label)
        return '∠(%s, %s)' % (self.vector0, self.vector1)

    def __eq__(self, other):
        return self.vector0 == other.vector0 and self.vector1 == other.vector1

class Triangle:
    def __init__(self, pts, side0, side1, side2):
        self.pts = list(pts)
        self.side0 = side0
        self.side1 = side1
        self.side2 = side2

    def variation(self, index):
        if index == 1:
            return Triangle((self.pts[0], self.pts[2], self.pts[1]), self.side0, self.side2, self.side1)
        if index == 2:
            return Triangle((self.pts[1], self.pts[0], self.pts[2]), self.side1, self.side0, self.side2)
        if index == 3:
            return Triangle((self.pts[1], self.pts[2], self.pts[0]), self.side1, self.side2, self.side0)
        if index == 4:
            return Triangle((self.pts[2], self.pts[0], self.pts[1]), self.side2, self.side0, self.side1)
        if index == 5:
            return Triangle((self.pts[2], self.pts[1], self.pts[0]), self.side2, self.side1, self.side0)
        return self

    def __eq__(self, other) -> bool:
        return self.pts[0] == other.pts[0] and self.pts[1] == other.pts[1] and self.pts[2] == other.pts[2]

    def __str__(self):
        return str(_comment('△ %s %s %s', *self.pts))

    def equilateral(self):
        return np.fabs(self.side0 - self.side1) < ERROR and \
               np.fabs(self.side0 - self.side2) < ERROR and \
               np.fabs(self.side1 - self.side2) < ERROR

    def isosceles(self):
        if np.fabs(self.side0 - self.side1) < ERROR:
            return self.variation(4)
        if np.fabs(self.side0 - self.side2) < ERROR:
            return self.variation(2)
        if np.fabs(self.side1 - self.side2) < ERROR:
            return self

    def similar(self, other) -> bool:
        ratio = self.side0 / other.side0
        if np.fabs(ratio / self.side1 * other.side1 - 1) >= ERROR:
            return False
        return np.fabs(ratio / self.side2 * other.side2 - 1) < ERROR

    def equal(self, other) -> bool:
        if np.fabs(self.side0 - other.side0) >= ERROR:
            return False
        if np.fabs(self.side1 - other.side1) >= ERROR:
            return False
        return np.fabs(self.side2 - other.side2) < ERROR

class LengthFamily:
    def __init__(self, vector: Vector):
        self.base = vector
        self.vectors = []

    def __test(self, vector: Vector) -> str:
        ratio = vector.length() / self.base.length()
        for i in range(1, 10):
            candidate = ratio * i
            if np.fabs(candidate - round(candidate)) < ERROR:
                return '%d/%d' % (round(candidate), i) if i > 1 else '%d' % round(candidate)
        ratio = ratio * ratio
        for i in range(1, 100):
            candidate = ratio * i
            if np.fabs(candidate - round(candidate)) < ERROR:
                if i == 1:
                    return 'SQRT(%d)' % round(candidate)
                return 'SQRT(%d/%d)' % (round(candidate), i)
        return None

    def add(self, vector: Vector) -> bool:
        test = self.__test(vector)
        if test is None:
            return False
        self.vectors.append({'vector': vector, 'comment': test})
        return True

class AngleFamily:
    def __init__(self, angle: Angle):
        self.base = angle
        self.angles = []

    def __test(self, angle: Angle) -> str:
        for addition0 in (0, 2 * np.pi, -2 * np.pi):
            for addition1 in (0, 2 * np.pi, -2 * np.pi):
                ratio = (angle.arc() + addition0) / (self.base.arc() + addition1)
                for i in range(1, 10):
                    candidate = ratio * i
                    if np.fabs(candidate - round(candidate)) < ERROR:
                        return '%d/%d' % (round(candidate), i) if i > 1 else '%d' % round(candidate)
        return None

    def add(self, angle: Angle) -> bool:
        test = self.__test(angle)
        if test is None:
            return False
        self.angles.append({'angle': angle, 'comment': test})
        return True

def hunt_proportional_segments(vectors):
    families = []
    for vec in vectors:
        for fam in families:
            if fam.add(vec):
                break
        else:
            families.append(LengthFamily(vec))

    print('%d segments in %d families' % (len(vectors), len([f for f in families if len(f.vectors) > 0])))
    for fam in families:
        if len(fam.vectors) > 0:
            print('%s: %d segments' % (fam.base, 1 + len(fam.vectors)))
            for data in fam.vectors:
                print('\t%s (%s)' % (data['vector'], data['comment']))

def hunt_rational_angles(angles):
    for ngl in angles:
        arc = ngl.arc()
        if np.fabs(arc) < ERROR:
            print('%s = 0' % ngl)
        else:
            ratio = arc / np.pi
            for i in range(1, 60):
                candidate = i * ratio
                if np.fabs(candidate - round(candidate)) < ERROR:
                    pi = 'PI' if i == 1 else ('PI / %d' % i)
                    if round(candidate) == 1:
                        print('%s = %s' % (ngl, pi))
                    elif round(candidate) == -1:
                        print('%s = -%s' % (ngl, pi))
                    else:
                        print('%s = %d %s' % (ngl, round(candidate), pi))
                    break

def hunt_proportional_angles(angles):
    families = []
    zero_count = 0
    for ngl in angles:
        if ngl.abs_arc() < ERROR:
            zero_count += 1
            continue
        for fam in families:
            if fam.add(ngl):
                break
        else:
            families.append(AngleFamily(ngl))

    print('%d non-zero angles in %d families' % (len(angles) - zero_count, len([f for f in families if len(f.angles) > 0])))
    for fam in families:
        if len(fam.angles) > 0:
            print('%s: %d angles' % (fam.base, 1 + len(fam.angles)))
            for pair in fam.angles:
                print('\t%s (%s)' % (pair['angle'], pair['comment']))

def hunt_coincidences(placement: Placement):
    used_points = set()
    points = placement.scene.points(skip_auxiliary=True)
    for index0, pt0 in enumerate(points):
        if pt0 in used_points:
            continue
        loc0 = placement.location(pt0)
        same_points = [pt0]
        for pt1 in points[index0 + 1:]:
            loc1 = placement.location(pt1)
            if loc1.distance_to(loc0) < ERROR:
                same_points.append(pt1)
                used_points.add(pt1)
        if len(same_points) > 1:
            print('same point: %s' % [pt.label for pt in same_points])

def iterate_pairs(lst):
    for index, elt0 in enumerate(lst):
        for elt1 in lst[index + 1:]:
            yield (elt0, elt1)

class Hunter:
    def __init__(self, scene):
        if isinstance(scene, Placement):
            self.placement = scene
        else:
            self.placement = iterative_placement(scene)
        self.properties = []

    @staticmethod
    def __iterate_triples(lst):
        for index0, elt0 in enumerate(lst):
            for index1, elt1 in enumerate(lst[index0 + 1:], start=index0 + 1):
                for elt2 in lst[index1 + 1:]:
                    yield (elt0, elt1, elt2)

    def __vectors(self):
        points = self.placement.scene.points(skip_auxiliary=True)
        for index, point0 in enumerate(points):
            for point1 in points[index + 1:]:
                vec = Vector(point0, point1, self.placement)
                if np.fabs(vec.length()) >= ERROR:
                    yield vec

    def __triangles(self):
        points = self.placement.scene.points(skip_auxiliary=True)
        for index0, pt0 in enumerate(points):
            loc0 = self.placement.location(pt0)
            for index1, pt1 in enumerate(points[index0 + 1:], start=index0 + 1):
                loc1 = self.placement.location(pt1)
                for pt2 in points[index1 + 1:]:
                    loc2 = self.placement.location(pt2)
                    area = loc0.x * (loc1.y - loc2.y) + loc1.x * (loc2.y - loc0.y) + loc2.x * (loc0.y - loc1.y)
                    if np.fabs(area) > ERROR:
                        side0 = loc1.distance_to(loc2)
                        side1 = loc2.distance_to(loc0)
                        side2 = loc0.distance_to(loc1)
                        yield Triangle((pt0, pt1, pt2), side0, side1, side2)

    def __lines(self):
        lines = []
        used_pairs = set()
        points = self.placement.scene.points(skip_auxiliary=True)
        for index0, pt0 in enumerate(points):
            loc0 = self.placement.location(pt0)
            for index1, pt1 in enumerate(points[index0 + 1:], start=index0 + 1):
                if (pt0, pt1) in used_pairs:
                    continue
                loc1 = self.placement.location(pt1)
                collinear = [pt0, pt1]
                for pt2 in points[index1 + 1:]:
                    loc2 = self.placement.location(pt2)
                    area = loc0.x * (loc1.y - loc2.y) + loc1.x * (loc2.y - loc0.y) + loc2.x * (loc0.y - loc1.y)
                    if np.fabs(area) < ERROR:
                        for pt in collinear:
                            used_pairs.add((pt, pt2))
                        collinear.append(pt2)
                lines.append(collinear)

        return lines

    def __angles(self, vectors):
        for pair in iterate_pairs(vectors):
            yield Angle(pair[0], pair[1])

    def __add(self, prop):
        if prop not in self.properties:
            self.properties.append(prop)

    def __hunt_collinears(self):
        for line in self.__lines():
            for triple in Hunter.__iterate_triples(line):
                self.__add(CollinearProperty(triple[0], triple[1], triple[2]))

    def __hunt_equal_segments(self):
        vectors = self.__vectors()
        families = []
        for vec in vectors:
            for fam in families:
                if np.fabs(vec.length() - fam[0].length()) < ERROR:
                    fam.append(vec)
                    break
            else:
                families.append([vec])

        for fam in families:
            for pair in iterate_pairs(fam):
                self.__add(EqualDistancesProperty((pair[0].start, pair[0].end), (pair[1].start, pair[1].end)))

    def __hunt_angle_values(self, angles):
        for ngl in angles:
            arc = ngl.arc()
            frac = arc / np.pi * 12
            frac_int = int(np.round(frac))
            if np.fabs(frac - frac_int) < ERROR:
                if frac >= 0:
                    self.__add(AngleValueProperty(ngl, 15 * frac_int))
                else:
                    self.__add(AngleValueProperty(ngl.reversed(), -15 * frac_int))

    def __hunt_equal_angles(self, angles):
        families = []

        for ngl in angles:
            if ngl.abs_arc() < ERROR or np.fabs(ngl.abs_arc() - np.pi) < ERROR:
                continue
            for fam in families:
                if np.fabs(ngl.arc() - fam[0].arc()) < ERROR:
                    fam.append(ngl)
                    break
                if np.fabs(ngl.arc() + fam[0].arc()) < ERROR:
                    fam.append(ngl.reversed())
                    break
            else:
                families.append([ngl if ngl.arc() > 0 else ngl.reversed()])

        for fam in families:
            for pair in iterate_pairs(fam):
                self.__add(EqualAnglesProperty(pair[0], pair[1]))

    def __hunt_equal_triangles(self):
        triangles = list(self.__triangles())
        families = []
        for trn in triangles:
            for fam in families:
                for variation in range(0, 6):
                    var = trn.variation(variation)
                    if fam[0].equal(var):
                        fam.append(var)
                        break
                else:
                    continue
                break
            else:
                families.append([trn])

        for fam in families:
            for pair in iterate_pairs(fam):
                self.__add(EqualTrianglesProperty(pair[0].pts, pair[1].pts))

    def __hunt_similar_triangles(self):
        triangles = list(self.__triangles())

        equilaterals = [trn for trn in triangles if trn.equilateral()]
        for trn in equilaterals:
            self.__add(EquilateralTriangleProperty(trn.pts))

        triangles = [trn for trn in triangles if not trn.equilateral()]

        isosceles = list(filter(None, [trn.isosceles() for trn in triangles]))
        for trn in isosceles:
            self.__add(IsoscelesTriangleProperty(trn.pts[0], trn.pts[1:]))

        families = []
        for trn in triangles:
            for fam in families:
                for variation in range(0, 6):
                    var = trn.variation(variation)
                    if fam[0].similar(var):
                        fam.append(var)
                        break
                else:
                    continue
                break
            else:
                families.append([trn])

        for fam in families:
            for pair in iterate_pairs(fam):
                self.__add(SimilarTrianglesProperty(pair[0].pts, pair[1].pts))

    def hunt(self, options=('default')):
        all_vectors = list(self.__vectors())
        all_vectors.sort(key=Vector.length)

        all_lines = list(self.__lines())

        all_angles = list(self.__angles(all_vectors))
        all_angles.sort(key=Angle.abs_arc)

        if 'collinears' in options or 'default' in options:
            self.__hunt_collinears()

        if 'equal_segments' in options or 'default' in options:
            self.__hunt_equal_segments()

        if 'equal_angles' in options or 'default' in options:
            self.__hunt_equal_angles(all_angles)

        if 'angle_values' in options or 'default' in options:
            self.__hunt_angle_values(all_angles)

        if 'equal_triangles' in options or 'default' in options:
            self.__hunt_equal_triangles()

        if 'similar_triangles' in options or 'default' in options:
            self.__hunt_similar_triangles()

        if 'proportional_segments' in options or 'all' in options:
            hunt_proportional_segments(all_vectors)

        if 'rational_angles' in options or 'all' in options:
            hunt_rational_angles(all_angles)

        if 'proportional_angles' in options or 'all' in options:
            hunt_proportional_angles(all_angles)

        if 'coincidences' in options or 'all' in options:
            hunt_coincidences(self.placement)

    def dump(self):
        print('Properties:\n')
        for prop in self.properties:
            print('\t%s' % prop)
        print('\nTotal properties: %d' % len(self.properties))

class CollinearProperty(Property):
    def __init__(self, A, B, C):
        self.points = (A, B, C)

    @property
    def description(self):
        return _comment('collinear %s, %s, %s', *self.points)

class AngleValueProperty(Property):
    def __init__(self, angle, degree):
        self.angle = angle
        self.degree = degree

    def __str__(self):
        return '%s = %dº' % (self.angle, self.degree)

    def __eq__(self, other):
        return isinstance(other, AngleValueProperty) and self.angle == other.angle and self.degree == other.degree

class EqualAnglesProperty(Property):
    def __init__(self, angle0, angle1):
        self.angle0 = angle0
        self.angle1 = angle1

    def __str__(self):
        return '%s = %s' % (self.angle0, self.angle1)

    def __eq__(self, other):
        if not isinstance(other, EqualAnglesProperty):
            return False
        return (self.angle0 == other.angle0 and self.angle1 == other.angle1) or \
               (self.angle0 == other.angle1 and self.angle1 == other.angle0)

class EqualDistancesProperty(Property):
    def __init__(self, AB, CD):
        self.AB = list(AB)
        self.CD = list(CD)

    @property
    def description(self):
        return _comment('|%s %s| = |%s %s|', *self.AB, *self.CD)

class SimilarTrianglesProperty(Property):
    def __init__(self, ABC, DEF):
        self.ABC = list(ABC)
        self.DEF = list(DEF)

    @property
    def description(self):
        return _comment('△ %s %s %s ~ △ %s %s %s', *self.ABC, *self.DEF)

class EqualTrianglesProperty(Property):
    def __init__(self, ABC, DEF):
        self.ABC = list(ABC)
        self.DEF = list(DEF)

    @property
    def description(self):
        return _comment('△ %s %s %s = △ %s %s %s', *self.ABC, *self.DEF)

class IsoscelesTriangleProperty(Property):
    def __init__(self, A, BC):
        self.A = A
        self.BC = list(BC)

    @property
    def description(self):
        return _comment('isosceles △ %s %s %s', self.A, *self.BC)
