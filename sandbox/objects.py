import itertools
from typing import List

class Object:
    def __init__(self, scene, **kwargs):
        id = kwargs.get('id')
        if id:
            assert scene.get(id) is None, 'Object with key `%s` already exists' % id
        else:
            pattern = self.__class__.__name__ + ' %d'
            for index in itertools.count():
                id = pattern % index
                if scene.get(id) is None:
                    self.id = id
                    break

        self.scene = scene
        self.__dict__.update(kwargs)
        self.__constraints = None
        scene.add(self)

    @property
    def name(self):
        return '%s `%s`' % (self.__class__.__name__, self.id)

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
            if key in ('id', 'scene'):
                continue
            value = self.__dict__[key]
            if value is None:
                continue
            if isinstance(value, Object):
                dct[key] = value.name
            elif isinstance(value, list):
                dct[key] = [elt.name if isinstance(elt, Object) else str(elt) for elt in value]
            else:
                dct[key] = value
        return '%s `%s` %s' % (self.__class__.__name__, self.id, dct)

class Scene:
    def __init__(self):
        self.__objects = []

    @property
    def points(self):
        return [p for p in self.__objects if isinstance(p, Point)]

    def add(self, obj: Object):
        self.__objects.append(obj)

    def get(self, key: str):
        for obj in self.__objects:
            if obj.id == key:
                return obj
        return None

    def __str__(self):
        return '\n'.join([str(obj) for obj in self.__objects])

class Point(Object):
    def __init__(self, scene: Scene, **kwargs):
        assert self.__class__ != Point, 'Cannot create abstract point'
        Object.__init__(self, scene, **kwargs)

class FreePoint(Point):
    def __init__(self, scene: Scene, **kwargs):
        Point.__init__(self, scene, **kwargs)

def assert_same_scene(obj0: Object, obj1: Object):
    assert obj0.scene == obj1.scene, 'Trying to use object from different scenes'

class PointOnLine(Point):
    def __init__(self, point0: Point, point1: Point, ratio: float, **kwargs):
        assert_same_scene(point0, point1)

        Point.__init__(self, point0.scene, point0=point0, point1=point1, ratio=ratio, **kwargs)

class CentrePoint(Point):
    def __init__(self, points: List[Point], **kwargs):
        assert len(points) > 0, 'Cannot calculate centre of empty list'
        pt0 = points[0]
        for index in range(1, len(points)):
            assert_same_scene(pt0, points[index])

        Point.__init__(self, pt0.scene, **kwargs)
        self.points = points

class Line(Object):
    def __init__(self, point0: Point, point1: Point, **kwargs):
        assert_same_scene(point0, point1)

        Object.__init__(self, point0.scene, **kwargs)
        self.point0 = point0
        self.point1 = point1

class Circle(Object):
    def __init__(self, centre: Point, point: Point, **kwargs):
        assert_same_scene(centre, point)

        Object.__init__(self, centre.scene, **kwargs)
        self.centre = centre
        self.point = point

class FreePointOnCircle(Point):
    def __init__(self, circle: Circle, **kwargs):
        Point.__init__(self, circle.scene, circle=circle, **kwargs)

class CirclesIntersection(Point):
    def __init__(self, circle0: Circle, circle1: Circle, **kwargs):
        assert_same_scene(circle0, circle1)

        Point.__init__(self, circle0.scene, circle0=circle0, circle1=circle1, **kwargs)
