from .core import _comment
from .property import Property, keys_for_vector

class NonCollinearProperty(Property):
    """
    Three points are not collinear
    """
    def __init__(self, point0, point1, point2):
        self.points = [point0, point1, point2]
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

    def keys(self):
        return keys_for_vector(self.vector0) + keys_for_vector(self.vector1)

    @property
    def description(self):
        return _comment('%s ↑↑ %s', self.vector0, self.vector1)

    def __eq__(self, other):
        return isinstance(other, ParallelVectorsProperty) and \
            {self.vector0, self.vector1} == {other.vector0, other.vector1}

class NotEqualProperty(Property):
    """
    The distance between two points is non-zero
    """
    def __init__(self, point0, point1):
        self.points = [point0, point1]
        self.__point_set = frozenset(self.points)

    def keys(self):
        return [frozenset(self.points), *self.points]

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
        self.points = [point0, point1]
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
