import sympy as sp

def divide(num0, num1):
    ratio = sp.sympify(num0) / num1
    return int(ratio) if ratio.is_integer else ratio

def normalize_number(num):
    if isinstance(num, int):
        return num
    return int(num) if num.is_integer else num

def good_angles(angle):
    """
    Returns list of pairs (ang, complementary) where ang is an angle
    consisting of the same segments as the given angle, and
    complementary is False if the values of ang and the given value is the same
    and True if ang is complementary to the given angle.

    The list contains one pair if the segments have a common endpoint,
    and four pairs otherwise.
    """
    def rev(first, second):
        if first or second:
            vec0 = angle.vector0.reversed if first else angle.vector0
            vec1 = angle.vector1.reversed if second else angle.vector1
            return vec0.angle(vec1)
        return angle

    if angle.vertex is not None:
        return [(angle, False)]
    if angle.vector0.start == angle.vector1.end:
        return [(rev(False, True), True)]
    if angle.vector0.end == angle.vector1.start:
        return [(rev(True, False), True)]
    if angle.vector0.end == angle.vector1.end:
        return [(rev(True, True), False)]
    return [
        (angle, False),
        (rev(False, True), True),
        (rev(True, False), True),
        (rev(True, True), False)
    ]

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
