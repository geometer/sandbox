"""
Core module.
Normally, do not add new construction methods here, do this in scene.py instead.
"""

from enum import Enum, auto
import itertools

class CoreScene:
    class Object:
        """
        Common ancestor for all geometric objects like point, line, circle
        """

        def __init__(self, scene, **kwargs):
            assert isinstance(scene, CoreScene)
            label = kwargs.get('label')
            if label:
                assert scene.get(label) is None, 'Object with label `%s` already exists' % label
            else:
                pattern = self.__class__.__name__ + ' %d'
                for index in itertools.count():
                    label = pattern % index
                    if scene.get(label) is None:
                        self.label = label
                        break
            if 'auxiliary' not in kwargs:
                self.auxiliary = None

            self.scene = scene
            self.__dict__.update(kwargs)
            self.__constraints = None
            scene.add(self)

        def add_constraint(self, constraint):
            if self.__constraints is None:
                self.__constraints = []
            self.__constraints.append(constraint)

        @property
        def constraints(self):
            return list(self.__constraints) if self.__constraints is not None else []

        def __str__(self):
            dct = {}
            for key in self.__dict__:
                if key in ('label', 'scene'):
                    continue
                value = self.__dict__[key]
                if value is None:
                    continue
                if isinstance(value, CoreScene.Object):
                    dct[key] = value.label
                elif isinstance(value, (list, tuple)):
                    dct[key] = [elt.label if isinstance(elt, CoreScene.Object) else str(elt) for elt in value]
                else:
                    dct[key] = str(value)
            return '%s `%s` %s' % (self.__class__.__name__, self.label, dct)

    class Point(Object):
        class Origin(Enum):
            free              = auto()
            ratio             = auto()
            line              = auto() 
            circle            = auto()
            line_x_line       = auto()
            circle_x_line     = auto()
            circle_x_circle   = auto()

        def __init__(self, scene, origin, **kwargs):
            assert isinstance(origin, CoreScene.Point.Origin), 'origin must be a Point.Origin, not %s' % type(origin)
            CoreScene.Object.__init__(self, scene, origin=origin, **kwargs)

        def ratio_point(self, point, coef0: int, coef1: int, **kwargs):
            """
            Constructs new point as (coef0 * self + coef1 * point) / (coef0 + coef1).
            Requires coef0 + coef1 != 0.
            No other conditions.
            """
            self.scene.assert_point(point)
            assert coef0 + coef1 != 0
            if self == point:
                return self
            return CoreScene.Point(self.scene, CoreScene.Point.Origin.ratio, point0=self, point1=point, coef0=coef0, coef1=coef1, **kwargs)

        def line_through(self, point, **kwargs):
            self.scene.assert_point(point)
            assert self != point, 'Cannot create a line by a single point'
            return CoreScene.Line(self.scene, point0=self, point1=point, **kwargs)

        def circle_through(self, point, **kwargs):
            self.scene.assert_point(point)
            assert self != point, 'Cannot create a circle of zero radius'
            return CoreScene.Circle(self.scene, centre=self, radius_start=self, radius_end=point, **kwargs)

        def circle_with_radius(self, start, end, **kwargs):
            self.scene.assert_point(start)
            self.scene.assert_point(end)
            assert start != end, 'Cannot create a circle of zero radius'
            return CoreScene.Circle(self.scene, centre=self, radius_start=start, radius_end=end, **kwargs)

    class Line(Object):
        def __init__(self, scene, **kwargs):
            CoreScene.Object.__init__(self, scene, **kwargs)

        def free_point(self, **kwargs):
            return CoreScene.Point(self.scene, CoreScene.Point.Origin.line, line=self, **kwargs)

        def intersection_point(self, obj, **kwargs):
            """
            Creates an intersection point of the line and given object (line or circle).
            Requires a constraint for determinate placement if the object a circle
            """
            self.scene.assert_line_or_circle(obj)
            assert self != obj, 'The line does not cross itself'
            if isinstance(obj, CoreScene.Circle):
                return CoreScene.Point(self.scene, CoreScene.Point.Origin.circle_x_line, circle=obj, line=self, **kwargs)
            else:
                return CoreScene.Point(self.scene, CoreScene.Point.Origin.line_x_line, line0=self, line1=obj, **kwargs)

    class Circle(Object):
        def __init__(self, scene, **kwargs):
            CoreScene.Object.__init__(self, scene, **kwargs)

        def free_point(self, **kwargs):
            return CoreScene.Point(self.scene, CoreScene.Point.Origin.circle, circle=self, **kwargs)

        def intersection_point(self, obj, **kwargs):
            """
            Creates an intersection point of the circle and given object (line or circle).
            Requires a constraint for determinate placement
            """
            self.scene.assert_line_or_circle(obj)
            assert self != obj, 'The circle does not cross itself'
            if isinstance(obj, CoreScene.Circle):
                return CoreScene.Point(self.scene, CoreScene.Point.Origin.circle_x_circle, circle0=self, circle1=obj, **kwargs)
            else:
                return CoreScene.Point(self.scene, CoreScene.Point.Origin.circle_x_line, circle=self, line=obj, **kwargs)

    def __init__(self):
        self.__objects = []

    def points(self, skip_auxiliary=False):
        if skip_auxiliary:
            return [p for p in self.__objects if isinstance(p, CoreScene.Point) and not p.auxiliary]
        else:
            return [p for p in self.__objects if isinstance(p, CoreScene.Point)]

    def assert_type(self, obj, *args):
        assert isinstance(obj, args), 'Unexpected type %s' % type(obj)
        assert obj.scene == self

    def assert_point(self, obj):
        self.assert_type(obj, CoreScene.Point)

    def assert_line(self, obj):
        self.assert_type(obj, CoreScene.Line)

    def assert_line_or_circle(self, obj):
        self.assert_type(obj, CoreScene.Line, CoreScene.Circle)

    def free_point(self, **kwargs):
        return CoreScene.Point(self, origin=CoreScene.Point.Origin.free, **kwargs)

    def add(self, obj: Object):
        self.__objects.append(obj)

    def get(self, key: str):
        for obj in self.__objects:
            if obj.label == key:
                return obj
        return None

    def __str__(self):
        count = len(self.__objects)
        aux = len([o for o in self.__objects if o.auxiliary])
        return '\n'.join([str(obj) for obj in self.__objects]) + \
               ('\n\nTotal: %s objects (+ %s auxiliary)\n' % (count - aux, aux))
