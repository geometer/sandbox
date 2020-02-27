"""
Core module.
Normally, do not add new construction methods here, do this in scene.py instead.
"""

from enum import Enum, auto, unique
import itertools
from typing import List

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
                        self.auto_label = True
                        break
            if 'auxiliary' not in kwargs:
                self.auxiliary = None

            self.extra_labels = set()
            self.scene = scene
            self.__dict__.update(kwargs)
            scene.add(self)

        def with_extra_args(self, **kwargs):
            if not kwargs.get('auxiliary'):
                self.auxiliary = None
            for key in kwargs:
                if key == 'auxiliary':
                    continue
                value = kwargs[key]
                if key == 'label' and value and value != self.label:
                    if hasattr(self, 'auto_label'):
                        self.label = value
                        delattr(self, 'auto_label')
                    else:
                        self.extra_labels.add(value)
                elif not hasattr(self, key):
                    self.__dict__[key] = value
            return self

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
                elif isinstance(value, (list, tuple, set)):
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
            new_point = CoreScene.Point(
                self.scene,
                CoreScene.Point.Origin.ratio,
                point0=self, point1=point, coef0=coef0, coef1=coef1, **kwargs
            )
            new_point.belongs_to(self.line_through(point, auxiliary=True))
            return new_point

        def line_through(self, point, **kwargs):
            self.scene.assert_point(point)
            assert self != point, 'Cannot create a line by a single point'
            self.not_equal_constraint(point)

            for existing in self.scene.lines():
                if self in existing.all_points and point in existing.all_points:
                    return existing.with_extra_args(**kwargs)

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

        def belongs_to(self, line_or_circle):
            self.scene.assert_line_or_circle(line_or_circle)
            line_or_circle.all_points.add(self)

        def not_equal_constraint(self, A, **kwargs):
            """
            The current point does not coincide with A.
            """
            for cnstr in self.scene.constraints(Constraint.Kind.not_equal):
                if set(cnstr.params) == set([self, A]):
                    return
