"""
Core module.
Normally, do not add new construction methods here, do this in scene.py instead.
"""

from enum import Enum, auto, unique
import itertools
import re
import sympy as sp
from typing import List

from .figure import Figure
from .reason import Reason
from .util import LazyComment, Comment, divide

class CoreScene:
    layers = ('user', 'auxiliary', 'invisible')

    @staticmethod
    def layers_by(max_layer):
        return CoreScene.layers[0:CoreScene.layers.index(max_layer) + 1]

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
                pattern = self.__class__.prefix + '%d'
                for index in itertools.count():
                    label = pattern % index
                    if scene.get(label) is None:
                        self.label = label
                        self.auto_label = True
                        break
            self.layer = kwargs.get('layer', 'user')
            assert self.layer in CoreScene.layers

            self.extra_labels = set()
            self.scene = scene
            self.__dict__.update(kwargs)
            scene.add(self)

        def with_extra_args(self, **kwargs):
            if self.scene.is_frozen:
                return self

            layer = kwargs.get('layer', 'user')
            if self.layer not in CoreScene.layers_by(layer):
                self.layer = layer
            for key in kwargs:
                if key == 'layer':
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
            for key in ('layer', 'extra_labels', 'all_points', 'comment'):
                value = self.__dict__.get(key)
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
            if self.name == self.label:
                return '%s %s %s' % (self.__class__.__name__, self, dct)
            else:
                return '%s %s %s %s' % (self.__class__.__name__, self.label, self.name, dct)

    class Point(Object, Figure):
        prefix = 'Pt_'

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
            self.__perpendiculars = {}

        def translated_point(self, vector, coef=1, **kwargs):
            self.scene.assert_vector(vector)
            if coef == 0:
                return self
            if coef == 1 and vector.start == self:
                return vector.end
            if coef == -1 and vector.end == self:
                return vector.start
            for pt in self.scene.points():
                if pt.origin == CoreScene.Point.Origin.translated and pt.base == self and pt.delta == vector and pt.coef == coef:
                    return pt
            if 'comment' not in kwargs:
                kwargs = dict(kwargs)
                if coef == 1:
                    pattern = 'translation of $%{point:pt}$ by vector $%{vector:vector}$'
                else:
                    pattern = 'translation of $%{point:pt}$ by vector $%{multiplier:coef} %{vector:vector}$'
                kwargs['comment'] = Comment(
                    pattern,
                    {'pt': self, 'coef': coef, 'vector': vector}
                )
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

        def symmetric_point(self, centre, **kwargs):
            symmetric = CoreScene.Point(
                self.scene, CoreScene.Point.Origin.translated,
                base=centre, delta=self.vector(centre), coef=1, **kwargs
            )
            symmetric.collinear_constraint(self, centre, guaranteed=True)
            from .property import MiddleOfSegmentProperty
            self.scene.add_property(MiddleOfSegmentProperty(centre, self.segment(symmetric)))
            return symmetric

        def perpendicular_line(self, line, **kwargs):
            """
            Constructs a line through the point, perpendicular to the given line.
            """
            self.scene.assert_line(line)
            existing = self.__perpendiculars.get(line)
            if existing:
                return existing.with_extra_args(**kwargs)

            new_point = CoreScene.Point(
                self.scene,
                CoreScene.Point.Origin.perp,
                point=self, line=line,
                layer='invisible'
            )
            if 'comment' not in kwargs:
                kwargs = dict(kwargs)
                kwargs['comment'] = LazyComment('perpendicular from %s to %s', self, line.label)
            new_line = self.line_through(new_point, **kwargs)
            if self not in line:
                crossing = new_line.intersection_point(line, layer='auxiliary', comment=LazyComment('foot of the perpendicular from %s to %s', self, line.label))
            line.perpendicular_constraint(new_line, guaranteed=True)
            self.__perpendiculars[line] = new_line
            return new_line

        def line_through(self, point, **kwargs):
            self.scene.assert_point(point)
            assert self != point, 'Cannot create a line by a single point'
            self.not_equal_constraint(point)

            for existing in self.scene.lines():
                if self in existing and point in existing:
                    return existing.with_extra_args(**kwargs)

            if 'comment' not in kwargs:
                kwargs = dict(kwargs)
                kwargs['comment'] = Comment(
                    'Line through $%{point:pt0}$ and $%{point:pt1}$',
                    {'pt0': self, 'pt1': point}
                )
            line = CoreScene.Line(self.scene, point0=self, point1=point, **kwargs)
            if not self.scene.is_frozen:
                for cnstr in self.scene.constraints(Constraint.Kind.collinear):
                    if len([pt for pt in line.all_points if pt in cnstr.params]) == 2:
                        for pt in cnstr.params:
                            if pt not in line.all_points:
                                line.all_points.append(pt)

            return line

        def circle_through(self, point, **kwargs):
            if 'comment' not in kwargs:
                kwargs = dict(kwargs)
                kwargs['comment'] = Comment(
                    'Circle with centre $%{point:centre}$ through $%{point:pt}$',
                    {'centre': self, 'pt': point}
                )
            return self.circle_with_radius(self.segment(point), **kwargs)

        def circle_with_radius(self, radius, **kwargs):
            self.scene.assert_segment(radius)
            assert radius.points[0] != radius.points[1], 'Cannot create a circle of zero radius'
            if 'comment' not in kwargs:
                kwargs = dict(kwargs)
                kwargs['comment'] = Comment(
                    'Circle with centre $%{point:centre}$ with radius $%{segment:radius}$',
                    {'centre': self, 'radius': radius}
                )
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
            self.not_equal_constraint(A, guaranteed=True, **kwargs)
            self.not_equal_constraint(B, guaranteed=True, **kwargs)
            A.not_equal_constraint(B, guaranteed=True, **kwargs)

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
            #self.not_collinear_constraint(line.point0, line.point1, **kwargs)
            #point.not_collinear_constraint(line.point0, line.point1, **kwargs)
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
            A.belongs_to(self.line_through(B, layer='auxiliary'))
            self.scene.constraint(Constraint.Kind.same_direction, self, A, B, **kwargs)

        def inside_constraint(self, obj, **kwargs):
            """
            The point is inside the object (angle or segment)
            """
            if isinstance(obj, CoreScene.Segment):
                self.collinear_constraint(*obj.points, **kwargs)
                self.scene.constraint(Constraint.Kind.inside_segment, self, obj, **kwargs)
            elif isinstance(obj, CoreScene.Angle) and obj.vertex:
                self.scene.constraint(Constraint.Kind.inside_angle, self, obj, **kwargs)
            else:
                assert False, 'Cannot declare point lying inside %s' % obj

        def inside_triangle_constraint(self, triangle, **kwargs):
            """
            The point is inside the triangle
            """
            triangle.points[0].not_collinear_constraint(*triangle.points[1:])
            if 'comment' not in kwargs:
                kwargs = dict(kwargs)
                kwargs['comment'] = Comment(
                    'point $%{point:pt}$ is inside $%{triangle:triangle}$',
                    {'pt': self, 'triangle': triangle}
                )
            for angle in triangle.angles:
                self.inside_constraint(angle, **kwargs)
            from .property import SameOrOppositeSideProperty
            for vertex, side in zip(triangle.points, triangle.sides):
                self.scene.add_property(SameOrOppositeSideProperty(side, vertex, self, True))

    class Line(Object):
        prefix = 'Ln_'

        def __init__(self, scene, **kwargs):
            CoreScene.Object.__init__(self, scene, **kwargs)
            self.all_points = [self.point0, self.point1]

        @property
        def name(self):
            if hasattr(self, 'auto_label') and self.auto_label:
                for points in itertools.combinations(self.all_points, 2):
                    if points[0].layer == 'user' and points[1].layer == 'user':
                        return '(%s %s)' % (points[0].name, points[1].name)

            return super().name

        def free_point(self, **kwargs):
            if 'comment' not in kwargs:
                kwargs = dict(kwargs)
                kwargs['comment'] = LazyComment('point on line %s', self.label)
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
            if 'comment' not in kwargs:
                kwargs = dict(kwargs)
                kwargs['comment'] = LazyComment('crossing point of %s and %s', self.label, obj.label)
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
            self.point0.segment(self.point1).perpendicular_constraint(other.point0.segment(other.point1), **kwargs)

        def __contains__(self, obj):
            if obj is None:
                return False
            if isinstance(obj, CoreScene.Point):
                return obj in self.all_points
            if isinstance(obj, CoreScene.Vector):
                return obj.start in self.all_points and obj.end in self.all_points
            assert False, 'Operator not defined for %s and Line' % type(obj)

    class Circle(Object):
        prefix = 'Circ_'

        def __init__(self, scene, **kwargs):
            CoreScene.Object.__init__(self, scene, **kwargs)
            self.all_points = []
            if not scene.is_frozen:
                if self.centre == self.radius.points[0]:
                    self.all_points.append(self.radius.points[1])
                elif self.centre == self.radius.points[1]:
                    self.all_points.append(self.radius.points[0])

        def centre_point(self, **kwargs):
            return self.centre.with_extra_args(**kwargs)

        def free_point(self, **kwargs):
            if 'comment' not in kwargs:
                kwargs = dict(kwargs)
                kwargs['comment'] = LazyComment('point on circle %s', self.label)
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
            if 'comment' not in kwargs:
                kwargs = dict(kwargs)
                kwargs['comment'] = LazyComment('crossing point of %s and %s', self.label, obj.label)
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

    class Vector(Figure):
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
                for vec in (self, other):
                    for cnstr in vec.scene.constraints(Constraint.Kind.not_equal):
                        if set(cnstr.params) == set(vec.points):
                            break
                    else:
                        vec.as_segment.non_zero_length_constraint(comment=Comment(
                            '$%{vector:side}$ is side of $%{angle:angle}$',
                            {'side': vec, 'angle': angle}
                        ))
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
            return '%s %s' % (self.start, self.end)

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

    class Segment(Figure):
        def __init__(self, pt0, pt1):
            self.points = (pt0, pt1)
            self.point_set = frozenset(self.points)
            self.__middle_point = None

        @property
        def scene(self):
            return self.points[0].scene

        def middle_point(self, **kwargs):
            """
            Constructs middle point of the segment
            """
            if self.__middle_point:
                return self.__middle_point.with_extra_args(**kwargs)

            delta = self.points[0].vector(self.points[1])
            coef = divide(1, 2)
            for pt in self.scene.points():
                if pt.origin == CoreScene.Point.Origin.translated:
                    if pt.base == self.points[0] and pt.delta == delta and pt.coef == coef:
                        middle = pt
                        break
                    if pt.base == self.points[1] and pt.delta == delta.reversed and pt.coef == coef:
                        middle = pt
                        break
            else:
                middle = CoreScene.Point(
                    self.scene, CoreScene.Point.Origin.translated,
                    base=self.points[0], delta=delta, coef=coef, **kwargs
                )
            from .property import MiddleOfSegmentProperty
            self.scene.add_property(MiddleOfSegmentProperty(middle, self))
            self.__middle_point = middle
            return middle

        def free_point(self, **kwargs):
            if 'comment' not in kwargs:
                kwargs = dict(kwargs)
                kwargs['comment'] = LazyComment('point on segment %s', self)
            point = self.line_through(layer='auxiliary').free_point(**kwargs)
            point.inside_constraint(self)
            return point

        def line_through(self, **kwargs):
            return self.points[0].line_through(self.points[1], **kwargs)

        def perpendicular_bisector_line(self, **kwargs):
            """
            Perpendicular bisector
            """
            middle = self.middle_point(layer='auxiliary')
            line = self.line_through(layer='auxiliary')
            if kwargs.get('comment') is None:
                kwargs = dict(kwargs)
                kwargs['comment'] = LazyComment('perpendicular bisector of %s', self)
            bisector = middle.perpendicular_line(line, **kwargs)
            comment=LazyComment('%s is the perpendicular bisector of %s', bisector, self)
            bisector.perpendicular_constraint(line, comment=comment)
            return bisector

        def perpendicular_constraint(self, other, **kwargs):
            """
            self ⟂ other
            """
            for cnstr in self.scene.constraints(Constraint.Kind.perpendicular):
                if set(cnstr.params) == {self, other}:
                    cnstr.update(kwargs)
                    return
            self.scene.constraint(Constraint.Kind.perpendicular, self, other, **kwargs)

        def ratio_constraint(self, segment, coef, **kwargs):
            """
            |self| == |segment| * coef
            coef is a non-zero number
            """
            assert isinstance(segment, CoreScene.Segment)
            assert self.scene == segment.scene
            assert coef != 0
            for cnstr in self.scene.constraints(Constraint.Kind.length_ratio):
                if set(cnstr.params) == {self, segment, coef}:
                    cnstr.update(kwargs)
                    return
            comment = kwargs.get('comment')
            if not comment:
                kwargs = dict(kwargs)
                if coef == 1:
                    pattern = '$|%{segment:seg0}| = |%{segment:seg1}|$'
                else:
                    pattern = '$|%{segment:seg0}| = %{multiplier:coef} |%{segment:seg1}|$'
                kwargs['comment'] = Comment(
                    pattern, {'seg0': self, 'seg1': segment, 'coef': coef}
                )
            return self.scene.constraint(Constraint.Kind.length_ratio, self, segment, coef, **kwargs)

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
            return '%s %s' % self.points

    def _get_angle(self, vector0, vector1):
        assert isinstance(vector0, CoreScene.Vector)
        assert isinstance(vector1, CoreScene.Vector)
        assert vector0.scene == self
        assert vector1.scene == self

        key = frozenset([vector0, vector1])
        angle = self.__angles.get(key)
        if angle is None:
            angle = CoreScene.Angle(vector0, vector1)
            if angle.vertex is None and angle.pseudo_vertex:
                if angle.vectors[0].end == angle.vectors[1].start:
                    from .property import SumOfTwoAnglesProperty
                    #TODO add comment
                    self.add_property(SumOfTwoAnglesProperty(
                        angle, angle.vectors[0].reversed.angle(angle.vectors[1]), 180
                    ))
                elif angle.vectors[0].start == angle.vectors[1].end:
                    from .property import SumOfTwoAnglesProperty
                    #TODO add comment
                    self.add_property(SumOfTwoAnglesProperty(
                        angle, angle.vectors[0].angle(angle.vectors[1].reversed), 180
                    ))
                elif angle.vectors[0].end == angle.vectors[1].end:
                    #TODO vertical angles
                    pass
            self.__angles[key] = angle
        return angle

    class Angle(Figure):
        def __init__(self, vector0, vector1):
            assert vector0 != vector1 and vector0 != vector1.reversed
            self.vectors = (vector0, vector1)
            self.vertex = vector0.start if vector0.start == vector1.start else None
            if self.vertex:
                self.pseudo_vertex = self.vertex
            else:
                self.pseudo_vertex = next((p for p in vector0.points if p in vector1.points), None)
            self.point_set = frozenset([*vector0.points, *vector1.points])
            self.__bisector = None

        @property
        def scene(self):
            return self.vectors[0].scene

        @property
        def endpoints(self):
            assert self.vertex, 'Cannot locate endpoints of angle with no vertex'
            return (self.vectors[0].end, self.vectors[1].end)

        def bisector_line(self, **kwargs):
            assert self.pseudo_vertex, 'Cannot construct bisector of angle %s with no vertex' % self
            if self.__bisector:
                return self.__bisector.with_extra_args(**kwargs)
            v = self.pseudo_vertex
            vec0 = self.vectors[0]
            e0 = vec0.end if v == vec0.start else v.translated_point(vec0, layer='invisible')
            vec1 = self.vectors[1]
            e1 = vec1.end if v == vec1.start else v.translated_point(vec1, layer='invisible')
            circle = v.circle_through(e0, layer='invisible')
            line = v.line_through(e1, layer='invisible')
            X = circle.intersection_point(line, layer='invisible')
            v.same_direction_constraint(X, e1)
            Y = X.translated_point(v.vector(e0), layer='invisible')
            self.point_on_bisector_constraint(Y, guaranteed=True)
            if kwargs.get('comment') is None:
                kwargs = dict(kwargs)
                kwargs['comment'] = LazyComment('bisector of %s', self)
            self.__bisector = v.line_through(Y, **kwargs)
            return self.__bisector

        def point_on_bisector_constraint(self, point, **kwargs):
            bisector = self.pseudo_vertex.vector(point)
            if kwargs.get('comment') is None:
                kwargs = dict(kwargs)
                kwargs['comment'] = Comment(
                    '$%{ray:bisector}$ is the bisector of $%{angle:angle}$',
                    {'bisector': bisector, 'angle': self}
                )
            angle0 = self.vectors[0].angle(bisector)
            angle1 = self.vectors[1].angle(bisector)
            if self.vertex:
                point.inside_constraint(self, **kwargs)
            self.ratio_constraint(angle0, 2, **kwargs)
            self.ratio_constraint(angle1, 2, **kwargs)
            angle0.ratio_constraint(angle1, 1, **kwargs)

        def ratio_constraint(self, angle, ratio, **kwargs):
            # self = angle * ratio
            self.scene.assert_angle(angle)
            self.scene.constraint(Constraint.Kind.angles_ratio, self, angle, ratio, **kwargs)

        def value_constraint(self, degree, **kwargs):
            if kwargs.get('comment') is None:
                kwargs = dict(kwargs)
                kwargs['comment'] = Comment(
                    '$%{anglemeasure:angle} = %{degree:degree}$',
                    {'angle': self, 'degree': degree}
                )
            self.scene.constraint(Constraint.Kind.angle_value, self, degree, **kwargs)

        def is_acute_constraint(self, **kwargs):
            self.scene.constraint(Constraint.Kind.acute_angle, self, **kwargs)

        def is_obtuse_constraint(self, **kwargs):
            self.scene.constraint(Constraint.Kind.obtuse_angle, self, **kwargs)

        def is_right_constraint(self, **kwargs):
            self.vectors[0].as_segment.line_through().perpendicular_constraint(
                self.vectors[1].as_segment.line_through(),
                **kwargs
            )

        def __str__(self):
            if self.vertex:
                return '\\angle %s %s %s' % (self.vectors[0].end, self.vertex, self.vectors[1].end)
            return '\\angle(%s, %s)' % self.vectors

    class Triangle(Figure):
        def __init__(self, pt0, pt1, pt2):
            self.points = (pt0, pt1, pt2)
            self.__sides = None
            self.__angles = None
            self.__permutations = None

        @property
        def scene(self):
            return self.points[0].scene

        @property
        def is_equilateral(self):
            for cnstr in self.scene.constraints(Constraint.Kind.equilateral):
                if set(cnstr.params[0].points) == set(self.points):
                    return True
            # TODO: check implicit equilateral constraints, e.g. congruency of sides
            return False

        @property
        def sides(self):
            if self.__sides is None:
                self.__sides = (
                    self.points[1].segment(self.points[2]),
                    self.points[0].segment(self.points[2]),
                    self.points[0].segment(self.points[1])
                )
            return self.__sides

        @property
        def angles(self):
            if self.__angles is None:
                self.__angles = (
                    self.points[0].angle(self.points[1], self.points[2]),
                    self.points[1].angle(self.points[0], self.points[2]),
                    self.points[2].angle(self.points[0], self.points[1])
                )
            return self.__angles

        @property
        def permutations(self):
            if self.__permutations is None:
                self.__permutations = (
                    (self.points[0], self.points[1], self.points[2]),
                    (self.points[0], self.points[2], self.points[1]),
                    (self.points[1], self.points[0], self.points[2]),
                    (self.points[1], self.points[2], self.points[0]),
                    (self.points[2], self.points[0], self.points[1]),
                    (self.points[2], self.points[1], self.points[0])
                )
            return self.__permutations

        def __str__(self):
            return '\\bigtriangleup %s %s %s' % self.points

    class Polygon(Figure):
        def __init__(self, *points):
            self.points = tuple(points)

        def __str__(self):
            return ' '.join(['%s'] * len(self.points)) % self.points

    def __init__(self):
        self.__objects = []
        self.validation_constraints = []
        self.adjustment_constraints = []
        self.__properties = set()
        self.__frozen = False
        self.__angles = {} # {vector, vector} => angle
        self.__segments = {} # {point, point} => angle

    def add_property(self, prop):
        if prop not in self.__properties:
            self.__properties.add(prop)

    @property
    def properties(self):
        return list(self.__properties)

    def constraint(self, kind, *args, **kwargs):
        cns = Constraint(kind, self, *args, **kwargs)
        if not self.__frozen:
            if kind.stage == Stage.validation:
                self.validation_constraints.append(cns)
            else:
                self.adjustment_constraints.append(cns)
        return cns

    def equilateral_constraint(self, triangle, **kwargs):
        if 'comment' not in kwargs:
            kwargs = dict(kwargs)
            kwargs['comment'] = Comment(
                '$%{triangle:equilateral}$ is equilateral',
                {'equilateral': triangle}
            )
        self.constraint(Constraint.Kind.equilateral, triangle, **kwargs)

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

    def points(self, max_layer='invisible'):
        return [p for p in self.__objects if isinstance(p, CoreScene.Point) and p.layer in CoreScene.layers_by(max_layer)]

    def lines(self, max_layer='invisible'):
        return [l for l in self.__objects if isinstance(l, CoreScene.Line) and l.layer in CoreScene.layers_by(max_layer)]

    def circles(self, max_layer='invisible'):
        return [c for c in self.__objects if isinstance(c, CoreScene.Circle) and c.layer in CoreScene.layers_by(max_layer)]

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

    def assert_vector(self, obj):
        self.assert_type(obj, CoreScene.Vector)

    def assert_segment(self, obj):
        self.assert_type(obj, CoreScene.Segment)

    def assert_angle(self, obj):
        self.assert_type(obj, CoreScene.Angle)

    def free_point(self, **kwargs):
        return CoreScene.Point(self, origin=CoreScene.Point.Origin.free, **kwargs)

    def existing_line(self, point0, point1):
        for cnstr in self.constraints(Constraint.Kind.not_equal):
            if {point0, point1} == {*cnstr.params}:
                break
        else:
            return None
        for line in self.lines():
            if point0 in line and point1 in line:
                return line
        return None

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

    def dump(self, include_constraints=False, max_layer='auxiliary'):
        print('Objects:')
        print('\n'.join(['\t' + obj.description for obj in self.__objects if obj.layer in CoreScene.layers_by(max_layer)]))
        counts = [len([o for o in self.__objects if o.layer == layer]) for layer in ('user', 'auxiliary', 'invisible')]
        print('Total: %s objects (+ %s auxiliary, %s invisible)' % tuple(counts))
        if include_constraints:
            if self.validation_constraints:
                print('\nValidation constraints:')
                print('\n'.join(['\t' + str(cnstr) for cnstr in self.validation_constraints]))
            if self.adjustment_constraints:
                print('\nAdjustment constraints:')
                print('\n'.join(['\t' + str(cnstr) for cnstr in self.adjustment_constraints]))

