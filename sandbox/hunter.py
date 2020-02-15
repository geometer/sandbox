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

    def __eq__(self, other) -> bool:
        return self.start == other.start and self.end == other.end

    @property
    def name(self):
        return "%s %s" % (self.start.id, self.end.id)

class Angle:
    def __init__(self, vector0: Vector, vector1: Vector):
        self.vector0 = vector0
        self.vector1 = vector1
        self.__arc = vector0.angle(vector1)

    def arc(self):
        return self.__arc

    @property
    def name(self):
        return "∠(%s, %s)" % (self.vector0.name, self.vector1.name)

def vectors(placement: Placement):
    points = placement.scene.points
    for index0 in range(0, len(points)):
        for index1 in range(index0 + 1, len(points)):
            yield Vector(points[index0], points[index1], placement)

def angles(vectors: List[Vector]):
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
        if test:
            vector.comment = test
            self.vectors.append(vector)
            return True
        else:
            return False

def hunt(scene):
    placement = Placement(scene)

    all_vectors = list(vectors(placement))
    all_vectors.sort(key=Vector.length)
    families = []
    for s in all_vectors:
        added = False
        for f in families:
            if f.add(s):
                added = True
                break
        if not added:
            families.append(LengthFamily(s))

    print("%d segments in %d families" % (len(all_vectors), len([f for f in families if len(f.vectors) > 0])))
    for fam in families:
        if len(fam.vectors) > 0:
            print("%s: %d segments" % (fam.base.name, 1 + len(fam.vectors)))
            for vec in fam.vectors:
                print("\t%s (%s)" % (vec.name, vec.comment))

    all_angles = list(angles(all_vectors))
    for angle in all_angles:
        arc = angle.arc()
        if math.fabs(arc) < 5e-6:
            print("%s = 0" % angle.name)
        else:
            ratio = arc / math.pi
            for i in range(1, 60):
                candidate = i * ratio
                if math.fabs(candidate - round(candidate)) < 5e-6:
                    if round(candidate) == 1:
                        print("%s = PI / %d" % (angle.name, i))
                    elif round(candidate) == -1:
                        print("%s = -PI / %d" % (angle.name, i))
                    else:
                        print("%s = %d PI / %d" % (angle.name, round(candidate), i))
                    break
