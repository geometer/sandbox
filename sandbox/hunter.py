import math

from sandbox import *

class Vector:
    def __init__(self, start: Point, end: Point, placement: Placement):
        self.start = start
        self.end = end
        self.__length = placement.distance(start, end)

    def length(self):
        return self.__length

    def __eq__(self, other) -> bool:
        return self.start == other.start and self.end == other.end or self.start == other.start and self.end == other.end

    @property
    def name(self):
        return "%s %s" % (self.start.id, self.end.id)

def vectors(placement: Placement):
    points = placement.scene.points
    for i0 in range(0, len(points)):
        for i1 in range(i0 + 1, len(points)):
            yield Vector(points[i0], points[i1], placement)

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
                return "SQRT(%d/%d)" % (round(candidate), i) if i > 1 else "SQRT(%d)" % round(candidate)
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
    for f in families:
        if len(f.vectors) > 0:
            print("%s: %d segments" % (f.base.name, 1 + len(f.vectors)))
            for s in f.vectors:
                print("\t%s (%s)" % (s.name, s.comment))

    for i0 in range(0, len(all_vectors)):
        for i1 in range(i0 + 1, len(all_vectors)):
            s0 = all_vectors[i0]
            s1 = all_vectors[i1]
            angle = placement.angle(s0.start, s0.end, s1.start, s1.end)
            if math.fabs(angle) < 5e-6:
                print("%s parallel to %s" % (s0.name, s1.name))
            else:
                ratio = angle / math.pi
                for i in range(1, 60):
                    candidate = i * ratio
                    if math.fabs(candidate - round(candidate)) < 5e-6:
                        if round(candidate) == 1:
                            print("angle between %s and %s = PI / %d" % (s0.name, s1.name, i))
                        elif round(candidate) == -1:
                            print("angle between %s and %s = -PI / %d" % (s0.name, s1.name, i))
                        else:
                            print("angle between %s and %s = %d * PI / %d" % (s0.name, s1.name, round(candidate), i))
                        break
