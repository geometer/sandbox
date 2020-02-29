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
            if coef0 == 0:
                return point
            if coef1 == 0:
                return self
            new_point = CoreScene.Point(
                self.scene,
                CoreScene.Point.Origin.ratio,
                point0=self, point1=point, coef0=coef0, coef1=coef1, **kwargs
            )
            new_point.collinear_constraint(self, point)
            return new_point

        def line_through(self, point, **kwargs):
            self.scene.assert_point(point)
            assert self != point, 'Cannot create a line by a single point'
            self.not_equal_constraint(point)

            existing = self.scene.get_line(self, point)
            if existing:
                return existing.with_extra_args(**kwargs)

            line = CoreScene.Line(self.scene, point0=self, point1=point, **kwargs)
            for cnstr in self.scene.reasoning_constraints:
                if cnstr.kind == Constraint.Kind.collinear:
                    if len(line.all_points.intersection(set(cnstr.params))) == 2:
                        line.all_points.update(cnstr.params)

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

        def belongs_to(self, line_or_circle):
            self.scene.assert_line_or_circle(line_or_circle)
            line_or_circle.all_points.add(self)

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
            self.scene.constraint(Constraint.Kind.not_collinear, self, A, B, **kwargs)

        def collinear_constraint(self, A, B, **kwargs):
            """
            The current point is collinear with A and B.
            """
            cnstr = self.scene.constraint(Constraint.Kind.collinear, self, A, B, **kwargs)
            for line in self.scene.lines():
                if len(line.all_points.intersection(set(cnstr.params))) == 2:
                    line.all_points.update(cnstr.params)

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
            for cnstr in self.scene.constraints(Constraint.Kind.opposite_side):
                if line == cnstr.params[2] and set(cnstr.params[0:2]) == set([self, point]):
                    cnstr.update(kwargs)
                    return
            self.not_collinear_constraint(line.point0, line.point1)
            point.not_collinear_constraint(line.point0, line.point1)
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
            self.not_collinear_constraint(line.point0, line.point1)
            point.not_collinear_constraint(line.point0, line.point1)
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

        def inside_angle_constraint(self, vertex, B, C, **kwargs):
            """
            The point is inside the ∠ B vertex C
            """
            self.same_side_constraint(B, vertex.line_through(C), **kwargs)
            self.same_side_constraint(C, vertex.line_through(B), **kwargs)

        def inside_triangle_constraint(self, A, B, C, **kwargs):
            """
            The point is inside the △ ABC
            """
            A.not_collinear_constraint(B, C)
            if 'comment' not in kwargs:
                kwargs = dict(kwargs)
                kwargs['comment'] = 'The point is inside the triangle'
            self.inside_angle_constraint(A, B, C, **kwargs)
            self.inside_angle_constraint(B, A, C, **kwargs)
            self.inside_angle_constraint(C, B, A, **kwargs)

    class Line(Object):
        def __init__(self, scene, **kwargs):
            CoreScene.Object.__init__(self, scene, **kwargs)
            self.all_points = set([self.point0, self.point1])

        def free_point(self, **kwargs):
            point = CoreScene.Point(self.scene, CoreScene.Point.Origin.line, line=self, **kwargs)
            point.belongs_to(self)
            return point

        def __contains__(self, point):
            if point is None:
                return False
            self.scene.assert_point(point)
            return point in self.all_points 

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
        self.reasoning_constraints = []

    def constraint(self, kind, *args, **kwargs):
        cns = Constraint(kind, self, *args, **kwargs)
        if kind.stage == Stage.validation:
            self.validation_constraints.append(cns)
        elif kind.stage == Stage.adjustment:
            self.adjustment_constraints.append(cns)
        else:
            self.reasoning_constraints.append(cns)
        return cns

    def flush(self):
        for cnstr in self.constraints(Constraint.Kind.not_collinear):
            def adjust(pt0, pt1, pt2):
                line = self.get_line(pt0, pt1)
                if line:
                    for pt in line.all_points:
                        pt.not_equal_constraint(pt2)

            adjust(cnstr.params[0], cnstr.params[1], cnstr.params[2])
            adjust(cnstr.params[1], cnstr.params[2], cnstr.params[0])
            adjust(cnstr.params[2], cnstr.params[0], cnstr.params[1])

        same_side_constraints = self.constraints(Constraint.Kind.same_side)
        for cnstr in same_side_constraints:
            pt0 = cnstr.params[0]
            pt1 = cnstr.params[1]
            line = cnstr.params[2]
            line2 = self.get_line(pt0, pt1)
            if line2:
                for pt in line.all_points:
                    if pt in line2:
                        pt.same_direction_constraint(pt0, pt1)
        for index in range(0, len(same_side_constraints)):
            cnstr0 = same_side_constraints[index]
            for cnstr1 in same_side_constraints[index + 1:]:
                AB = cnstr0.params[2]
                AC = cnstr1.params[2]
                A = self.get_intersection(AB, AC)
                if A is None:
                    continue
                if cnstr0.params[0] == cnstr1.params[0]:
                    B, C, D = cnstr1.params[1], cnstr0.params[1], cnstr0.params[0]
                elif cnstr0.params[1] == cnstr1.params[0]:
                    B, C, D = cnstr1.params[1], cnstr0.params[0], cnstr0.params[1]
                elif cnstr0.params[0] == cnstr1.params[1]:
                    B, C, D = cnstr1.params[0], cnstr0.params[1], cnstr0.params[0]
                elif cnstr0.params[1] == cnstr1.params[1]:
                    B, C, D = cnstr1.params[0], cnstr0.params[0], cnstr0.params[1]
                else:
                    continue
                if B == C or B not in AB or C not in AC:
                    continue
                AD = self.get_line(A, D)
                BC = self.get_line(B, C)
                if AD is None or BC is None:
                    continue
                X = self.get_intersection(AD, BC)
                if X:
                    X.same_direction_constraint(A, D)
                    A.same_direction_constraint(D, X)
                    B.same_direction_constraint(X, C)
                    C.same_direction_constraint(X, B)

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
        elif kind.stage == Stage.adjustment:
            return [cnstr for cnstr in self.adjustment_constraints if cnstr.kind == kind]
        else:
            return [cnstr for cnstr in self.reasoning_constraints if cnstr.kind == kind]

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
        intr = line0.all_points.intersection(line1.all_points)
        return intr.pop() if len(intr) > 0 else None

    def dump(self):
        self.flush()
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
        if self.reasoning_constraints:
            print('\nReasoning constraints:')
            print('\n'.join(['\t' + str(cnstr) for cnstr in self.reasoning_constraints]))
        print('')

