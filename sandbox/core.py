"""
Core module.
Normally, do not add new construction methods here, do this in scene.py instead.
"""

from enum import Enum, auto, unique
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
            scene.add(self)

        def __str__(self):
            dct = {}
            for key in self.__dict__:
                if key in ('label', 'scene'):
                    continue
                value = self.__dict__[key]
                if value is None:
                    continue
                if isinstance(value, Enum):
                    dct[key] = value.name
                elif isinstance(value, CoreScene.Object):
                    dct[key] = value.label
                elif isinstance(value, (list, tuple)):
                    if value:
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
            return CoreScene.Point(
                self.scene,
                CoreScene.Point.Origin.ratio,
                point0=self, point1=point, coef0=coef0, coef1=coef1, **kwargs
            )

        def line_through(self, point, **kwargs):
            self.scene.assert_point(point)
            assert self != point, 'Cannot create a line by a single point'
            self.not_equal_constraint(point)
            return CoreScene.Line(self.scene, point0=self, point1=point, **kwargs)

        def circle_through(self, point, **kwargs):
            self.scene.assert_point(point)
            assert self != point, 'Cannot create a circle of zero radius'
            return CoreScene.Circle(
                self.scene, centre=self, radius_start=self, radius_end=point, **kwargs
            )

        def circle_with_radius(self, start, end, **kwargs):
            self.scene.assert_point(start)
            self.scene.assert_point(end)
            assert start != end, 'Cannot create a circle of zero radius'
            return CoreScene.Circle(
                self.scene, centre=self, radius_start=start, radius_end=end, **kwargs
            )

        def not_equal_constraint(self, A, **kwargs):
            """
            The current point does not coincide with A.
            """
            self.scene.constraint(Constraint.Kind.not_equal, self, A, **kwargs)

        def not_collinear_constraint(self, A, B, **kwargs):
            """
            The current point does not collinear with A and B.
            """
            self.scene.constraint(Constraint.Kind.not_collinear, self, A, B, **kwargs)

        def distance_constraint(self, A, distance, **kwargs):
            """
            Distance to the point A equals to the given distance.
            The given distance must be an integer.
            """
            if distance > 0:
                self.not_equal_constraint(A)
            self.scene.constraint(Constraint.Kind.distance, self, A, distance, **kwargs)

        def opposite_side_constraint(self, point, line, **kwargs):
            """
            The current point lies on the opposite side to the line than the given point.
            """
            if isinstance(point, CoreScene.Line) and isinstance(line, CoreScene.Point):
                point, line = line, point
            self.scene.constraint(Constraint.Kind.opposite_side, self, point, line, **kwargs)

        def same_side_constraint(self, point, line, **kwargs):
            """
            The current point lies on the same side to the line as the given point.
            """
            if isinstance(point, CoreScene.Line) and isinstance(line, CoreScene.Point):
                point, line = line, point
            self.scene.constraint(Constraint.Kind.same_side, self, point, line, **kwargs)

        def inside_triangle_constraint(self, A, B, C, **kwargs):
            """
            The current point is inside the △ABC
            """
            self.scene.constraint(Constraint.Kind.inside_triangle, self, A, B, C, **kwargs)

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
                return CoreScene.Point(
                    self.scene,
                    CoreScene.Point.Origin.circle_x_line,
                    circle=obj, line=self, **kwargs
                )
            else:
                return CoreScene.Point(
                    self.scene,
                    CoreScene.Point.Origin.line_x_line,
                    line0=self, line1=obj, **kwargs
                )

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
                return CoreScene.Point(
                    self.scene,
                    CoreScene.Point.Origin.circle_x_circle,
                    circle0=self, circle1=obj, **kwargs
                )
            else:
                return CoreScene.Point(
                    self.scene,
                    CoreScene.Point.Origin.circle_x_line,
                    circle=self, line=obj, **kwargs
                )

    def __init__(self):
        self.__objects = []
        self.validation_constraints = []
        self.adjustment_constraints = []

    def constraint(self, kind, *args, **kwargs):
        cns = Constraint(kind, self, *args, **kwargs)
        if kind.stage == Stage.validation:
            self.validation_constraints.append(cns)
        else:
            self.adjustment_constraints.append(cns)

    def quadrilateral_constraint(self, A, B, C, D, **kwargs):
        """
        ABDC is a quadrilateral.
        I.e., the polygonal chain ABCD does not cross itself and contains no 180º angles.
        """
        self.constraint(Constraint.Kind.quadrilateral, A, B, C, D, **kwargs)

    def distances_ratio_constraint(self, AB, CD, ratio, **kwargs):
        """
        |AB| == |CD| * ratio
        AB and CD are tuples or lists of two points, ratio is an integer
        """
        assert len(AB) == 2 and len(CD) == 2
        self.constraint(Constraint.Kind.distances_ratio, AB[0], AB[1], CD[0], CD[1], ratio, **kwargs)

    def equal_distances_constraint(self, AB, CD, **kwargs):
        """
        |AB| == |CD|
        AB and CD are tuples or lists of two points
        """
        self.distances_ratio_constraint(AB, CD, 1, **kwargs)

    def right_angle_constraint(self, AB, CD, **kwargs):
        """
        AB ⟂ CD
        AB and CD are tuples or lists of two points
        """
        assert len(AB) == 2 and len(CD) == 2
        self.constraint(Constraint.Kind.right_angle, AB[0], AB[1], CD[0], CD[1], **kwargs)

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

    def dump(self):
        print('Objects:')
        print('\n'.join(['\t' + str(obj) for obj in self.__objects]))
        count = len(self.__objects)
        aux = len([o for o in self.__objects if o.auxiliary])
        print('Total: %s objects (+ %s auxiliary)' % (count - aux, aux))
        if self.validation_constraints:
            print('\nValidation constraints:')
            print('\n'.join(['\t' + str(cnstr) for cnstr in self.validation_constraints]))
        if self.adjustment_constraints:
            print('\nAdjustment constraints:')
            print('\n'.join(['\t' + str(cnstr) for cnstr in self.adjustment_constraints]))
        print('')

