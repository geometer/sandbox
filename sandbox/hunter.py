import math
from typing import List

from sandbox import Point, Placement

class Vector:
    def __init__(self, start: Point, end: Point, placement: Placement):
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
        return "%s %s" % (self.start.id, self.end.id)

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
            return "∠ %s %s %s" % (self.vector0.end.id, self.vector0.start.id, self.vector1.end.id)
        return "∠(%s, %s)" % (self.vector0, self.vector1)

def __vectors(placement: Placement):
    points = placement.scene.points
    for index0 in range(0, len(points)):
        for index1 in range(index0 + 1, len(points)):
            yield Vector(points[index0], points[index1], placement)

def __angles(vectors: List[Vector]):
    for index0 in range(0, len(vectors)):
        for index1 in range(index0 + 1, len(vectors)):
            yield Angle(vectors[index0], vectors[index1])

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

def hunt(scene):
    placement = Placement(scene)

    all_vectors = list(__vectors(placement))
    all_vectors.sort(key=Vector.length)
    families = []
    for vec in all_vectors:
        added = False
        for fam in families:
            if fam.add(vec):
                added = True
                break
        if not added:
            families.append(LengthFamily(vec))

    print("%d segments in %d families" % (len(all_vectors), len([f for f in families if len(f.vectors) > 0])))
    for fam in families:
        if len(fam.vectors) > 0:
            print("%s: %d segments" % (fam.base, 1 + len(fam.vectors)))
            for data in fam.vectors:
                print("\t%s (%s)" % (data['vector'], data['comment']))

    all_angles = list(__angles(all_vectors))
    all_angles.sort(key=Angle.abs_arc)
    for angle in all_angles:
        arc = angle.arc()
        if math.fabs(arc) < 5e-6:
            print("%s = 0" % angle)
        else:
            ratio = arc / math.pi
            for i in range(1, 60):
                candidate = i * ratio
                if math.fabs(candidate - round(candidate)) < 5e-6:
                    pi = "PI" if i == 1 else ("PI / %d" % i)
                    if round(candidate) == 1:
                        print("%s = %s" % (angle, pi))
                    elif round(candidate) == -1:
                        print("%s = -%s" % (angle, pi))
                    else:
                        print("%s = %d %s" % (angle, round(candidate), pi))
                    break

    families = []
    zero_count = 0
    for ang in all_angles:
        if ang.abs_arc() < 5e-6:
            zero_count += 1
            continue
        added = False
        for fam in families:
            if fam.add(ang):
                added = True
                break
        if not added:
            families.append(AngleFamily(ang))

    print("%d non-zero angles in %d families" % (len(all_angles) - zero_count, len([f for f in families if len(f.angles) > 0])))
    for fam in families:
        if len(fam.angles) > 0:
            print("%s: %d angles" % (fam.base, 1 + len(fam.angles)))
            for pair in fam.angles:
                print("\t%s (%s)" % (pair['angle'], pair['comment']))
