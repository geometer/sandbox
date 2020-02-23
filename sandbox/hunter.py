import mpmath
from typing import List

from . import Scene, Placement
from .property import *

ERROR = mpmath.mpf(5e-6)

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
        return "%s %s" % (self.start.label, self.end.label)

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
        return mpmath.fabs(self.__arc)

    def __str__(self):
        if self.vector0.start == self.vector1.start:
            return "∠ %s %s %s" % (self.vector0.end.label, self.vector0.start.label, self.vector1.end.label)
        return "∠(%s, %s)" % (self.vector0, self.vector1)

class Triangle:
    def __init__(self, pts, side0: float, side1: float, side2: float):
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
        return "△ %s %s %s" % (self.pts[0].label, self.pts[1].label, self.pts[2].label)

    def equilateral(self):
        return mpmath.fabs(self.side0 - self.side1) < ERROR and \
               mpmath.fabs(self.side0 - self.side2) < ERROR and \
               mpmath.fabs(self.side1 - self.side2) < ERROR

    def isosceles(self):
        if mpmath.fabs(self.side0 - self.side1) < ERROR:
            return self.variation(4)
        if mpmath.fabs(self.side0 - self.side2) < ERROR:
            return self.variation(2)
        if mpmath.fabs(self.side1 - self.side2) < ERROR:
            return self

    def similar(self, other) -> bool:
        ratio = self.side0 / other.side0
        if mpmath.fabs(ratio / self.side1 * other.side1 - 1) >= ERROR:
            return False
        return mpmath.fabs(ratio / self.side2 * other.side2 - 1) < ERROR

    def equal(self, other) -> bool:
        if mpmath.fabs(self.side0 - other.side0) >= ERROR:
            return False
        if mpmath.fabs(self.side1 - other.side1) >= ERROR:
            return False
        return mpmath.fabs(self.side2 - other.side2) < ERROR

class LengthFamily:
    def __init__(self, vector: Vector):
        self.base = vector
        self.vectors = []

    def __test(self, vector: Vector) -> str:
        ratio = vector.length() / self.base.length()
        for i in range(1, 10):
            candidate = ratio * i
            if mpmath.fabs(candidate - round(candidate)) < ERROR:
                return "%d/%d" % (round(candidate), i) if i > 1 else "%d" % round(candidate)
        ratio = ratio * ratio
        for i in range(1, 100):
            candidate = ratio * i
            if mpmath.fabs(candidate - round(candidate)) < ERROR:
                if i == 1:
                    return "SQRT(%d)" % round(candidate)
                return "SQRT(%d/%d)" % (round(candidate), i)
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
        for addition0 in (0, 2 * mpmath.pi, -2 * mpmath.pi):
            for addition1 in (0, 2 * mpmath.pi, -2 * mpmath.pi):
                ratio = (angle.arc() + addition0) / (self.base.arc() + addition1)
                for i in range(1, 10):
                    candidate = ratio * i
                    if mpmath.fabs(candidate - round(candidate)) < ERROR:
                        return "%d/%d" % (round(candidate), i) if i > 1 else "%d" % round(candidate)
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

    print("%d segments in %d families" % (len(vectors), len([f for f in families if len(f.vectors) > 0])))
    for fam in families:
        if len(fam.vectors) > 0:
            print("%s: %d segments" % (fam.base, 1 + len(fam.vectors)))
            for data in fam.vectors:
                print("\t%s (%s)" % (data['vector'], data['comment']))

def hunt_rational_angles(angles):
    for ngl in angles:
        arc = ngl.arc()
        if mpmath.fabs(arc) < ERROR:
            print("%s = 0" % ngl)
        else:
            ratio = arc / mpmath.pi
            for i in range(1, 60):
                candidate = i * ratio
                if mpmath.fabs(candidate - round(candidate)) < ERROR:
                    pi = "PI" if i == 1 else ("PI / %d" % i)
                    if round(candidate) == 1:
                        print("%s = %s" % (ngl, pi))
                    elif round(candidate) == -1:
                        print("%s = -%s" % (ngl, pi))
                    else:
                        print("%s = %d %s" % (ngl, round(candidate), pi))
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

    print("%d non-zero angles in %d families" % (len(angles) - zero_count, len([f for f in families if len(f.angles) > 0])))
    for fam in families:
        if len(fam.angles) > 0:
            print("%s: %d angles" % (fam.base, 1 + len(fam.angles)))
            for pair in fam.angles:
                print("\t%s (%s)" % (pair['angle'], pair['comment']))

