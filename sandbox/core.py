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

        @property
        def name(self):
            return self.label

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
            perp              = auto()
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
            if coef0 == 0:
                return point
            if coef1 == 0:
                return self
            new_point = CoreScene.Point(
                self.scene,
                CoreScene.Point.Origin.ratio,
                point0=self, point1=point, coef0=coef0, coef1=coef1, **kwargs
            )
            new_point.collinear_constraint(self, point, guaranteed=True)
            self.vector(new_point).length_ratio_constraint(new_point.vector(point), coef1 / coef0, guaranteed=True)
            if coef0 > 0 and coef1 > 0 or coef0 < 0 and coef1 < 0:
                self.same_direction_constraint(point, new_point, guaranteed=True)
                point.same_direction_constraint(self, new_point, guaranteed=True)
            elif coef0 < 0:
                self.same_direction_constraint(point, new_point, guaranteed=True)
                new_point.same_direction_constraint(self, point, guaranteed=True)
            elif coef1 < 0:
                new_point.same_direction_constraint(point, self, guaranteed=True)
                point.same_direction_constraint(self, new_point, guaranteed=True)
            return new_point

        def perpendicular_line(self, line, **kwargs):
            """
            Constructs a line through the point, perpendicular to the given line.
            """
            self.scene.assert_line(line)
            new_point = CoreScene.Point(
                self.scene,
                CoreScene.Point.Origin.perp,
                point=self, line=line,
                auxiliary=True
            )
            new_line = self.line_through(new_point, **kwargs)
            line.perpendicular_constraint(new_line, guaranteed=True)
            return new_line

        def line_through(self, point, **kwargs):
            self.scene.assert_point(point)
            assert self != point, 'Cannot create a line by a single point'
            self.not_equal_constraint(point)

            existing = self.scene.get_line(self, point)
            if existing:
                return existing.with_extra_args(**kwargs)

            line = CoreScene.Line(self.scene, point0=self, point1=point, **kwargs)
            for cnstr in self.scene.constraints(Constraint.Kind.collinear):
                if len([pt for pt in line.all_points if pt in cnstr.params]) == 2:
                    for pt in cnstr.params:
                        if pt not in line.all_points:
                            line.all_points.append(pt)

            return line

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

        def vector(self, point):
            return CoreScene.Vector(self, point)

        def angle(self, point0, point1):
            return self.vector(point0).angle(self.vector(point1))

        def belongs_to(self, line_or_circle):
            self.scene.assert_line_or_circle(line_or_circle)
            if self not in line_or_circle.all_points:
                line_or_circle.all_points.append(self)

        def not_equal_constraint(self, A, **kwargs):
            """
            The current point does not coincide with A.
            """
            for cnstr in self.scene.constraints(Constraint.Kind.not_equal):
                if set(cnstr.params) == set([self, A]):
                    cnstr.update(kwargs)
                    return
            self.scene.constraint(Constraint.Kind.not_equal, self, A, **kwargs)

        def not_collinear_constraint(self, A, B, **kwargs):
            """
            The current point is not collinear with A and B.
            """
            for cnstr in self.scene.constraints(Constraint.Kind.not_collinear):
                if set(cnstr.params) == set([self, A, B]):
                    cnstr.update(kwargs)
                    return
            self.not_equal_constraint(A, **kwargs)
            self.not_equal_constraint(B, **kwargs)
            A.not_equal_constraint(B, **kwargs)
            self.scene.constraint(Constraint.Kind.not_collinear, self, A, B, **kwargs)

        def collinear_constraint(self, A, B, **kwargs):
            """
            The current point is collinear with A and B.
            """
            cnstr = self.scene.constraint(Constraint.Kind.collinear, self, A, B, **kwargs)
            for line in self.scene.lines():
                if len([pt for pt in line.all_points if pt in cnstr.params]) == 2:
                    for pt in cnstr.params:
                        if pt not in line.all_points:
                            line.all_points.append(pt)

        def distance_constraint(self, A, distance, **kwargs):
            """
            Distance to the point A equals to the given distance.
            The given distance must be a non-negative number
            """
            if isinstance(A, str):
                A = self.scene.get(A)
            self.vector(A).length_constraint(distance, **kwargs)

        def opposite_side_constraint(self, point, line, **kwargs):
            """
            The current point lies on the opposite side to the line than the given point.
            """
            if isinstance(point, CoreScene.Line) and isinstance(line, CoreScene.Point):
                point, line = line, point
            for cnstr in self.scene.constraints(Constraint.Kind.opposite_side):
                if line == cnstr.params[2] and set(cnstr.params[0:2]) == set([self, point]):
                    cnstr.update(kwargs)
                    return
            self.not_collinear_constraint(line.point0, line.point1, **kwargs)
            point.not_collinear_constraint(line.point0, line.point1, **kwargs)
            self.scene.constraint(Constraint.Kind.opposite_side, self, point, line, **kwargs)

        def same_side_constraint(self, point, line, **kwargs):
            """
            The point lies on the same side to the line as the given point.
            """
            if isinstance(point, CoreScene.Line) and isinstance(line, CoreScene.Point):
                point, line = line, point
            for cnstr in self.scene.constraints(Constraint.Kind.same_side):
                if line == cnstr.params[2] and set(cnstr.params[0:2]) == set([self, point]):
                    cnstr.update(kwargs)
                    return
            self.not_collinear_constraint(line.point0, line.point1, **kwargs)
            point.not_collinear_constraint(line.point0, line.point1, **kwargs)
            self.scene.constraint(Constraint.Kind.same_side, self, point, line, **kwargs)

        def same_direction_constraint(self, A, B, **kwargs):
            """
            Vectors (self, A) and (self, B) have the same direction
            """
            for cnstr in self.scene.constraints(Constraint.Kind.same_direction):
                if self == cnstr.params[0] and set(cnstr.params[1:3]) == set([A, B]):
                    cnstr.update(kwargs)
                    return
            self.not_equal_constraint(A)
            self.not_equal_constraint(B)
            A.belongs_to(self.line_through(B, auxiliary=True))
            self.scene.constraint(Constraint.Kind.same_direction, self, A, B, **kwargs)

        def inside_angle_constraint(self, angle, **kwargs):
            """
            The point is inside the ∠ B vertex C
            """
            assert angle.vertex is not None
            B = angle.vector0.end
            C = angle.vector1.end
            self.same_side_constraint(B, angle.vertex.line_through(C), **kwargs)
            self.same_side_constraint(C, angle.vertex.line_through(B), **kwargs)

        def inside_triangle_constraint(self, A, B, C, **kwargs):
            """
            The point is inside the △ ABC
            """
            A.not_collinear_constraint(B, C)
            if 'comment' not in kwargs:
                kwargs = dict(kwargs)
                kwargs['comment'] = ParametrizedString(
                    'Point %s is inside △ %s %s %s', self, A, B, C
                )
            self.inside_angle_constraint(A.angle(B, C), **kwargs)
            self.inside_angle_constraint(B.angle(A, C), **kwargs)
            self.inside_angle_constraint(C.angle(B, A), **kwargs)

    class Line(Object):
        def __init__(self, scene, **kwargs):
            CoreScene.Object.__init__(self, scene, **kwargs)
            self.all_points = [self.point0, self.point1]

        @property
        def name(self):
            if hasattr(self, 'auto_label') and self.auto_label:
                for points in itertools.combinations(self.all_points, 2):
                    if not points[0].auxiliary and not points[1].auxiliary:
                        return '(%s %s)' % (points[0].name, points[1].name)

            return super().name

        def free_point(self, **kwargs):
            point = CoreScene.Point(self.scene, CoreScene.Point.Origin.line, line=self, **kwargs)
            point.belongs_to(self)
            return point

        def __contains__(self, obj):
            if obj is None:
                return False
            if isinstance(obj, CoreScene.Point):
                return obj in self.all_points
            if isinstance(obj, CoreScene.Vector):
                return obj.start in self.all_points and obj.end in self.all_points
            assert False, 'Operator not defined for %s and Line' % type(obj)

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
                existing = self.scene.get_intersection(self, obj)
                if existing:
                    return existing.with_extra_args(**kwargs)

                crossing = CoreScene.Point(
                    self.scene,
                    CoreScene.Point.Origin.line_x_line,
                    line0=self, line1=obj, **kwargs
                )

            crossing.belongs_to(self)
            crossing.belongs_to(obj)
            return crossing

        def perpendicular_constraint(self, other, **kwargs):
            """
            self ⟂ other
            """
            for cnstr in self.scene.constraints(Constraint.Kind.perpendicular):
                if set(cnstr.params) == set([self, other]):
                    cnstr.update(kwargs)
                    return
            self.scene.constraint(Constraint.Kind.perpendicular, self, other, **kwargs)

    class Circle(Object):
        def __init__(self, scene, **kwargs):
            CoreScene.Object.__init__(self, scene, **kwargs)
            self.all_points = []
            if self.centre == self.radius_start:
                self.all_points.append(self.radius_end)
            elif self.centre == self.radius_end:
                self.all_points.append(self.radius_start)

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

    class Vector:
        def __init__(self, start, end):
            assert isinstance(start, CoreScene.Point)
            assert isinstance(end, CoreScene.Point)
            assert start.scene == end.scene
            self.start = start
            self.end = end

        def angle(self, other):
            angle = CoreScene.Angle(self, other)
            self.non_zero_length_constraint(comment=_comment('%s is side of angle %s', self, angle))
            other.non_zero_length_constraint(comment=_comment('%s is side of angle %s', other, angle))
            return angle

        @property
        def scene(self):
            return self.start.scene

        @property
        def reversed(self):
            return CoreScene.Vector(self.end, self.start)

        def non_zero_length_constraint(self, **kwargs):
            """
            |self| > 0
            """
            self.start.not_equal_constraint(self.end, **kwargs)

        def length_constraint(self, length, **kwargs):
            """
            |self| == length
            """
            if length > 0:
                self.non_zero_length_constraint(**kwargs)
            #TODO: equal_constraint otherwise?
            self.scene.constraint(Constraint.Kind.distance, self, length, **kwargs)

        def length_ratio_constraint(self, vector, coef, **kwargs):
            """
            |self| == |vector| * coef
            coef is a non-zero number
            """
            assert isinstance(vector, CoreScene.Vector)
            assert self.scene == vector.scene
            assert coef != 0
            self.scene.constraint(Constraint.Kind.distances_ratio, self, vector, coef, **kwargs)

        def length_equal_constraint(self, vector, **kwargs):
            """
            |self| == |vector|
            """
            self.length_ratio_constraint(vector, 1, **kwargs)

        def __eq__(self, other):
            return self.start == other.start and self.end == other.end

        def __hash__(self):
            return hash(self.start) * 13 + hash(self.end) * 23

        def __str__(self):
            return str(_comment('%s %s', self.start, self.end))

    class Angle:
        def __init__(self, vector0, vector1):
            assert isinstance(vector0, CoreScene.Vector)
            assert isinstance(vector1, CoreScene.Vector)
            assert vector0.scene == vector1.scene
            self.vector0 = vector0
            self.vector1 = vector1
            self.vertex = self.vector0.start if self.vector0.start == self.vector1.start else None

        @property
        def scene(self):
            return self.vector0.scene

        @property
        def reversed(self):
            return CoreScene.Angle(self.vector1, self.vector0)

        def bisector_line(self, **kwargs):
            assert self.vertex is not None
            B = self.vector0.end
            C = self.vector1.end
            circle = self.vertex.circle_through(B, auxiliary=True)
            line = self.vertex.line_through(C, auxiliary=True)
            X = circle.intersection_point(line, auxiliary=True)
            self.vertex.same_direction_constraint(X, C)
            Y = X.ratio_point(B, 1, 1, auxiliary=True)
            bisector = self.vertex.line_through(Y, **kwargs)
            comment = _comment('%s is bisector of %s', bisector, self)
            Y.inside_angle_constraint(self, comment=comment)
            self.ratio_constraint(self.vertex.angle(B, Y), 2, guaranteed=True, comment=comment)
            self.ratio_constraint(self.vertex.angle(Y, C), 2, guaranteed=True, comment=comment)
            return bisector

        def ratio_constraint(self, angle, ratio, **kwargs):
            # self = angle * ratio
            self.scene.assert_angle(angle)
            self.scene.constraint(Constraint.Kind.angles_ratio, self, angle, ratio, **kwargs)

        def __eq__(self, other):
            #return self.vector0 == other.vector0 and self.vector1 == other.vector1
            # optimized version
            return \
                self.vector0.start == other.vector0.start and \
                self.vector0.end == other.vector0.end and \
                self.vector1.start == other.vector1.start and \
                self.vector1.end == other.vector1.end

        def __hash__(self):
            return hash(self.vector0) * 13 + hash(self.vector1) * 23

        def __str__(self):
            if self.vertex:
                return str(_comment('∠ %s %s %s', self.vector0.end, self.vertex, self.vector1.end))
            return '∠(%s, %s)' % (self.vector0, self.vector1)

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
        return cns

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

    def perpendicular_constraint(self, AB, CD, **kwargs):
        """
        AB ⟂ CD
        AB and CD are tuples or lists of two points
        """
        assert len(AB) == 2 and len(CD) == 2
        lineAB = AB[0].line_through(AB[1], auxiliary=True)
        lineCD = CD[0].line_through(CD[1], auxiliary=True)
        lineAB.perpendicular_constraint(lineCD, **kwargs)

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

    def assert_angle(self, obj):
        self.assert_type(obj, CoreScene.Angle)

    def free_point(self, **kwargs):
        return CoreScene.Point(self, origin=CoreScene.Point.Origin.free, **kwargs)

    def add(self, obj: Object):
        self.__objects.append(obj)

    def get(self, label: str):
        for obj in self.__objects:
            if obj.label == label or label in obj.extra_labels:
                return obj
        return None

    def get_line(self, point0, point1):
        """
        Returns *existing* line through point0 and point1.
        Does not require point0 != point1, returns first found line that meets the condition.
        """
        for line in self.lines():
            if point0 in line and point1 in line:
                return line
        return None

    def get_intersection(self, line0, line1):
        """
        Returns *existing* intersection point of line0 and line1.
        """
        try:
            return next(pt for pt in line0.all_points if pt in line1)
        except:
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
        collinear         = ('collinear', Stage.adjustment, CoreScene.Point, CoreScene.Point, CoreScene.Point)
        opposite_side     = ('opposite_side', Stage.validation, CoreScene.Point, CoreScene.Point, CoreScene.Line)
        same_side         = ('same_side', Stage.validation, CoreScene.Point, CoreScene.Point, CoreScene.Line)
        same_direction    = ('same_direction', Stage.validation, CoreScene.Point, CoreScene.Point, CoreScene.Point)
        quadrilateral     = ('quadrilateral', Stage.validation, CoreScene.Point, CoreScene.Point, CoreScene.Point, CoreScene.Point)
        convex_polygon    = ('convex_polygon', Stage.validation, List[CoreScene.Point])
        distance          = ('distance', Stage.adjustment, CoreScene.Vector, int)
        distances_ratio   = ('distances_ratio', Stage.adjustment, CoreScene.Vector, CoreScene.Vector, int)
        angles_ratio      = ('angles_ratio', Stage.adjustment, CoreScene.Angle, CoreScene.Angle, int)
        perpendicular     = ('perpendicular', Stage.adjustment, CoreScene.Line, CoreScene.Line)

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
                assert isinstance(arg, (list, tuple))
            # TODO: restore other parameters type check
            #else:
            #    assert isinstance(arg, knd)
            self.params.append(arg)
        self.kind = kind
        self.comments = []
        self.update(kwargs)

    def update(self, kwargs):
        if 'comment' in kwargs:
            #if kwargs['comment'] not in self.comments:
            if not self.comments:
                self.comments.append(kwargs['comment'])
            del kwargs['comment']
        self.__dict__.update(kwargs)

    def __str__(self):
        params = [para.label if isinstance(para, CoreScene.Object) else str(para) for para in self.params]
        extras = dict(self.__dict__)
        del extras['kind']
        del extras['params']
        del extras['comments']
        if self.comments:
            comments = ', '.join([str(com) for com in self.comments])
            return 'Constraint(%s) %s %s (%s)' % (self.kind.name, params, comments, extras)
        else:
            return 'Constraint(%s) %s (%s)' % (self.kind.name, params, extras)

class ParametrizedString:
    def __init__(self, format_string, *params):
        self.format_string = format_string
        self.params = params

    def __eq__(self, other):
        return isinstance(other, ParametrizedString) and self.format_string == other.format_string and self.params == other.params

    def __str__(self):
        return self.format_string % tuple(p.name if isinstance(p, CoreScene.Object) else p for p in self.params)

def _comment(*args):
    return ParametrizedString(*args)