#                if cnstr.params[0] == self and cnstr.params[1] == A:
#                    return
#                if cnstr.params[0] == A and cnstr.params[1] == self:
#                    return
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
            self.all_points = set([self.point0, self.point1])

        def free_point(self, **kwargs):
            point = CoreScene.Point(self.scene, CoreScene.Point.Origin.line, line=self, **kwargs)
            point.belongs_to(self)
            return point

        def intersection_point(self, obj, **kwargs):
            """
            Creates an intersection point of the line and given object (line or circle).
            Requires a constraint for determinate placement if the object a circle
            """
            self.scene.assert_line_or_circle(obj)
            assert self != obj, 'The line does not cross itself'
            if isinstance(obj, CoreScene.Circle):
                crossing = CoreScene.Point(
                    self.scene,
                    CoreScene.Point.Origin.circle_x_line,
                    circle=obj, line=self, **kwargs
                )
            else:
                existing_points = [pt for pt in self.all_points if pt in obj.all_points]
                if len(existing_points) == 1:
                    return existing_points[0].with_extra_args(**kwargs)
                assert len(existing_points) == 0

                crossing = CoreScene.Point(
                    self.scene,
                    CoreScene.Point.Origin.line_x_line,
                    line0=self, line1=obj, **kwargs
                )

            crossing.belongs_to(self)
            crossing.belongs_to(obj)
            return crossing

    class Circle(Object):
        def __init__(self, scene, **kwargs):
            CoreScene.Object.__init__(self, scene, **kwargs)
            self.all_points = set()
            if self.centre == self.radius_start:
                self.all_points.add(self.radius_end)
            elif self.centre == self.radius_end:
                self.all_points.add(self.radius_start)

        def free_point(self, **kwargs):
            point = CoreScene.Point(self.scene, CoreScene.Point.Origin.circle, circle=self, **kwargs)
            point.belongs_to(self)
            return point

        def intersection_point(self, obj, **kwargs):
            """
            Creates an intersection point of the circle and given object (line or circle).
            Requires a constraint for determinate placement
            """
            self.scene.assert_line_or_circle(obj)
            assert self != obj, 'The circle does not cross itself'
            if isinstance(obj, CoreScene.Circle):
                crossing = CoreScene.Point(
                    self.scene,
                    CoreScene.Point.Origin.circle_x_circle,
                    circle0=self, circle1=obj, **kwargs
                )
            else:
                crossing = CoreScene.Point(
                    self.scene,
                    CoreScene.Point.Origin.circle_x_line,
                    circle=self, line=obj, **kwargs
                )

            crossing.belongs_to(self)
            crossing.belongs_to(obj)
            return crossing

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

    def convex_polygon_constraint(self, *points, **kwargs):
        """
        *points (in given order) is a convex polygon.
        """
        assert len(points) > 3
        self.constraint(Constraint.Kind.convex_polygon, points, **kwargs)

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

    def angles_ratio_constraint(self, ABCD, EFGH, ratio, **kwargs):
        self.constraint(
            Constraint.Kind.angles_ratio,
            ABCD[0][0], ABCD[0][1], ABCD[1][0], ABCD[1][1],
            EFGH[0][0], EFGH[0][1], EFGH[1][0], EFGH[1][1],
            ratio,
            **kwargs
        )

    def points(self, skip_auxiliary=False):
        if skip_auxiliary:
            return [p for p in self.__objects if isinstance(p, CoreScene.Point) and not p.auxiliary]
        else:
            return [p for p in self.__objects if isinstance(p, CoreScene.Point)]

    def lines(self, skip_auxiliary=False):
        if skip_auxiliary:
            return [l for l in self.__objects if isinstance(l, CoreScene.Line) and not l.auxiliary]
        else:
            return [l for l in self.__objects if isinstance(l, CoreScene.Line)]

    def constraints(self, kind):
        if kind.stage == Stage.validation:
            return [cnstr for cnstr in self.validation_constraints if cnstr.kind == kind]
        else:
            return [cnstr for cnstr in self.adjustment_constraints if cnstr.kind == kind]

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

    def get(self, label: str):
        for obj in self.__objects:
            if obj.label == label or label in obj.extra_labels:
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
        convex_polygon    = ('convex_polygon', Stage.validation, List[CoreScene.Point])
        inside_triangle   = ('inside_triangle', Stage.validation, CoreScene.Point, CoreScene.Point, CoreScene.Point, CoreScene.Point)
        distance          = ('distance', Stage.adjustment, CoreScene.Point, CoreScene.Point, int)
        distances_ratio   = ('distances_ratio', Stage.adjustment, CoreScene.Point, CoreScene.Point, CoreScene.Point, CoreScene.Point, int)
        right_angle       = ('right_angle', Stage.adjustment, CoreScene.Point, CoreScene.Point, CoreScene.Point, CoreScene.Point)
        angles_ratio      = ('angles_ratio', Stage.adjustment, CoreScene.Point, CoreScene.Point, CoreScene.Point, CoreScene.Point, CoreScene.Point, CoreScene.Point, CoreScene.Point, CoreScene.Point, int)

        def __init__(self, name, stage, *params):
            self.stage = stage
            self.params = params

    def __init__(self, kind, scene, *args, **kwargs):
        assert isinstance(kind, Constraint.Kind)
        assert len(args) == len(kind.params)
        self.params = []
        for (arg, knd) in zip(args, kind.params):
            if knd == List[CoreScene.Point]:
                knd = knd.__origin__
            if issubclass(knd, CoreScene.Object):
                if isinstance(arg, str):
                    arg = scene.get(arg)
                scene.assert_type(arg, knd)
            elif issubclass(knd, List):
                # TODO: check element types
                assert isinstance(arg, list) or isinstance(arg, tuple)
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
