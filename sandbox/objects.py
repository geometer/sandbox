import itertools

class Scene:
    class Object:
        """Common ancestor for all geometric objects like point, line, circle"""

        def __init__(self, scene, **kwargs):
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
                elif isinstance(value, list) or isinstance(value, tuple):
                    dct[key] = [elt.label if isinstance(elt, Scene.Object) else str(elt) for elt in value]
                else:
                    dct[key] = value
            return '%s `%s` %s' % (self.__class__.__name__, self.label, dct)

    class Point(Object):
        def __init__(self, scene, **kwargs):
            assert 'origin' in kwargs, 'Cannot create a point with unknown origin'
            Scene.Object.__init__(self, scene, **kwargs)

    class Line(Object):
        def __init__(self, scene, **kwargs):
            Scene.Object.__init__(self, scene, **kwargs)

    class Circle(Object):
        def __init__(self, scene, **kwargs):
            Scene.Object.__init__(self, scene, **kwargs)

    def __init__(self):
        self.__objects = []

    @property
    def points(self):
        return [p for p in self.__objects if isinstance(p, Scene.Point)]

    def __assert_point(self, obj):
        assert isinstance(obj, Scene.Point)
        assert obj.scene == self

    def __assert_points(self, *args):
        for p in args:
            self.__assert_point(p)

    def __assert_line_or_circle(self, obj):
        assert isinstance(obj, Scene.Line) or isinstance(obj, Scene.Circle), 'Unexpected type %s' % type(obj)
        assert obj.scene == self

    def __assert_line(self, obj):
        assert isinstance(obj, Scene.Line)
        assert obj.scene == self

    def __assert_circle(self, obj):
        assert isinstance(obj, Scene.Circle)
        assert obj.scene == self

    def free_point(self, **kwargs):
        circle = kwargs.get('circle')
        if circle:
            self.__assert_circle(circle)
            return Scene.Point(self, origin='circle', **kwargs)

        line = kwargs.get('line')
        if line:
            self.__assert_line(line)
            return Scene.Point(self, origin='line', **kwargs)

        return Scene.Point(self, origin='free', **kwargs)

    def line(self, point0, point1, **kwargs):
        self.__assert_points(point0, point1)
        return Scene.Line(self, point0=point0, point1=point1, **kwargs)

    def circle(self, **kwargs):
        centre = kwargs.get('centre')
        self.__assert_point(centre)
        point = kwargs.get('point')
        if point:
            del kwargs['point']
            return Scene.Circle(self, radius_start=centre, radius_end=point, **kwargs)
        self.__assert_points(kwargs.get('radius_start'), kwargs.get('radius_end'))
        return Scene.Circle(self, **kwargs)

    def intersection_point(self, obj0, obj1, **kwargs):
        """Point that is an intersection of given objects (lines or circles).
           Requires a constraint for correct placement if at lease one on the objects is a circle"""
        self.__assert_line_or_circle(obj0)
        self.__assert_line_or_circle(obj1)
        if isinstance(obj0, Scene.Circle):
            if isinstance(obj1, Scene.Circle):
                return Scene.Point(self, origin='intersection(circle,circle)', circle0=obj0, circle1=obj1, **kwargs)
            else:
                return Scene.Point(self, origin='intersection(circle,line)', circle=obj0, line=obj1, **kwargs)
        else:
            if isinstance(obj1, Scene.Circle):
                return Scene.Point(self, origin='intersection(circle,line)', circle=obj1, line=obj0, **kwargs)
            else:
                return Scene.Point(self, origin='intersection(line,line)', line0=obj0, line1=obj1, **kwargs)

    def centre_point(self, *args, **kwargs):
        self.__assert_points(*args)
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
