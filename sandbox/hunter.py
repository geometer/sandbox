import math

from sandbox import *

class Segment:
    def __init__(self, p0: Point, p1: Point, placement: Placement):
        self.p0 = p0
        self.p1 = p1
        self.__length = placement.distance(p0, p1)

    def length(self):
        return self.__length

    def __eq__(self, other) -> bool:
        return self.p0 == other.p0 and self.p1 == other.p1 or self.p0 == other.p0 and self.p1 == other.p1

    @property
    def name(self):
        return "%s %s" % (self.p0.id, self.p1.id)

def segments(placement: Placement):
    points = placement.scene.points
    for i0 in range(0, len(points)):
        for i1 in range(i0 + 1, len(points)):
            yield Segment(points[i0], points[i1], placement)

class LengthFamily:
    def __init__(self, segment: Segment):
        self.base = segment
        self.segments = []

    def __test(self, segment: Segment) -> str:
        ratio = segment.length() / self.base.length()
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

    def add(self, segment: Segment) -> bool:
        test = self.__test(segment)
        if test:
            segment.comment = test
            self.segments.append(segment)
            return True
        else:
            return False

def hunt(scene):
    placement = Placement(scene)

    all_segments = list(segments(placement))
    all_segments.sort(key=Segment.length)
    families = []
    for s in all_segments:
        added = False
        for f in families:
            if f.add(s):
                added = True
                break 
        if not added:
            families.append(LengthFamily(s))

    print("%d segments in %d families" % (len(all_segments), len([f for f in families if len(f.segments) > 0])))
    for f in families:
        if len(f.segments) > 0:
            print("%s: %d segments" % (f.base.name, 1 + len(f.segments)))
            for s in f.segments:
                print("\t%s (%s)" % (s.name, s.comment))

    for i0 in range(0, len(all_segments)):
        for i1 in range(i0 + 1, len(all_segments)):
            s0 = all_segments[i0]
            s1 = all_segments[i1]
            angle = placement.angle(s0.p0, s0.p1, s1.p0, s1.p1)
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
