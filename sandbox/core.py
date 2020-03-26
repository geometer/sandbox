"""
Core module.
Normally, do not add new construction methods here, do this in scene.py instead.
"""

from enum import Enum, auto, unique
import itertools
import sympy as sp
from typing import List

from .property import AngleValueProperty, PointsCoincidenceProperty, PointsCollinearityProperty, LengthsRatioProperty, PointInsideAngleProperty, EquilateralTriangleProperty
from .reason import Reason
from .util import _comment, divide

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
            if self.scene.is_frozen:
                return self

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
            return self.name

        @property
        def description(self):
            dct = {}
            for key in self.__dict__:
                if key in ('label', 'scene') or key.startswith('_'):
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
            translated        = auto()
            perp              = auto()
            line              = auto()
            circle            = auto()
            line_x_line       = auto()
            circle_x_line     = auto()
            circle_x_circle   = auto()

        def __init__(self, scene, origin, **kwargs):
            assert isinstance(origin, CoreScene.Point.Origin), 'origin must be a Point.Origin, not %s' % type(origin)
            CoreScene.Object.__init__(self, scene, origin=origin, **kwargs)
            self.__vectors = {}

        def translated_point(self, vector, coef=1, **kwargs):
            self.scene.assert_vector(vector)
            if coef == 0:
                return self
            if coef == 1 and vector.start == self:
                return vector.end
            if coef == -1 and vector.end == self:
                return vector.start
            new_point = CoreScene.Point(
                self.scene,
                CoreScene.Point.Origin.translated,
                base=self, delta=vector, coef=coef, **kwargs
            )
            if self in {vector.start, vector.end}:
                new_point.collinear_constraint(vector.start, vector.end)
            if coef > 0:
                self.vector(new_point).parallel_constraint(vector, guaranteed=True)
            else:
                new_point.vector(self).parallel_constraint(vector, guaranteed=True)
            self.segment(new_point).ratio_constraint(vector.as_segment, sp.Abs(coef), guaranteed=True)
            return new_point

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
            new_point = self.translated_point(self.vector(point), divide(coef1, coef0 + coef1), **kwargs)
            new_point.collinear_constraint(self, point, guaranteed=True)
            self.segment(new_point).ratio_constraint(new_point.segment(point), divide(coef1, coef0), guaranteed=True)
            if coef0 > 0 and coef1 > 0 or coef0 < 0 and coef1 < 0:
                self.vector(point).parallel_constraint(self.vector(new_point), guaranteed=True)
                point.vector(self).parallel_constraint(point.vector(new_point), guaranteed=True)
            elif coef0 < 0:
                self.vector(point).parallel_constraint(self.vector(new_point), guaranteed=True)
                new_point.vector(self).parallel_constraint(new_point.vector(point), guaranteed=True)
            elif coef1 < 0:
                new_point.vector(self).parallel_constraint(new_point.vector(point), guaranteed=True)
                point.vector(self).parallel_constraint(point.vector(new_point), guaranteed=True)
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
            if self not in line:
                crossing = new_line.intersection_point(line, auxiliary=True)
                print('DEBUG %s' % crossing)
            line.perpendicular_constraint(new_line, guaranteed=True)
            return new_line

        def line_through(self, point, **kwargs):
            self.scene.assert_point(point)
            assert self != point, 'Cannot create a line by a single point'
            self.not_equal_constraint(point)

            for existing in self.scene.lines():
                if self in existing and point in existing:
                    return existing.with_extra_args(**kwargs)

            line = CoreScene.Line(self.scene, point0=self, point1=point, **kwargs)
            if not self.scene.is_frozen:
                for cnstr in self.scene.constraints(Constraint.Kind.collinear):
                    if len([pt for pt in line.all_points if pt in cnstr.params]) == 2:
                        for pt in cnstr.params:
                            if pt not in line.all_points:
                                line.all_points.append(pt)

            return line

        def circle_through(self, point, **kwargs):
            return self.circle_with_radius(self.segment(point), **kwargs)

        def circle_with_radius(self, radius, **kwargs):
            self.scene.assert_segment(radius)
            assert radius.points[0] != radius.points[1], 'Cannot create a circle of zero radius'
            return CoreScene.Circle(
                self.scene, centre=self, radius=radius, **kwargs
            )

        def vector(self, point):
            assert self != point, 'Cannot create vector from a single point'
            vec = self.__vectors.get(point)
            if vec is None:
                vec = CoreScene.Vector(self, point)
                self.__vectors[point] = vec
            return vec

        def segment(self, point):
            assert self != point, 'Cannot create segment from a single point'
            return self.scene._get_segment(self, point)

        def angle(self, point0, point1):
            assert point0 != point1, 'Angle endpoints should be different'
            return self.scene._get_angle(self.vector(point0), self.vector(point1))

        def belongs_to(self, line_or_circle):
            self.scene.assert_line_or_circle(line_or_circle)
            if not self.scene.is_frozen and self not in line_or_circle.all_points:
                line_or_circle.all_points.append(self)

        def not_equal_constraint(self, A, **kwargs):
            """
            The current point does not coincide with A.
            """
            if self.scene.is_frozen:
                return
            for cnstr in self.scene.constraints(Constraint.Kind.not_equal):
                if set(cnstr.params) == {self, A}:
                    cnstr.update(kwargs)
                    return
            self.scene.constraint(Constraint.Kind.not_equal, self, A, **kwargs)

        def not_collinear_constraint(self, A, B, **kwargs):
            """
            The current point is not collinear with A and B.
            """
            for cnstr in self.scene.constraints(Constraint.Kind.not_collinear):
                if set(cnstr.params) == {self, A, B}:
                    cnstr.update(kwargs)
                    return
            self.scene.constraint(Constraint.Kind.not_collinear, self, A, B, **kwargs)

        def collinear_constraint(self, A, B, **kwargs):
            """
            The current point is collinear with A and B.
            """
            cnstr = self.scene.constraint(Constraint.Kind.collinear, self, A, B, **kwargs)
            if not self.scene.is_frozen:
                for line in self.scene.lines():
                    if len([pt for pt in line.all_points if pt in cnstr.params]) == 2:
                        for pt in cnstr.params:
                            if pt not in line.all_points:
                                line.all_points.append(pt)
            return cnstr

        def distance_constraint(self, A, distance, **kwargs):
            """
            Distance to the point A equals to the given distance.
            The given distance must be a non-negative number
            """
            if isinstance(A, str):
                A = self.scene.get(A)
            return self.segment(A).length_constraint(distance, **kwargs)

        def opposite_side_constraint(self, point, line, **kwargs):
            """
            The current point lies on the opposite side to the line than the given point.
            """
            if isinstance(point, CoreScene.Line) and isinstance(line, CoreScene.Point):
                point, line = line, point
            for cnstr in self.scene.constraints(Constraint.Kind.opposite_side):
                if line == cnstr.params[2] and set(cnstr.params[0:2]) == {self, point}:
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
                if line == cnstr.params[2] and set(cnstr.params[0:2]) == {self, point}:
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
                if self == cnstr.params[0] and set(cnstr.params[1:3]) == {A, B}:
                    cnstr.update(kwargs)
                    return
            self.not_equal_constraint(A)
            self.not_equal_constraint(B)
            A.belongs_to(self.line_through(B, auxiliary=True))
            self.scene.constraint(Constraint.Kind.same_direction, self, A, B, **kwargs)

        def inside_constraint(self, obj, **kwargs):
            """
            The point is inside the object (angle or segment)
            """
            if isinstance(obj, CoreScene.Segment):
                self.scene.constraint(Constraint.Kind.inside_segment, self, obj, **kwargs)
            elif isinstance(obj, CoreScene.Angle) and obj.vertex:
                self.scene.constraint(Constraint.Kind.inside_angle, self, obj, **kwargs)
            else:
                assert False, 'Cannot declare point lying inside %s' % obj

        def inside_triangle_constraint(self, A, B, C, **kwargs):
            """
            The point is inside the △ ABC
            """
            A.not_collinear_constraint(B, C)
            if 'comment' not in kwargs:
                kwargs = dict(kwargs)
                kwargs['comment'] = _comment(
                    'Point %s is inside △ %s %s %s', self, A, B, C
                )
            self.inside_constraint(A.angle(B, C), **kwargs)
            self.inside_constraint(B.angle(A, C), **kwargs)
            self.inside_constraint(C.angle(B, A), **kwargs)

    class Line(Object):
        def __init__(self, scene, **kwargs):
            CoreScene.Object.__init__(self, scene, **kwargs)
            self.all_points = [self.point0, self.point1]
            self.__key = frozenset(self.all_points)

        @property
        def name(self):
            if hasattr(self, 'auto_label') and self.auto_label:
                for points in itertools.combinations(self.all_points, 2):
                    if not points[0].auxiliary and not points[1].auxiliary:
                        return '(%s %s)' % (points[0].name, points[1].name)

            return super().name

        def __eq__(self, other):
            return isinstance(other, CoreScene.Line) and self.__key == other.__key

        def __hash__(self):
            return hash(self.__key)

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
                existing = next((pt for pt in self.all_points if pt in obj), None)
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
                if set(cnstr.params) == {self, other}:
                    cnstr.update(kwargs)
                    return
            self.scene.constraint(Constraint.Kind.perpendicular, self, other, **kwargs)

        def __contains__(self, obj):
            if obj is None:
                return False
            if isinstance(obj, CoreScene.Point):
                return obj in self.all_points
            if isinstance(obj, CoreScene.Vector):
                return obj.start in self.all_points and obj.end in self.all_points
            assert False, 'Operator not defined for %s and Line' % type(obj)

    class Circle(Object):
        def __init__(self, scene, **kwargs):
            CoreScene.Object.__init__(self, scene, **kwargs)
            self.all_points = []
            if not scene.is_frozen:
                if self.centre == self.radius.points[0]:
                    self.all_points.append(self.radius.points[1])
                elif self.centre == self.radius.points[1]:
                    self.all_points.append(self.radius.points[0])

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

        def __contains__(self, obj):
            if obj is None:
                return False
            if isinstance(obj, CoreScene.Point):
                return obj in self.all_points
            assert False, 'Operator not defined for %s and Circle' % type(obj)

    class Vector:
        def __init__(self, start, end):
            assert isinstance(start, CoreScene.Point)
            assert isinstance(end, CoreScene.Point)
            assert start.scene == end.scene
            self.start = start
            self.end = end
            self.points = (start, end)
            self.__segment = None

        @property
        def as_segment(self):
            if self.__segment is None:
                self.__segment = self.start.segment(self.end)
            return self.__segment

        def angle(self, other):
            angle = self.scene._get_angle(self, other)
            if not self.scene.is_frozen:
                self.as_segment.non_zero_length_constraint(comment=_comment('%s is side of %s', self, angle))
                other.as_segment.non_zero_length_constraint(comment=_comment('%s is side of %s', other, angle))
            return angle

        @property
        def scene(self):
            return self.start.scene

        @property
        def reversed(self):
            return self.end.vector(self.start)

        def parallel_constraint(self, vector, **kwargs):
            """
            Self and vector have the same direction.
            This constraint also fulfilled if at least one of the vectors has zero length.
            """
            assert isinstance(vector, CoreScene.Vector)
            assert self.scene == vector.scene
            return self.scene.constraint(Constraint.Kind.parallel_vectors, self, vector, **kwargs)

        def __str__(self):
            return str(_comment('%s %s', self.start, self.end))

    def _get_segment(self, point0, point1):
        assert isinstance(point0, CoreScene.Point)
        assert isinstance(point1, CoreScene.Point)
        assert point0.scene == self
        assert point1.scene == self
        key = frozenset([point0, point1])
        #key = (point0, point1)
        segment = self.__segments.get(key)
        if segment is None:
            segment = CoreScene.Segment(point0, point1)
            self.__segments[key] = segment
        return segment

    class Segment:
        def __init__(self, pt0, pt1):
            self.points = (pt0, pt1)
            self.point_set = frozenset(self.points)

        @property
        def scene(self):
            return self.points[0].scene

        def free_point(self, **kwargs):
            point = self.points[0].line_through(self.points[1], auxiliary=True).free_point(**kwargs)
            point.inside_constraint(self)
            return point

        def ratio_constraint(self, segment, coef, **kwargs):
            """
            |self| == |segment| * coef
            coef is a non-zero number
            """
            assert isinstance(segment, CoreScene.Segment)
            assert self.scene == segment.scene
            assert coef != 0
            args = dict(kwargs)
            comment = args.get('comment')
            if not comment:
                if coef == 1:
                    comment = _comment('Given: |%s| == |%s|', self, segment)
                else:
                    comment = _comment('Given: |%s| == %s |%s|', self, coef, segment)
                args['comment'] = comment
            return self.scene.constraint(Constraint.Kind.length_ratio, self, segment, coef, **args)

        def congruent_constraint(self, segment, **kwargs):
            """
            |self| == |vector|
            """
            self.ratio_constraint(segment, 1, **kwargs)

        def non_zero_length_constraint(self, **kwargs):
            """
            |self| > 0
            """
            self.points[0].not_equal_constraint(self.points[1], **kwargs)

        def length_constraint(self, length, **kwargs):
            """
            |self| == length
            """
            if length > 0:
                self.non_zero_length_constraint(**kwargs)
            #TODO: equal_constraint otherwise?
            self.scene.constraint(Constraint.Kind.distance, self, length, **kwargs)

        def __str__(self):
            return str(_comment('%s %s', *self.points))

    def _get_angle(self, vector0, vector1):
        assert isinstance(vector0, CoreScene.Vector)
        assert isinstance(vector1, CoreScene.Vector)
        assert vector0.scene == self
        assert vector1.scene == self

        key = frozenset([vector0, vector1])
        angle = self.__angles.get(key)
        if angle is None:
            angle = CoreScene.Angle(vector0, vector1)
            self.__angles[key] = angle
            if vector0.start != vector1.start:
                assert vector0.end != vector1.end
                self.__angles[frozenset([vector0.reversed, vector1.reversed])] = angle
        return angle

    class Angle:
        def __init__(self, vector0, vector1):
            self.vector0 = vector0
            self.vector1 = vector1
            self.vertex = self.vector0.start if self.vector0.start == self.vector1.start else None
            self.points = frozenset([*vector0.points, *vector1.points])

        @property
        def scene(self):
            return self.vector0.scene

        @property
        def endpoints(self):
            assert self.vertex, 'Cannot locate endpoints of angle with no vertex'
            return (self.vector0.end, self.vector1.end)

        def bisector_line(self, **kwargs):
            assert self.vertex, 'Cannot construct bisector of angle %s with no vertex' % self
            B = self.vector0.end
            C = self.vector1.end
            circle = self.vertex.circle_through(B, auxiliary=True)
            line = self.vertex.line_through(C, auxiliary=True)
            X = circle.intersection_point(line, auxiliary=True)
            self.vertex.same_direction_constraint(X, C)
            Y = X.translated_point(self.vector0, auxiliary=True)
            bisector = self.vertex.line_through(Y, **kwargs)
            comment = _comment('[%s %s) is the bisector of %s', self.vertex, Y, self)
            Y.inside_constraint(self, comment=comment)
            self.ratio_constraint(self.vertex.angle(B, Y), 2, guaranteed=True, comment=comment)
            self.ratio_constraint(self.vertex.angle(Y, C), 2, guaranteed=True, comment=comment)
            return bisector

        def ratio_constraint(self, angle, ratio, **kwargs):
            # self = angle * ratio
            self.scene.assert_angle(angle)
            self.scene.constraint(Constraint.Kind.angles_ratio, self, angle, ratio, **kwargs)

        def __str__(self):
            if self.vertex:
                return str(_comment('∠ %s %s %s', self.vector0.end, self.vertex, self.vector1.end))
            return '∠(%s, %s)' % (self.vector0, self.vector1)

    def __init__(self):
        self.__objects = []
        self.validation_constraints = []
        self.adjustment_constraints = []
        self.__frozen = False
        self.__angles = {} # {vector, vector} => angle
        self.__segments = {} # {point, point} => angle

    def constraint(self, kind, *args, **kwargs):
        cns = Constraint(kind, self, *args, **kwargs)
        if not self.__frozen:
            if kind.stage == Stage.validation:
                self.validation_constraints.append(cns)
            else:
                self.adjustment_constraints.append(cns)
        return cns

    def equilateral_constraint(self, triangle, **kwargs):
        self.triangle_constraint(triangle, **kwargs)
        self.constraint(Constraint.Kind.equilateral, *triangle, **kwargs)

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
        AB[0].not_equal_constraint(AB[1], **kwargs)
        CD[0].not_equal_constraint(CD[1], **kwargs)
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

    def circles(self, skip_auxiliary=False):
        if skip_auxiliary:
            return [c for c in self.__objects if isinstance(c, CoreScene.Circle) and not c.auxiliary]
        else:
            return [c for c in self.__objects if isinstance(c, CoreScene.Circle)]

    def constraints(self, kind):
        if kind.stage == Stage.validation:
            return [cnstr for cnstr in self.validation_constraints if cnstr.kind == kind]
        else:
            return [cnstr for cnstr in self.adjustment_constraints if cnstr.kind == kind]

    def enumerate_predefined_properties(self):
        for cnstr in self.constraints(Constraint.Kind.collinear):
            yield (PointsCollinearityProperty(*cnstr.params, True), cnstr.comments)

        for cnstr in self.constraints(Constraint.Kind.not_collinear):
            if any(param.auxiliary for param in cnstr.params):
                continue
            yield (PointsCollinearityProperty(*cnstr.params, False), cnstr.comments)
            yield (PointsCoincidenceProperty(*cnstr.params[0:2], False), cnstr.comments)
            yield (PointsCoincidenceProperty(*cnstr.params[1:3], False), cnstr.comments)
            yield (PointsCoincidenceProperty(cnstr.params[0], cnstr.params[2], False), cnstr.comments)

        for cnstr in self.constraints(Constraint.Kind.not_equal):
            if cnstr.params[0].auxiliary or cnstr.params[1].auxiliary:
                continue
            yield (PointsCoincidenceProperty(cnstr.params[0], cnstr.params[1], False), cnstr.comments)

        for cnstr in self.constraints(Constraint.Kind.length_ratio):
            if any(param.auxiliary for param in [*cnstr.params[0].points, *cnstr.params[1].points]):
                continue
            yield (
                LengthsRatioProperty(cnstr.params[0], cnstr.params[1], cnstr.params[2]),
                cnstr.comments
            )

        for cnstr in self.constraints(Constraint.Kind.same_direction):
            #TODO: filter aux points
            yield (
                AngleValueProperty(cnstr.params[0].angle(*cnstr.params[1:]), 0),
                cnstr.comments
            )

        for cnstr in self.constraints(Constraint.Kind.perpendicular):
            line0 = cnstr.params[0]
            line1 = cnstr.params[1]
            vector0 = line0.point0.vector(line0.point1)
            vector1 = line1.point0.vector(line1.point1)
            yield (
                AngleValueProperty(vector0.angle(vector1), 90),
                cnstr.comments
            )

        for cnstr in self.constraints(Constraint.Kind.inside_angle):
            point = cnstr.params[0]
            angle = cnstr.params[1]
            yield (
                PointInsideAngleProperty(point, angle),
                cnstr.comments
            )

        for cnstr in self.constraints(Constraint.Kind.inside_segment):
            #TODO: filter aux points
            yield (
                PointsCoincidenceProperty(*cnstr.params[1].points, False),
                cnstr.comments
            )
            yield (
                AngleValueProperty(cnstr.params[0].angle(*cnstr.params[1].points), 180),
                cnstr.comments
            )

        for cnstr in self.constraints(Constraint.Kind.equilateral):
            yield (
                EquilateralTriangleProperty(cnstr.params),
                cnstr.comments
            )

        for line in self.lines(skip_auxiliary=False):
            for pt0, pt1, pt2 in itertools.combinations([p for p in line.all_points], 3):
                yield (
                    PointsCollinearityProperty(pt0, pt1, pt2, True),
                    [_comment('Three points on the line %s', line)]
                )

        for circle in self.circles(skip_auxiliary=True):
            radiuses = [circle.centre.segment(pt) for pt in circle.all_points]
            if circle.centre not in circle.radius.points:
                for rad in radiuses:
                    yield (
                        LengthsRatioProperty(rad, circle.radius, 1),
                        [_comment('Distance between centre %s and point %s on the circle of radius |%s|', circle.centre, rad.points[0], circle.radius)]
                    )
            for rad0, rad1 in itertools.combinations(radiuses, 2):
                yield (
                    LengthsRatioProperty(rad0, rad1, 1),
                    [_comment('Two radiuses of the same circle with centre %s', circle.centre)]
                )

    def assert_type(self, obj, *args):
        assert isinstance(obj, args), 'Unexpected type %s' % type(obj)
        assert obj.scene == self

    def assert_point(self, obj):
        self.assert_type(obj, CoreScene.Point)

    def assert_line(self, obj):
        self.assert_type(obj, CoreScene.Line)

    def assert_line_or_circle(self, obj):
        self.assert_type(obj, CoreScene.Line, CoreScene.Circle)

    def assert_vector(self, obj):
        self.assert_type(obj, CoreScene.Vector)

    def assert_segment(self, obj):
        self.assert_type(obj, CoreScene.Segment)

    def assert_angle(self, obj):
        self.assert_type(obj, CoreScene.Angle)

    def free_point(self, **kwargs):
        return CoreScene.Point(self, origin=CoreScene.Point.Origin.free, **kwargs)

    def add(self, obj: Object):
        if not self.__frozen:
            self.__objects.append(obj)

    def get(self, label: str):
        for obj in self.__objects:
            if obj.label == label or label in obj.extra_labels:
                return obj
        return None

    def freeze(self):
        self.__frozen = True

    def unfreeze(self):
        self.__frozen = False

    @property
    def is_frozen(self):
        return self.__frozen

    def dump(self):
        print('Objects:')
        print('\n'.join(['\t' + obj.description for obj in self.__objects]))
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
        inside_segment    = ('inside_segment', Stage.validation, CoreScene.Point, CoreScene.Segment)
        inside_angle      = ('inside_angle', Stage.validation, CoreScene.Point, CoreScene.Angle)
        quadrilateral     = ('quadrilateral', Stage.validation, CoreScene.Point, CoreScene.Point, CoreScene.Point, CoreScene.Point)
        equilateral       = ('equilateral', Stage.adjustment, CoreScene.Point, CoreScene.Point, CoreScene.Point)
        convex_polygon    = ('convex_polygon', Stage.validation, List[CoreScene.Point])
        distance          = ('distance', Stage.adjustment, CoreScene.Vector, int)
        length_ratio      = ('length_ratio', Stage.adjustment, CoreScene.Segment, CoreScene.Segment, int)
        parallel_vectors  = ('parallel_vectors', Stage.adjustment, CoreScene.Vector, CoreScene.Vector)
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
