import mpmath
from typing import List

from sandbox import Scene, Placement

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

    def arc(self):
        return self.__arc

    def abs_arc(self):
        return mpmath.fabs(self.__arc)

    def __str__(self):
        if self.vector0.start == self.vector1.start:
            return "∠ %s %s %s" % (self.vector0.end.label, self.vector0.start.label, self.vector1.end.label)
        return "∠(%s, %s)" % (self.vector0, self.vector1)

def __vectors(placement: Placement):
    points = placement.scene.points(skip_auxiliary=True)
    for index in range(0, len(points)):
        point0 = points[index]
        for point1 in points[index + 1:]:
            vec = Vector(point0, point1, placement)
            if mpmath.fabs(vec.length()) >= ERROR:
                yield vec

def __angles(vectors: List[Vector]):
    for index0 in range(0, len(vectors)):
        vec0 = vectors[index0]
        for vec1 in vectors[index0 + 1:]:
            yield Angle(vec0, vec1)

class Triangle:
    def __init__(self, pt0: Scene.Point, pt1: Scene.Point, pt2: Scene.Point, side0: float, side1: float, side2: float):
        self.pt0 = pt0
        self.pt1 = pt1
        self.pt2 = pt2
        self.side0 = side0
        self.side1 = side1
        self.side2 = side2

    def variation(self, index):
        if index == 1:
            return Triangle(self.pt0, self.pt2, self.pt1, self.side0, self.side2, self.side1)
        if index == 2:
            return Triangle(self.pt1, self.pt0, self.pt2, self.side1, self.side0, self.side2)
        if index == 3:
            return Triangle(self.pt1, self.pt2, self.pt0, self.side1, self.side2, self.side0)
        if index == 4:
            return Triangle(self.pt2, self.pt0, self.pt1, self.side2, self.side0, self.side1)
        if index == 5:
            return Triangle(self.pt2, self.pt1, self.pt0, self.side2, self.side1, self.side0)
        return self

    def __eq__(self, other) -> bool:
        return self.pt0 == other.pt0 and self.pt1 == other.pt1 and self.pt2 == other.pt2

    def __str__(self):
        return "△ %s %s %s" % (self.pt0.label, self.pt1.label, self.pt2.label)

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

def __triangles(placement: Placement):
    points = placement.scene.points(skip_auxiliary=True)
    for index0 in range(0, len(points)):
        pt0 = points[index0]
        loc0 = placement.location(pt0)
        for index1 in range(index0 + 1, len(points)):
            pt1 = points[index1]
            loc1 = placement.location(pt1)
            for index2 in range(index1 + 1, len(points)):
                pt2 = points[index2]
                loc2 = placement.location(pt2)
                area = loc0.x * (loc1.y - loc2.y) + loc1.x * (loc2.y - loc0.y) + loc2.x * (loc0.y - loc1.y)
                if mpmath.fabs(area) > ERROR:
                    side0 = loc1.distance_to(loc2)
                    side1 = loc2.distance_to(loc0)
                    side2 = loc0.distance_to(loc1)
                    yield Triangle(pt0, pt1, pt2, side0, side1, side2)

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

def hunt_similar_triangles(triangles):
    equilaterals = [trn for trn in triangles if trn.equilateral()]
    if equilaterals:
        print('Equilateral triangles: ' + ', '.join([str(trn) for trn in equilaterals]))

    triangles = [trn for trn in triangles if not trn.equilateral()]

    isosceles = list(filter(None, [trn.isosceles() for trn in triangles]))
    if isosceles:
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
        if len(fam) > 1:
            print(" ∼ ".join([str(trn) for trn in fam]))

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

def hunt_collinears(placement: Placement):
    used_pairs = set()
    points = placement.scene.points(skip_auxiliary=True)
    for index0 in range(0, len(points)):
        pt0 = points[index0]
        loc0 = placement.location(pt0)
        for index1 in range(index0 + 1, len(points)):
            pt1 = points[index1]
            if (pt0, pt1) in used_pairs:
                continue
            loc1 = placement.location(pt1)
            collinear = [pt0, pt1]
            for index2 in range(index1 + 1, len(points)):
                pt2 = points[index2]
                loc2 = placement.location(pt2)
                area = loc0.x * (loc1.y - loc2.y) + loc1.x * (loc2.y - loc0.y) + loc2.x * (loc0.y - loc1.y)
                if mpmath.fabs(area) < ERROR:
                    for pt in collinear:
                        used_pairs.add((pt, pt2))
                    collinear.append(pt2)
            if len(collinear) > 2:
                print('collinear: %s' % [pt.label for pt in collinear])

def hunt(scene, options=('all')):
    if isinstance(scene, Placement):
        placement = scene
    else:
        placement = Placement(scene)

    all_vectors = list(__vectors(placement))
    all_vectors.sort(key=Vector.length)

    if 'proportional_segments' in options or 'all' in options:
        hunt_proportional_segments(all_vectors)

    all_angles = list(__angles(all_vectors))
    all_angles.sort(key=Angle.abs_arc)

    if 'rational_angles' in options or 'all' in options:
        hunt_rational_angles(all_angles)

    if 'proportional_angles' in options or 'all' in options:
        hunt_proportional_angles(all_angles)

    if 'similar_triangles' in options or 'all' in options:
        hunt_similar_triangles(list(__triangles(placement)))

    if 'coincidences' in options or 'all' in options:
        hunt_coincidences(placement)

    if 'collinears' in options or 'all' in options:
        hunt_collinears(placement)
