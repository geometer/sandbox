from .core import _comment

def keys_for_vector(vector):
    return [frozenset(vector.points)]

def keys_for_angle(angle):
    return [frozenset([*angle.vector0.points, *angle.vector1.points])]

def keys_for_triangle(triangle, lengths):
    keys = []
    if lengths is None or 3 in lengths:
        keys.append(frozenset(triangle))
    if lengths is None or 2 in lengths:
        keys += [frozenset(triangle[1:]), frozenset(triangle[:-1]), frozenset([triangle[0], triangle[2]])]
    return keys

class Property:
    def __str__(self):
        return str(self.description)

    def keys(self):
        return []

class EquilateralTriangleProperty(Property):
    """
    A triangle is equilateral
    """
    def __init__(self, ABC):
        self.ABC = list(ABC)

    def keys(self, lengths=None):
        return keys_for_triangle(self.ABC, lengths)

    @property
    def description(self):
        return _comment('△ %s %s %s is equilateral', *self.ABC)

class CollinearProperty(Property):
    """
    Three points are collinear
    """
    def __init__(self, A, B, C):
        self.points = (A, B, C)

    def keys(self):
        return [frozenset(self.points)]

    @property
    def description(self):
        return _comment('Points %s, %s, and %s are collinear', *self.points)

    def __eq__(self, other):
        return isinstance(other, CollinearProperty) and set(self.points) == set(other.points)

class NonCollinearProperty(Property):
    """
    Three points are not collinear
    """
    def __init__(self, point0, point1, point2):
        self.points = [point0, point1, point2]

    def keys(self):
        return [frozenset(self.points)]

    @property
    def description(self):
        return _comment('Points %s, %s, and %s are not collinear', *self.points)

    def __eq__(self, other):
        return isinstance(other, NonCollinearProperty) and set(self.points) == set(other.points)

class AngleValueProperty(Property):
    """
    Angle value
    """
    def __init__(self, angle, degree):
        self.angle = angle
        self.degree = degree

    def keys(self):
        return keys_for_angle(self.angle)

    @property
    def description(self):
        if self.degree == 0:
            if self.angle.vertex is not None:
                return _comment('%s, %s in the same direction from %s', self.angle.vector0.end, self.angle.vector1.end, self.angle.vertex)
        return _comment('%s = %dº', self.angle, self.degree)

    def __eq__(self, other):
        if not isinstance(other, AngleValueProperty):
            return False
        if self.degree == 180:
            return self.angle == other.angle or self.angle.reversed == other.angle
        return \
            (self.degree == other.degree and self.angle == other.angle) or \
            (self.degree == -other.degree and self.angle.reversed == other.angle)

class AnglesRatioProperty(Property):
    """
    Two angle values ratio
    """
    def __init__(self, angle0, angle1, ratio):
        # angle0 / angle1 = ratio
        self.angle0 = angle0
        self.angle1 = angle1
        self.ratio = ratio

    def keys(self):
        return keys_for_angle(self.angle0) + keys_for_angle(self.angle1)

    @property
    def description(self):
        if self.ratio == 1:
            return _comment('%s = %s', self.angle0, self.angle1)
        else:
            return _comment('%s = %s %s', self.angle0, self.ratio, self.angle1)

    def __eq__(self, other):
        if not isinstance(other, AnglesRatioProperty):
            return False
        return self.ratio == other.ratio and \
            ((self.angle0 == other.angle0 and self.angle1 == other.angle1) or \
             (self.angle0 == other.angle1 and self.angle1 == other.angle0) or \
             (self.angle0 == other.angle0.reversed and self.angle1 == other.angle1.reversed) or \
             (self.angle0 == other.angle1.reversed and self.angle1 == other.angle0.reversed))

class ParallelVectorsProperty(Property):
    """
    Two vectors are parallel (or at least one of them has zero length)
    """
    def __init__(self, vector0, vector1):
        self.vector0 = vector0
        self.vector1 = vector1

    def keys(self):
        return keys_for_vector(self.vector0) + keys_for_vector(self.vector1)

    @property
    def description(self):
        return _comment('%s ↑↑ %s', self.vector0, self.vector1)

class CongruentSegmentProperty(Property):
    """
    Two segments are congruent
    """
    def __init__(self, vector0, vector1):
        self.vector0 = vector0
        self.vector1 = vector1

    def keys(self):
        return keys_for_vector(self.vector0) + keys_for_vector(self.vector1)

    @property
    def description(self):
        return _comment('|%s| = |%s|', self.vector0, self.vector1)

class SimilarTrianglesProperty(Property):
    """
    Two triangles are similar
    """
    def __init__(self, ABC, DEF):
        self.ABC = list(ABC)
        self.DEF = list(DEF)

    def keys(self, lengths=None):
        return keys_for_triangle(self.ABC, lengths) + keys_for_triangle(self.DEF, lengths)

    @property
    def description(self):
        return _comment('△ %s %s %s ~ △ %s %s %s', *self.ABC, *self.DEF)

class CongruentTrianglesProperty(Property):
    """
    Two triangles are congruent
    """
    def __init__(self, ABC, DEF):
        self.ABC = list(ABC)
        self.DEF = list(DEF)

    def keys(self, lengths=None):
        return keys_for_triangle(self.ABC, lengths) + keys_for_triangle(self.DEF, lengths)

    @property
    def description(self):
        return _comment('△ %s %s %s = △ %s %s %s', *self.ABC, *self.DEF)

class IsoscelesTriangleProperty(Property):
    """
    A triangle is isosceles
    """
    def __init__(self, A, BC):
        self.A = A
        self.BC = list(BC)

    def keys(self, lengths=None):
        return keys_for_triangle([self.A] + self.BC, lengths)

    @property
    def description(self):
        return _comment('△ %s %s %s is isosceles (with apex %s)', self.A, *self.BC, self.A)
