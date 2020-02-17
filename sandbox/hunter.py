import math
from typing import List

from sandbox import Scene, Placement

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
        return math.fabs(self.__arc)

    def __str__(self):
        if self.vector0.start == self.vector1.start:
            return "∠ %s %s %s" % (self.vector0.end.label, self.vector0.start.label, self.vector1.end.label)
        return "∠(%s, %s)" % (self.vector0, self.vector1)

def __vectors(placement: Placement):
    points = placement.scene.points(skip_auxiliary=True)
    for index0 in range(0, len(points)):
        for index1 in range(index0 + 1, len(points)):
            vec = Vector(points[index0], points[index1], placement)
            if math.fabs(vec.length()) >= 5e-6:
                yield vec

def __angles(vectors: List[Vector]):
    for index0 in range(0, len(vectors)):
        for index1 in range(index0 + 1, len(vectors)):
            yield Angle(vectors[index0], vectors[index1])

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
        return math.fabs(self.side0 - self.side1) < 5e-6 and \
               math.fabs(self.side0 - self.side2) < 5e-6 and \
               math.fabs(self.side1 - self.side2) < 5e-6

    def isosceles(self):
        return math.fabs(self.side0 - self.side1) < 5e-6 or \
               math.fabs(self.side0 - self.side2) < 5e-6 or \
               math.fabs(self.side1 - self.side2) < 5e-6

    def similar(self, other) -> bool:
        ratio = self.side0 / other.side0
        if math.fabs(ratio / self.side1 * other.side1 - 1) >= 5e-6:
            return False
        return math.fabs(ratio / self.side2 * other.side2 - 1) < 5e-6

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
                if math.fabs(area) > 5e-6:
                    side0 = loc1.distanceTo(loc2)
                    side1 = loc2.distanceTo(loc0)
                    side2 = loc0.distanceTo(loc1)
                    yield Triangle(pt0, pt1, pt2, side0, side1, side2)

class LengthFamily:
    def __init__(self, vector: Vector):
        self.base = vector
        self.vectors = []

    def __test(self, vector: Vector) -> str:
        ratio = vector.length() / self.base.length()
        for i in range(1, 10):
            candidate = ratio * i
            if math.fabs(candidate - round(candidate)) < 5e-6:
                return "%d/%d" % (round(candidate), i) if i > 1 else "%d" % round(candidate)
        ratio = ratio * ratio
        for i in range(1, 100):
            candidate = ratio * i
            if math.fabs(candidate - round(candidate)) < 5e-6:
                if i > 1:
                    return "SQRT(%d/%d)" % (round(candidate), i)
                else:
                    return "SQRT(%d)" % round(candidate)
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
        for addition0 in (0, 2 * math.pi, -2 * math.pi):
            for addition1 in (0, 2 * math.pi, -2 * math.pi):
                ratio = (angle.arc() + addition0) / (self.base.arc() + addition1)
                for i in range(1, 10):
                    candidate = ratio * i
                    if math.fabs(candidate - round(candidate)) < 5e-6:
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
        added = False
        for fam in families:
            if fam.add(vec):
                added = True
                break
        if not added:
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
        if math.fabs(arc) < 5e-6:
            print("%s = 0" % ngl)
        else:
            ratio = arc / math.pi
            for i in range(1, 60):
                candidate = i * ratio
                if math.fabs(candidate - round(candidate)) < 5e-6:
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
        if ngl.abs_arc() < 5e-6:
            zero_count += 1
            continue
        added = False
        for fam in families:
            if fam.add(ngl):
                added = True
                break
        if not added:
            families.append(AngleFamily(ngl))

    print("%d non-zero angles in %d families" % (len(angles) - zero_count, len([f for f in families if len(f.angles) > 0])))
    for fam in families:
        if len(fam.angles) > 0:
            print("%s: %d angles" % (fam.base, 1 + len(fam.angles)))
            for pair in fam.angles:
                print("\t%s (%s)" % (pair['angle'], pair['comment']))

def hunt_similar_triangles(triangles):
    for trn in triangles:
        if trn.equilateral():
            print("%s equilateral" % trn)
        elif trn.isosceles():
            print("%s isosceles" % trn)
    for index0 in range(0, len(triangles)):
        trn0 = triangles[index0]
        for index1 in range(index0 + 1, len(triangles)):
            for variation in range(0, 6):
                trn1 = triangles[index1].variation(variation)
                if trn0.similar(trn1):
                    print('%s ∼ %s' % (trn0, trn1))
                    break

def hunt(scene, options = ['all']):
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
