import itertools
from .util import _comment, divide, good_angles, normalize_number

def keys_for_vector(vector):
    return [frozenset(vector.points)]

def keys_for_triangle(triangle, lengths):
    keys = []
    if lengths is None or 3 in lengths:
        keys.append(frozenset(triangle))
    if lengths is None or 2 in lengths:
        keys += [frozenset(triangle[1:]), frozenset(triangle[:-1]), frozenset([triangle[0], triangle[2]])]
    return keys

class Property:
    def keys(self):
        return []

    def __str__(self):
        return str(self.description)

class NonCollinearProperty(Property):
    """
    Three points are not collinear
    """
    def __init__(self, point0, point1, point2):
        self.points = (point0, point1, point2)
        self.__point_set = frozenset(self.points)

    def keys(self):
        return [self.__point_set]

    @property
    def description(self):
        return _comment('Points %s, %s, and %s are not collinear', *self.points)

    def __eq__(self, other):
        return isinstance(other, NonCollinearProperty) and self.__point_set == other.__point_set

    def __hash__(self):
        return hash(NonCollinearProperty) + hash(self.__point_set)

class ParallelVectorsProperty(Property):
    """
    Two vectors are parallel (or at least one of them has zero length)
    """
    def __init__(self, vector0, vector1):
        self.vector0 = vector0
        self.vector1 = vector1
        self.__vector_set = frozenset([vector0, vector1])

    def keys(self):
        return keys_for_vector(self.vector0) + keys_for_vector(self.vector1)

    @property
    def description(self):
        return _comment('%s ↑↑ %s', self.vector0, self.vector1)

    def __eq__(self, other):
        return isinstance(other, ParallelVectorsProperty) and \
            self.__vector_set == other.__vector_set

    def __hash__(self):
        return hash(ParallelVectorsProperty) + hash(self.__vector_set)

class NotEqualProperty(Property):
    """
    The distance between two points is non-zero
    """
    def __init__(self, point0, point1):
        self.points = [point0, point1]
        self.__point_set = frozenset(self.points)

    def keys(self):
        return [self.__point_set, *self.points]

    @property
    def description(self):
        return _comment('%s != %s', *self.points)

    def __eq__(self, other):
        return isinstance(other, NotEqualProperty) and self.__point_set == other.__point_set

    def __hash__(self):
        return hash(NotEqualProperty) + hash(self.__point_set)

class OppositeSideProperty(Property):
    """
    Two points are located on opposite sides of the line
    """
    def __init__(self, line, point0, point1):
        self.line = line
        self.points = (point0, point1)
        self.__object_set = frozenset([line, point0, point1])

    def keys(self):
        return [self.__object_set]

    @property
    def description(self):
        return _comment('%s, %s located on opposite sides of %s', *self.points, self.line)

    def __eq__(self, other):
        return isinstance(other, OppositeSideProperty) and self.__object_set == other.__object_set

    def __hash__(self):
        return hash(OppositeSideProperty) + hash(self.__object_set)

class SameSideProperty(Property):
    """
    Two points are located on the same side of the line
    """
    def __init__(self, line, point0, point1):
        self.line = line
        self.points = (point0, point1)
        self.__object_set = frozenset([line, point0, point1])

    def keys(self):
        return [self.__object_set]

    @property
    def description(self):
        return _comment('%s, %s located on the same side of %s', *self.points, self.line)

    def __eq__(self, other):
        return isinstance(other, SameSideProperty) and self.__object_set == other.__object_set

    def __hash__(self):
        return hash(SameSideProperty) + hash(self.__object_set)

class EquilateralTriangleProperty(Property):
    """
    A triangle is equilateral
    """
    def __init__(self, ABC):
        self.ABC = tuple(ABC)
        self.__point_set = frozenset(self.ABC)

    def keys(self, lengths=None):
        return keys_for_triangle(self.ABC, lengths)

    @property
    def description(self):
        return _comment('△ %s %s %s is equilateral', *self.ABC)

    def __eq__(self, other):
        return isinstance(other, EquilateralTriangleProperty) and self.__point_set == other.__point_set

    def __hash__(self):
        return hash(EquilateralTriangleProperty) + hash(self.__point_set)

class CollinearProperty(Property):
    """
    Three points are collinear
    """
    def __init__(self, A, B, C):
        self.points = (A, B, C)
        self.__point_set = frozenset(self.points)

    def keys(self):
        return [self.__point_set]

    @property
    def description(self):
        return _comment('Points %s, %s, and %s are collinear', *self.points)

    def __eq__(self, other):
        return isinstance(other, CollinearProperty) and self.__point_set == other.__point_set

    def __hash__(self):
        return hash(CollinearProperty) + hash(self.__point_set)

class AngleValueProperty(Property):
    """
    Angle value
    """
    @staticmethod
    def generate(angle, value):
        for ngl, complementary in good_angles(angle):
            yield AngleValueProperty(ngl, 180 - value if complementary else value)

    def __init__(self, angle, degree):
        self.angle = angle
        self.degree = normalize_number(degree)

    def keys(self):
        return [self.angle.points]

    @property
    def description(self):
        if self.degree == 0:
            if self.angle.vertex is not None:
                return _comment('%s, %s in the same direction from %s', self.angle.vector0.end, self.angle.vector1.end, self.angle.vertex)
        return _comment('%s = %dº', self.angle, self.degree)

    def __eq__(self, other):
        if not isinstance(other, AngleValueProperty):
            return False
        return self.angle == other.angle

    def __hash__(self):
        return hash(AngleValueProperty) + hash(self.angle)