class Stage(Enum):
    validation        = auto()
    adjustment        = auto()

class Constraint:
    @unique
    class Kind(Enum):
        not_equal                 = ('not_equal', Stage.validation, CoreScene.Point, CoreScene.Point)
        not_collinear             = ('not_collinear', Stage.validation, CoreScene.Point, CoreScene.Point, CoreScene.Point)
        collinear                 = ('collinear', Stage.adjustment, CoreScene.Point, CoreScene.Point, CoreScene.Point)
        opposite_side             = ('opposite_side', Stage.validation, CoreScene.Point, CoreScene.Point, CoreScene.Line)
        same_side                 = ('same_side', Stage.validation, CoreScene.Point, CoreScene.Point, CoreScene.Line)
        same_direction            = ('same_direction', Stage.validation, CoreScene.Point, CoreScene.Point, CoreScene.Point)
        inside_segment            = ('inside_segment', Stage.validation, CoreScene.Point, CoreScene.Segment)
        inside_angle              = ('inside_angle', Stage.validation, CoreScene.Point, CoreScene.Angle)
        quadrilateral             = ('quadrilateral', Stage.validation, CoreScene.Point, CoreScene.Point, CoreScene.Point, CoreScene.Point)
        equilateral               = ('equilateral', Stage.adjustment, CoreScene.Triangle)
        convex_polygon            = ('convex_polygon', Stage.validation, List[CoreScene.Point])
        distance                  = ('distance', Stage.adjustment, CoreScene.Vector, int)
        length_ratio              = ('length_ratio', Stage.adjustment, CoreScene.Segment, CoreScene.Segment, int)
        parallel_vectors          = ('parallel_vectors', Stage.adjustment, CoreScene.Vector, CoreScene.Vector)
        angles_ratio              = ('angles_ratio', Stage.adjustment, CoreScene.Angle, CoreScene.Angle, int)
        perpendicular             = ('perpendicular', Stage.adjustment, CoreScene.Segment, CoreScene.Segment)
        acute_angle               = ('acute_angle', Stage.validation, CoreScene.Angle)
        obtuse_angle              = ('obtuse_angle', Stage.validation, CoreScene.Angle)
        angle_value               = ('angle_value', Stage.adjustment, CoreScene.Angle, int)

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
        self.comment = None
        self.update(kwargs)

    def update(self, kwargs):
        self.__dict__.update(kwargs)

    def __str__(self):
        params = [para.label if isinstance(para, CoreScene.Object) else str(para) for para in self.params]
        extras = dict(self.__dict__)
        del extras['kind']
        del extras['params']
        del extras['comment']
        if self.comment:
            return 'Constraint(%s) %s %s (%s)' % (self.kind.name, params, self.comment, extras)
        else:
            return 'Constraint(%s) %s (%s)' % (self.kind.name, params, extras)
