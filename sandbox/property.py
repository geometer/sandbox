from .core import _comment

def keys_for_vector(vector):
    return [frozenset([vector.start, vector.end])]

def keys_for_angle(angle):
    return [frozenset([angle.vector0.start, angle.vector0.end, angle.vector1.start, angle.vector1.end])]

def keys_for_triangle(triangle):
    return [frozenset(triangle), frozenset(triangle[1:]), frozenset(triangle[:-1]), frozenset([triangle[0], triangle[2]])]

class Property:
    def __str__(self):
        return str(self.description)

    @property
    def keys(self):
        return []

class EquilateralTriangleProperty(Property):
    def __init__(self, ABC):
        self.ABC = list(ABC)

    @property
    def keys(self):
        return keys_for_triangle(self.ABC)

    @property
    def description(self):
        return _comment('equilateral △ %s %s %s', *self.ABC)

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

    @property
    def keys(self):
        return keys_for_angle(self.angle)

    @property
    def description(self):
        return _comment('%s = %dº', self.angle, self.degree)

    def __eq__(self, other):
        return isinstance(other, AngleValueProperty) and self.angle == other.angle and self.degree == other.degree

class CongruentAnglesProperty(Property):
    def __init__(self, angle0, angle1):
        self.angle0 = angle0
        self.angle1 = angle1

    @property
    def keys(self):
        return keys_for_angle(self.angle0) + keys_for_angle(self.angle1)

    @property
    def description(self):
        return _comment('%s = %s', self.angle0, self.angle1)

    def __eq__(self, other):
        if not isinstance(other, CongruentAnglesProperty):
            return False
        return (self.angle0 == other.angle0 and self.angle1 == other.angle1) or \
               (self.angle0 == other.angle1 and self.angle1 == other.angle0)

class CongruentSegmentProperty(Property):
    def __init__(self, vector0, vector1):
        self.vector0 = vector0
        self.vector1 = vector1

    @property
    def keys(self):
        return keys_for_vector(self.vector0) + keys_for_vector(self.vector1)

    @property
    def description(self):
        return _comment('|%s| = |%s|', self.vector0, self.vector1)

class SimilarTrianglesProperty(Property):
    def __init__(self, ABC, DEF):
        self.ABC = list(ABC)
        self.DEF = list(DEF)

    @property
    def keys(self):
        return keys_for_triangle(self.ABC) + keys_for_triangle(self.DEF)

    @property
    def description(self):
        return _comment('△ %s %s %s ~ △ %s %s %s', *self.ABC, *self.DEF)

class CongruentTrianglesProperty(Property):
    def __init__(self, ABC, DEF):
        self.ABC = list(ABC)
        self.DEF = list(DEF)

    @property
    def keys(self):
        return keys_for_triangle(self.ABC) + keys_for_triangle(self.DEF)

    @property
    def description(self):
        return _comment('△ %s %s %s = △ %s %s %s', *self.ABC, *self.DEF)

class IsoscelesTriangleProperty(Property):
    def __init__(self, A, BC):
        self.A = A
        self.BC = list(BC)

    @property
    def keys(self):
        return keys_for_triangle([self.A] + self.BC)

    @property
    def description(self):
        return _comment('isosceles △ %s %s %s', self.A, *self.BC)