class AnglesRatioProperty(Property):
    """
    Two angle values ratio
    """
    def __init__(self, angle0, angle1, ratio):
        # angle0 / angle1 = ratio
        if ratio < 0:
            ratio = -ratio

        if ratio >= 1:
            self.angle0 = angle0
            self.angle1 = angle1
            self.ratio = normalize_number(ratio)
        else:
            self.angle0 = angle1
            self.angle1 = angle0
            self.ratio = divide(1, ratio)

        self.__hash = None

    def keys(self):
        return [self.angle0.points, self.angle1.points, self.angle0, self.angle1]

    @property
    def description(self):
        if self.ratio == 1:
            return _comment('%s = %s', self.angle0, self.angle1)
        else:
            return _comment('%s = %s %s', self.angle0, self.ratio, self.angle1)

    def __eq__(self, other):
        if not isinstance(other, AnglesRatioProperty):
            return False

        if self.angle0 == other.angle0:
            return self.angle1 == other.angle1
        if self.ratio == 1:
            if self.angle0 == other.angle1:
                return self.angle1 == other.angle0
        return False

    def __hash__(self):
        if self.__hash is None:
            self.__hash = hash(AnglesRatioProperty) + hash(self.angle0) + hash(self.angle1)
        return self.__hash

class SumOfAnglesProperty(Property):
    """
    Sum of two angles is equal to degree
    """
    def __init__(self, angle0, angle1, degree):
        self.angle0 = angle0
        self.angle1 = angle1
        self.degree = degree
        self.angle_set = frozenset([angle0, angle1])

    def keys(self):
        return [self.angle0.points, self.angle1.points, self.angle0, self.angle1]

    @property
    def description(self):
        return _comment('%s + %s == %sº', self.angle0, self.angle1, self.degree)

    def __eq__(self, other):
        return isinstance(other, SumOfAnglesProperty) and self.angle_set == other.angle_set

    def __hash__(self):
        return hash(SumOfAnglesProperty) + hash(self.angle_set)

class CongruentSegmentProperty(Property):
    """
    Two segments are congruent
    """
    def __init__(self, vector0, vector1):
        self.vector0 = vector0
        self.vector1 = vector1
        self.__vector_set = frozenset([
            frozenset([vector0.start, vector0.end]),
            frozenset([vector1.start, vector1.end])
        ])

    def keys(self):
        return keys_for_vector(self.vector0) + keys_for_vector(self.vector1)

    @property
    def description(self):
        return _comment('|%s| = |%s|', self.vector0, self.vector1)

    def __eq__(self, other):
        return isinstance(other, CongruentSegmentProperty) and \
            self.__vector_set == other.__vector_set

    def __hash__(self):
        return hash(CongruentSegmentProperty) + hash(self.__vector_set)

class SimilarTrianglesProperty(Property):
    """
    Two triangles are similar
    """
    def __init__(self, ABC, DEF):
        self.ABC = tuple(ABC)
        self.DEF = tuple(DEF)
        pairs = [frozenset([(ABC[i], ABC[j], ABC[k]), (DEF[i], DEF[j], DEF[k])]) for i, j, k in itertools.permutations(range(0, 3), 3)]
        self.__triangle_set = frozenset(pairs)

    def keys(self, lengths=None):
        return keys_for_triangle(self.ABC, lengths) + keys_for_triangle(self.DEF, lengths)

    @property
    def description(self):
        return _comment('△ %s %s %s ~ △ %s %s %s', *self.ABC, *self.DEF)

    def __eq__(self, other):
        return isinstance(other, SimilarTrianglesProperty) and \
            self.__triangle_set == other.__triangle_set

    def __hash__(self):
        return hash(SimilarTrianglesProperty) + hash(self.__triangle_set)

class CongruentTrianglesProperty(Property):
    """
    Two triangles are congruent
    """
    def __init__(self, ABC, DEF):
        self.ABC = tuple(ABC)
        self.DEF = tuple(DEF)
        pairs = [frozenset([(ABC[i], ABC[j], ABC[k]), (DEF[i], DEF[j], DEF[k])]) for i, j, k in itertools.permutations(range(0, 3), 3)]
        self.__triangle_set = frozenset(pairs)

    def keys(self, lengths=None):
        return keys_for_triangle(self.ABC, lengths) + keys_for_triangle(self.DEF, lengths)

    @property
    def description(self):
        return _comment('△ %s %s %s = △ %s %s %s', *self.ABC, *self.DEF)

    def __eq__(self, other):
        return isinstance(other, CongruentTrianglesProperty) and \
            self.__triangle_set == other.__triangle_set

    def __hash__(self):
        return hash(CongruentTrianglesProperty) + hash(self.__triangle_set)

class IsoscelesTriangleProperty(Property):
    """
    A triangle is isosceles
    """
    def __init__(self, apex, base):
        self.apex = apex
        self.base = tuple(base)
        self.__base_points_set = frozenset(self.base)

    def keys(self, lengths=None):
        return keys_for_triangle([self.apex, *self.base], lengths)

    @property
    def description(self):
        return _comment('△ %s %s %s is isosceles (with apex %s)', self.apex, *self.base, self.apex)

    def __eq__(self, other):
        return isinstance(other, IsoscelesTriangleProperty) and \
            self.apex == other.apex and self.__base_points_set == other.__base_points_set

    def __hash__(self):
        return hash(IsoscelesTriangleProperty) + hash(self.apex) + hash(self.__base_points_set)