class Stage(Enum):
    validation        = auto()
    adjustment        = auto()
    reasoning         = auto()

class Constraint:
    @unique
    class Kind(Enum):
        not_equal         = ('not_equal', Stage.validation, CoreScene.Point, CoreScene.Point)
        not_collinear     = ('not_collinear', Stage.validation, CoreScene.Point, CoreScene.Point, CoreScene.Point)
        collinear         = ('collinear', Stage.reasoning, CoreScene.Point, CoreScene.Point, CoreScene.Point)
        opposite_side     = ('opposite_side', Stage.validation, CoreScene.Point, CoreScene.Point, CoreScene.Line)
        same_side         = ('same_side', Stage.validation, CoreScene.Point, CoreScene.Point, CoreScene.Line)
        same_direction    = ('same_direction', Stage.validation, CoreScene.Point, CoreScene.Point, CoreScene.Point)
        quadrilateral     = ('quadrilateral', Stage.validation, CoreScene.Point, CoreScene.Point, CoreScene.Point, CoreScene.Point)
        convex_polygon    = ('convex_polygon', Stage.validation, List[CoreScene.Point])
        distance          = ('distance', Stage.adjustment, CoreScene.Point, CoreScene.Point, int)
        distances_ratio   = ('distances_ratio', Stage.adjustment, CoreScene.Point, CoreScene.Point, CoreScene.Point, CoreScene.Point, int)
        right_angle       = ('right_angle', Stage.adjustment, CoreScene.Point, CoreScene.Point, CoreScene.Point, CoreScene.Point)
        angles_ratio      = ('angles_ratio', Stage.adjustment, CoreScene.Point, CoreScene.Point, CoreScene.Point, CoreScene.Point, CoreScene.Point, CoreScene.Point, CoreScene.Point, CoreScene.Point, int)
        perpendicular     = ('perpendicular', Stage.reasoning, CoreScene.Line, CoreScene.Line)

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
            else:
                assert isinstance(arg, knd)
            self.params.append(arg)
        self.kind = kind
        self.comments = []
        self.update(kwargs)

    def update(self, kwargs):
        if 'comment' in kwargs:
            if kwargs['comment'] not in self.comments:
                self.comments.append(kwargs['comment'])
            del kwargs['comment']
        self.__dict__.update(kwargs)

    def __str__(self):
        params = [para.label if isinstance(para, CoreScene.Object) else para for para in self.params]
        if self.comments:
            return 'Constraint(%s) %s %s' % (self.kind.name, params, self.comments)
        else:
            return 'Constraint(%s) %s' % (self.kind.name, params)
