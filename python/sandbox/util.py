import re
import sympy as sp
from pylatexenc.latex2text import LatexNodes2Text

def degree_to_string(degree):
    if isinstance(degree, sp.Number):
        if not degree.is_integer and (2 * degree).is_integer:
            return '%.1fº' % degree
    return '%sº' % degree

def keys_for_triangle(triangle, lengths):
    collection = []
    if lengths is None or 3 in lengths:
        collection += triangle.angles
    if lengths is None or 2 in lengths:
        collection += triangle.sides
    return collection

class SimplificationCache:
    def __init__(self):
        self.cache = {}
        for num in (sp.sympify(1) / 2, sp.sympify(1) / 4, sp.sympify(3) / 4):
            self.cache[num] = num
        for num in (sp.sqrt(3), sp.sqrt(3) / 3):
            self.cache[num] = num

simplification = SimplificationCache()

def simplify(num):
    if isinstance(num, int) or num.is_integer:
        return num

    cached_value = simplification.cache.get(num)
    if cached_value:
        return cached_value
    result = sp.simplify(num)
    simplification.cache[num] = result
    simplification.cache[result] = result
    return result

def divide(num0, num1):
    if isinstance(num0, int) and isinstance(num1, int):
        quot = num0 // num1
        if quot * num1 == num0:
            return quot
    ratio = simplify(sp.sympify(num0) / num1)
    return int(ratio) if ratio.is_integer else ratio

def normalize_number(num):
    if isinstance(num, int):
        return num
    if num.is_integer:
        return int(num)
    num = simplify(num)
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

class LazyComment:
    def __init__(self, format_string, *params):
        self.format_string = format_string
        self.params = params

    def stringify(self, printer):
        if printer:
            def htmlize(obj):
                from .figure import Figure
                if isinstance(obj, Figure):
                    return '<span class="missing"></span>'
                while hasattr(obj, 'stringify'):
                    obj = obj.stringify(printer)
                return obj
            return self.format_string % tuple(htmlize(p) for p in self.params)
        return str(self)

    def __str__(self):
        from .core import CoreScene
        return self.format_string % tuple(p.name if isinstance(p, CoreScene.Object) else p for p in self.params)

class SimplePrinter:
    def print(self, line, params):
        def to_str(name, kind):
            obj = params[name]
            if kind == 'degree':
                return degree_to_string(obj)
            return str(obj)

        for match in re.finditer('%{(?P<type>[^:}]*):(?P<name>[^}]*)}', line):
            line = line.replace(match.group(0), to_str(match.group('name'), match.group('type')))
        return LatexNodes2Text().latex_to_text(line)

class Comment:
    @staticmethod
    def validate_data(format_string, params):
        from .scene import Scene
        from .figure import Circle
        from .property import Cycle
        # TODO: validate format string + check that all params are presented in the map
        # 1) balanced $'s
        parts = format_string.split('$')
        assert len(parts) % 2 == 1, 'Unbalanced $\'s in `%s`' % format_string

        def validate_text_chunk(chunk):
            # 2) all refs inside $'s
            # 3) all TeX sequences inside $'s
            for special in '%{}\\':
                assert special not in chunk, 'Symbol `%s` outside of math area in `%s`' % (special, format_string)

        def validate_math_chunk(chunk):
            # TODO: 4) all {'s, }'s, and %'s are parts of references
            clean = re.sub(r'%{([^:}]*):([^}]*)}', '', chunk)
            for special in '%{}':
                assert special not in clean, 'Orphaned `%s` in math area `$%s$`' % (special, chunk)
            # 5) for each ref, the param is presented in the map
            # 6) for each ref, the param type is correct
            for match in re.finditer('%{(?P<type>[^:}]*):(?P<name>[^}]*)}', chunk):
                name = match.group('name')
                obj = params.get(name)
                assert obj is not None, 'No value for parameter `%s`' % name
                kind = match.group('type')
                if kind in ('number', 'multiplier', 'degree'):
                    assert isinstance(obj, int) or obj.is_number, 'Parameter `%s` of type `%s`, expected `%s`' % (name, type(obj), kind)
                elif kind == 'point':
                    assert isinstance(obj, Scene.Point), 'Parameter `%s` of type `%s`, expected `%s`' % (name, type(obj), kind)
                elif kind in ('segment', 'line'):
                    assert isinstance(obj, (Scene.Segment, Scene.Vector)), 'Parameter `%s` of type `%s`, expected `%s`' % (name, type(obj), kind)
                elif kind in ('vector', 'ray'):
                    assert isinstance(obj, Scene.Vector), 'Parameter `%s` of type `%s`, expected `%s`' % (name, type(obj), kind)
                elif kind in ('angle', 'anglemeasure'):
                    assert isinstance(obj, Scene.Angle), 'Parameter `%s` of type `%s`, expected `%s`' % (name, type(obj), kind)
                elif kind == 'triangle':
                    assert isinstance(obj, Scene.Triangle), 'Parameter `%s` of type `%s`, expected `%s`' % (name, type(obj), kind)
                elif kind == 'polygon':
                    assert isinstance(obj, Scene.Polygon), 'Parameter `%s` of type `%s`, expected `%s`' % (name, type(obj), kind)
                elif kind == 'circle':
                    assert isinstance(obj, Circle), 'Parameter `%s` of type `%s`, expected `%s`' % (name, type(obj), kind)
                elif kind == 'cycle':
                    assert isinstance(obj, Cycle), 'Parameter `%s` of type `%s`, expected `%s`' % (name, type(obj), kind)
                else:
                    assert False, 'Parameter `%s` of unknown type `%s`' % (name, kind)

        for index, chunk in enumerate(parts):
            if index % 2 == 1:
                validate_math_chunk(chunk)
            else:
                validate_text_chunk(chunk)

        return True

    def __init__(self, format_string, params={}):
        assert Comment.validate_data(format_string, params)
        self.format_string = format_string
        self.params = params

    def stringify(self, printer=SimplePrinter()):
        return printer.print(self.format_string, self.params)

    def __str__(self):
        return self.stringify()
