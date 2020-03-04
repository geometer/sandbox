from .core import _comment

class Property:
    def __str__(self):
        return str(self.description)

class EquilateralTriangleProperty(Property):
    def __init__(self, ABC):
        self.ABC = list(ABC)

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

    def __str__(self):
        return '%s = %dº' % (self.angle, self.degree)

    def __eq__(self, other):
        return isinstance(other, AngleValueProperty) and self.angle == other.angle and self.degree == other.degree

class CongruentAnglesProperty(Property):
    def __init__(self, angle0, angle1):
        self.angle0 = angle0
        self.angle1 = angle1

    def __str__(self):
        return '%s = %s' % (self.angle0, self.angle1)

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
    def description(self):
        return _comment('|%s| = |%s|', self.vector0, self.vector1)

class SimilarTrianglesProperty(Property):
    def __init__(self, ABC, DEF):
        self.ABC = list(ABC)
        self.DEF = list(DEF)

    @property
    def description(self):
        return _comment('△ %s %s %s ~ △ %s %s %s', *self.ABC, *self.DEF)

class CongruentTrianglesProperty(Property):
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
