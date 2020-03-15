import itertools
import sympy as sp

from .util import _comment

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
    def keys(self):
        return []

    def __str__(self):
        return str(self.description)

class PropertySet:
    class ByType:
        def __init__(self):
            self.all = []
            self.by_key_map = {}

    def __init__(self):
        self.by_type_map = {}

    def add(self, prop):
        key = type(prop)
        by_type = self.by_type_map.get(key)
        if by_type is None:
            by_type = PropertySet.ByType()
            self.by_type_map[key] = by_type
        by_type.all.append(prop)
        for key in prop.keys():
            arr = by_type.by_key_map.get(key)
            if arr is None:
                by_type.by_key_map[key] = [prop]
            else:
                arr.append(prop)

    def list(self, property_type, keys=None):
        by_type = self.by_type_map.get(property_type)
        if not by_type:
            return []
        if keys:
            assert isinstance(keys, list)
            sublists = [by_type.by_key_map.get(k) for k in keys]
            return list(set(itertools.chain(*[l for l in sublists if l])))
        else:
            return by_type.all

    def __len__(self):
        return sum(len(by_type.all) for by_type in self.by_type_map.values())

    @property
    def all(self):
        return list(itertools.chain(*[by_type.all for by_type in self.by_type_map.values()]))

    def __contains__(self, prop):
        by_type = self.by_type_map.get(type(prop))
        if not by_type:
            return False

        keys = prop.keys()
        lst = by_type.by_key_map.get(keys[0]) if keys else by_type.all
        return lst is not None and prop in lst

    def keys_num(self):
        return sum(len(by_type.by_key_map) for by_type in self.by_type_map.values())

    def copy(self):
        copy = PropertySet()
        for prop in self.all:
            copy.add(prop)
        return copy

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
    def __init__(self, angle, degree):
        self.angle = angle
        degree = sp.sympify(degree)
        self.degree = int(degree) if degree.is_integer else degree

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
        return self.degree == other.degree and self.angle == other.angle

    def __hash__(self):
        return hash(AngleValueProperty) + hash(self.degree) + hash(self.angle)

class AnglesRatioProperty(Property):
    """
    Two angle values ratio
    """
    def __init__(self, angle0, angle1, ratio):
        # angle0 / angle1 = ratio
        ratio = sp.sympify(ratio)
        if ratio < 0:
            ratio = -ratio

        if ratio >= 1:
            self.angle0 = angle0
            self.angle1 = angle1
            self.ratio = ratio
        else:
            self.angle0 = angle1
            self.angle1 = angle0
            self.ratio = 1 / ratio

        if self.ratio.is_integer:
            self.ratio = int(self.ratio)

        self.__hash = None

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

        if self.ratio != other.ratio:
            return False

        if self.angle0 == other.angle0:
            return self.angle1 == other.angle1
        if self.ratio == 1:
            if self.angle0 == other.angle1:
                return self.angle1 == other.angle0
        return False

    def __hash__(self):
        if self.__hash is None:
            self.__hash = hash(AnglesRatioProperty) + hash(self.ratio) + hash(self.angle0) + hash(self.angle1)
        return self.__hash

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
        self.__triangle_set = frozenset([self.ABC, self.DEF])

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
        self.__triangle_set = frozenset([self.ABC, self.DEF])

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
    def __init__(self, A, BC):
        self.A = A
        self.BC = tuple(BC)
        self.__base_points_set = frozenset(self.BC)

    def keys(self, lengths=None):
        return keys_for_triangle([self.A, *self.BC], lengths)

    @property
    def description(self):
        return _comment('△ %s %s %s is isosceles (with apex %s)', self.A, *self.BC, self.A)

    def __eq__(self, other):
        return isinstance(other, IsoscelesTriangleProperty) and \
            self.A == other.A and self.__base_points_set == other.__base_points_set

    def __hash__(self):
        return hash(IsoscelesTriangleProperty) + hash(self.A) + hash(self.__base_points_set)
