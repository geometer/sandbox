import sympy as sp

def side_of(triangle, index):
    return triangle[(index + 1) % 3].segment(triangle[(index + 2) % 3])

def angle_of(triangle, index):
    return triangle[index].angle(triangle[(index + 1) % 3], triangle[(index + 2) % 3])

def divide(num0, num1):
    if isinstance(num0, int) and isinstance(num1, int):
        quot = num0 // num1
        if quot * num1 == num0:
            return quot
    ratio = sp.sympify(num0) / num1
    return int(ratio) if ratio.is_integer else ratio

def normalize_number(num):
    if isinstance(num, int):
        return num
    return int(num) if num.is_integer else num

def good_angles(vector0, vector1, include_four_point=False):
    """
    Returns list of pairs (ang, complementary) where ang is an angle
    consisting of the same segments as the given vectors, and
    complementary is False if the values of ang and the given value is the same
    and True if ang is complementary to the vector0.angle(vector1).

    The list contains one pair if the segments have a common endpoint,
    and two pairs otherwise.
    """
    def rev(first, second):
        vec0 = vector0.reversed if first else vector0
        vec1 = vector1.reversed if second else vector1
        return vec0.angle(vec1)

    if vector0.start == vector1.start:
        return [(rev(False, False), False)]
    if vector0.start == vector1.end:
        return [(rev(False, True), True)]
    if vector0.end == vector1.start:
        return [(rev(True, False), True)]
    if vector0.end == vector1.end:
        return [(rev(True, True), False)]
    if include_four_point:
        return [
            (rev(False, False), False),
            (rev(False, True), True)
        ]
    return []

class ParametrizedString:
    def __init__(self, format_string, *params):
        self.format_string = format_string
        self.params = params

    def __eq__(self, other):
        return isinstance(other, ParametrizedString) and self.format_string == other.format_string and self.params == other.params

    def __str__(self):
        from .core import CoreScene
        return self.format_string % tuple(p.name if isinstance(p, CoreScene.Object) else p for p in self.params)

def _comment(*args):
    return ParametrizedString(*args)