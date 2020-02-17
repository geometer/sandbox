import itertools

class Scene:
    class Object:
        """Common ancestor for all geometric objects like point, line, circle"""

        def __init__(self, scene, **kwargs):
            assert isinstance(scene, Scene)
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
                if isinstance(value, Scene.Object):
                    dct[key] = value.label
                elif isinstance(value, (list, tuple)):
                    dct[key] = [elt.label if isinstance(elt, Scene.Object) else str(elt) for elt in value]
                else:
                    dct[key] = value
            return '%s `%s` %s' % (self.__class__.__name__, self.label, dct)

    class Point(Object):
        def __init__(self, scene, **kwargs):
            assert 'origin' in kwargs, 'Cannot create a point with unknown origin'
            Scene.Object.__init__(self, scene, **kwargs)

        def line_via(self, point, **kwargs):
            self.scene.assert_point(point)
            assert self != point, 'Cannot create a line by a single point'
            return Scene.Line(self.scene, point0=self, point1=point, **kwargs)

        def circle_via(self, point, **kwargs):
            self.scene.assert_point(point)
            assert self != point, 'Cannot create a circle of zero radius'
            return Scene.Circle(self.scene, centre=self, radius_start=self, radius_end=point, **kwargs)

        def circle_with_radius(self, start, end, **kwargs):
            self.scene.assert_point(start)
            self.scene.assert_point(end)
            assert start != end, 'Cannot create a circle of zero radius'
            return Scene.Circle(self.scene, centre=self, radius_start=start, radius_end=end, **kwargs)

    class Line(Object):
        def __init__(self, scene, **kwargs):
            Scene.Object.__init__(self, scene, **kwargs)

        def free_point(self, **kwargs):
            return Scene.Point(self.scene, origin='line', line=self, **kwargs)

        def intersection_point(self, obj, **kwargs):
            """Creates an intersection point of the line and given object (line or circle).
               Requires a constraint for determinate placement if the object a circle"""
            self.scene.assert_line_or_circle(obj)
            assert self != obj, 'The line does not cross itself'
            if isinstance(obj, Scene.Circle):
                return Scene.Point(self.scene, origin='intersection(circle,line)', circle=obj, line=self, **kwargs)
            else:
                return Scene.Point(self.scene, origin='intersection(line,line)', line0=self, line1=obj, **kwargs)

    class Circle(Object):
        def __init__(self, scene, **kwargs):
            Scene.Object.__init__(self, scene, **kwargs)

        def free_point(self, **kwargs):
            return Scene.Point(self.scene, origin='circle', circle=self, **kwargs)

        def intersection_point(self, obj, **kwargs):
            """Creates an intersection point of the line and given object (line or circle).
               Requires a constraint for determinate placement"""
            self.scene.assert_line_or_circle(obj)
            assert self != obj, 'The circle does not cross itself'
            if isinstance(obj, Scene.Circle):
                return Scene.Point(self.scene, origin='intersection(circle,circle)', circle0=self, circle1=obj, **kwargs)
            else:
                return Scene.Point(self.scene, origin='intersection(circle,line)', circle=self, line=obj, **kwargs)

    def __init__(self):
        self.__objects = []

    @property
    def points(self):
        return [p for p in self.__objects if isinstance(p, Scene.Point)]

    def assert_type(self, obj, *args):
        assert isinstance(obj, args), 'Unexpected type %s' % type(obj)
        assert obj.scene == self

    def assert_point(self, obj):
        self.assert_type(obj, Scene.Point)

    def assert_line_or_circle(self, obj):
        self.assert_type(obj, Scene.Line, Scene.Circle)

    def free_point(self, **kwargs):
        return Scene.Point(self, origin='free', **kwargs)

    def centre_point(self, *args, **kwargs):
        assert len(args) > 0
        for point in args:
            self.assert_point(point)
        return Scene.Point(self, origin='centre', points=args, **kwargs)

    def add(self, obj: Object):
        self.__objects.append(obj)

    def get(self, key: str):
        for obj in self.__objects:
            if obj.label == key:
                return obj
        return None

    def __str__(self):
        return '\n'.join([str(obj) for obj in self.__objects])