class Stage(Enum):
    validation        = auto()
    adjustment        = auto()

class Constraint:
    @unique
    class Kind(Enum):
        not_equal         = ('not_equal', Stage.validation, CoreScene.Point, CoreScene.Point)
        not_collinear     = ('not_collinear', Stage.validation, CoreScene.Point, CoreScene.Point, CoreScene.Point)
        opposite_side     = ('opposite_side', Stage.validation, CoreScene.Point, CoreScene.Point, CoreScene.Line)
        same_side         = ('same_side', Stage.validation, CoreScene.Point, CoreScene.Point, CoreScene.Line)
        quadrilateral     = ('quadrilateral', Stage.validation, CoreScene.Point, CoreScene.Point, CoreScene.Point, CoreScene.Point)
        inside_triangle   = ('inside_triangle', Stage.validation, CoreScene.Point, CoreScene.Point, CoreScene.Point, CoreScene.Point)
        distance          = ('distance', Stage.adjustment, CoreScene.Point, CoreScene.Point, int)
        distances_ratio   = ('distances_ratio', Stage.adjustment, CoreScene.Point, CoreScene.Point, CoreScene.Point, CoreScene.Point, int)
        right_angle       = ('right_angle', Stage.adjustment, CoreScene.Point, CoreScene.Point, CoreScene.Point, CoreScene.Point)

        def __init__(self, name, stage, *params):
            self.stage = stage
            self.params = params

    def __init__(self, kind, scene, *args, **kwargs):
        assert isinstance(kind, Constraint.Kind)
        assert len(args) == len(kind.params)
        self.params = []
        for (arg, knd) in zip(args, kind.params):
            if issubclass(knd, CoreScene.Object):
                if isinstance(arg, str):
                    arg = scene.get(arg)
                scene.assert_type(arg, knd)
            else:
                assert isinstance(arg, knd)
            self.params.append(arg)
        self.kind = kind
        self.__dict__.update(kwargs)

    def __str__(self):
        return 'Constraint(%s) %s' % (
            self.kind.name,
            [para.label if isinstance(para, CoreScene.Object) else para for para in self.params]
        )