def hunt_coincidences(placement: Placement):
    used_points = set()
    points = placement.scene.points(skip_auxiliary=True)
    for index0 in range(0, len(points)):
        pt0 = points[index0]
        if pt0 in used_points:
            continue
        loc0 = placement.location(pt0)
        same_points = [pt0]
        for index1 in range(index0 + 1, len(points)):
            pt1 = points[index1]
            loc1 = placement.location(pt1)
            if loc1.distance_to(loc0) < ERROR:
                same_points.append(pt1)
                used_points.add(pt1)
        if len(same_points) > 1:
            print('same point: %s' % [pt.label for pt in same_points])

class Hunter:
    def __init__(self, scene):
        if isinstance(scene, Placement):
            self.placement = scene
        else:
            self.placement = Placement(scene)
        self.properties = []

    @staticmethod
    def __iterate_pairs(lst):
        for index in range(0, len(lst)):
            elt0 = lst[index]
            for elt1 in lst[index + 1:]:
                yield (elt0, elt1)

    @staticmethod
    def __iterate_triples(lst):
        for index0 in range(0, len(lst)):
            elt0 = lst[index0]
            for index1 in range(index0 + 1, len(lst)):
                elt1 = lst[index1]
                for elt2 in lst[index1 + 1:]:
                    yield (elt0, elt1, elt2)

    def __vectors(self):
        points = self.placement.scene.points(skip_auxiliary=True)
        for index in range(0, len(points)):
            point0 = points[index]
            for point1 in points[index + 1:]:
                vec = Vector(point0, point1, self.placement)
                if mpmath.fabs(vec.length()) >= ERROR:
                    yield vec

    def __triangles(self):
        points = self.placement.scene.points(skip_auxiliary=True)
        for index0 in range(0, len(points)):
            pt0 = points[index0]
            loc0 = self.placement.location(pt0)
            for index1 in range(index0 + 1, len(points)):
                pt1 = points[index1]
                loc1 = self.placement.location(pt1)
                for index2 in range(index1 + 1, len(points)):
                    pt2 = points[index2]
                    loc2 = self.placement.location(pt2)
                    area = loc0.x * (loc1.y - loc2.y) + loc1.x * (loc2.y - loc0.y) + loc2.x * (loc0.y - loc1.y)
                    if mpmath.fabs(area) > ERROR:
                        side0 = loc1.distance_to(loc2)
                        side1 = loc2.distance_to(loc0)
                        side2 = loc0.distance_to(loc1)
                        yield Triangle((pt0, pt1, pt2), side0, side1, side2)

    def __lines(self):
        lines = []
        used_pairs = set()
        points = self.placement.scene.points(skip_auxiliary=True)
        for index0 in range(0, len(points)):
            pt0 = points[index0]
            loc0 = self.placement.location(pt0)
            for index1 in range(index0 + 1, len(points)):
                pt1 = points[index1]
                if (pt0, pt1) in used_pairs:
                    continue
                loc1 = self.placement.location(pt1)
                collinear = [pt0, pt1]
                for pt2 in points[index1 + 1:]:
                    loc2 = self.placement.location(pt2)
                    area = loc0.x * (loc1.y - loc2.y) + loc1.x * (loc2.y - loc0.y) + loc2.x * (loc0.y - loc1.y)
                    if mpmath.fabs(area) < ERROR:
                        for pt in collinear:
                            used_pairs.add((pt, pt2))
                        collinear.append(pt2)
                lines.append(collinear)

        return lines

    def __angles(self, lines):
        for index in range(0, len(lines)):
            line0 = lines[index]
            for line1 in lines[index + 1:]:
                common = None
                for pt in line0:
                    if pt in line1:
                        common = pt
                        break
                if common:
                    vec0 = Vector(common, line0[1] if line0[0] == common else line0[0], self.placement)
                    vec1 = Vector(common, line1[1] if line1[0] == common else line1[0], self.placement)
                else:
                    vec0 = Vector(line0[0], line0[1], self.placement)
                    vec1 = Vector(line1[0], line1[1], self.placement)
                yield Angle(vec0, vec1)

    def __hunt_collinears(self, lines, verbose):
        for line in lines:
            for triple in Hunter.__iterate_triples(line):
                self.properties.append(CollinearProperty(triple[0], triple[1], triple[2]))
            if len(line) > 2 and verbose:
                print('collinear: %s' % [pt.label for pt in line])

    def __hunt_equal_segments(self, verbose):
        vectors = self.__vectors()
        families = []
        for vec in vectors:
            for fam in families:
                if mpmath.fabs(vec.length() - fam[0].length()) < ERROR:
                    fam.append(vec)
                    break
            else:
                families.append([vec])

        for fam in families:
            for pair in Hunter.__iterate_pairs(fam):
                self.properties.append(EqualDistancesProperty((pair[0].start, pair[0].end), (pair[1].start, pair[1].end)))
            if len(fam) > 1 and verbose:
                print(' = '.join(['|' + str(vec) + '|' for vec in fam]))

    def __hunt_right_angles(self, angles, verbose):
        rights = []
        for ngl in angles:
            arc = ngl.arc()
            if mpmath.fabs(arc - mpmath.pi / 2) < ERROR:
                rights.append(ngl)
            elif mpmath.fabs(arc + mpmath.pi / 2) < ERROR:
                rights.append(ngl.reversed())
        for ngl in rights:
            self.properties.append(RightAngleProperty(
                (ngl.vector0.start, ngl.vector0.end),
                (ngl.vector1.start, ngl.vector1.end)
            ))
        if rights and verbose:
            print('90º: ' + ', '.join([str(ngl) for ngl in rights]))

    def __hunt_equal_angles(self, angles, verbose):
        families = []
        for ngl in angles:
            if ngl.abs_arc() < ERROR or mpmath.fabs(ngl.abs_arc() - mpmath.pi) < ERROR:
                continue
            for fam in families:
                if mpmath.fabs(ngl.arc() - fam[0].arc()) < ERROR:
                    fam.append(ngl)
                    break
                if mpmath.fabs(ngl.arc() + fam[0].arc()) < ERROR:
                    fam.append(ngl.reversed())
                    break
            else:
                families.append([ngl if ngl.arc() > 0 else ngl.reversed()])

        for fam in families:
            for pair in Hunter.__iterate_pairs(fam):
                self.properties.append(EqualAnglesProperty(
                    (pair[0].vector0.start, pair[0].vector0.end,
                     pair[0].vector1.start, pair[0].vector1.end),
                    (pair[1].vector0.start, pair[1].vector0.end,
                     pair[1].vector1.start, pair[1].vector1.end)
                ))
            if len(fam) > 1 and verbose:
                print(' = '.join([str(ngl) for ngl in fam]))

    def __hunt_equal_triangles(self, verbose):
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
            for pair in Hunter.__iterate_pairs(fam):
                self.properties.append(EqualTrianglesProperty(pair[0].pts, pair[1].pts))
            if len(fam) > 1 and verbose:
                print(" = ".join([str(trn) for trn in fam]))

    def __hunt_similar_triangles(self, verbose):
        triangles = list(self.__triangles())

        equilaterals = [trn for trn in triangles if trn.equilateral()]
        for trn in equilaterals:
            self.properties.append(EquilateralTriangleProperty(trn.pts))
        if equilaterals and verbose:
            print('Equilateral triangles: ' + ', '.join([str(trn) for trn in equilaterals]))

        triangles = [trn for trn in triangles if not trn.equilateral()]

        isosceles = list(filter(None, [trn.isosceles() for trn in triangles]))
        for trn in isosceles:
            self.properties.append(IsoscelesTriangleProperty(trn.pts[0], trn.pts[1:]))
        if isosceles and verbose:
            print('Isosceles triangles: ' + ', '.join([str(trn) for trn in isosceles]))

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
            for pair in Hunter.__iterate_pairs(fam):
                self.properties.append(SimilarTrianglesProperty(pair[0].pts, pair[1].pts))
            if len(fam) > 1 and verbose:
                print(" ~ ".join([str(trn) for trn in fam]))

    def hunt(self, options=('all')):
        all_vectors = list(self.__vectors())
        all_vectors.sort(key=Vector.length)

        all_lines = list(self.__lines())

        all_angles = list(self.__angles(all_lines))
        all_angles.sort(key=Angle.abs_arc)

        if 'collinears' in options or 'all' in options:
            self.__hunt_collinears(all_lines, 'verbose' in options)

        if 'equal_segments' in options or 'all' in options:
            self.__hunt_equal_segments('verbose' in options)

        if 'proportional_segments' in options or 'all' in options:
            hunt_proportional_segments(all_vectors)

        if 'rational_angles' in options or 'all' in options:
            hunt_rational_angles(all_angles)

        if 'equal_angles' in options or 'all' in options:
            self.__hunt_equal_angles(all_angles, 'verbose' in options)

        if 'right_angles' in options or 'all' in options:
            self.__hunt_right_angles(all_angles, 'verbose' in options)

        if 'proportional_angles' in options or 'all' in options:
            hunt_proportional_angles(all_angles)

        if 'equal_triangles' in options or 'all' in options:
            self.__hunt_equal_triangles('verbose' in options)

        if 'similar_triangles' in options or 'all' in options:
            self.__hunt_similar_triangles('verbose' in options)

        if 'coincidences' in options or 'all' in options:
            hunt_coincidences(self.placement)

    def dump(self):
        print('Properties:\n')
        for prop in self.properties:
            print('\t%s' % prop)
        print('\nTotal properties: %d' % len(self.properties))
