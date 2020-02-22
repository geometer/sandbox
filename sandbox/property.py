from . import Scene

class Line:
    def __init__(self, points):
        assert len(points) >= 2
        for point in points:
            assert isinstance(point, Scene.Point)
        self.points = points

class Property:
    pass

class RightAngleProperty(Property):
    def __init__(self, AB, CD):
        assert len(AB) == 2 and len(CD) == 2
        for point in AB:
            assert isinstance(point, Scene.Point)
        for point in CD:
            assert isinstance(point, Scene.Point)
        self.AB = AB
        self.CD = CD

    def __str__(self):
        if self.AB[0] == self.CD[0]:
            return '∠ %s %s %s = 90º' % (self.AB[1].label, self.CD[0].label, self.CD[1].label)
        return '∠ (%s %s), (%s %s) = 90º' % (self.AB[0].label, self.AB[1].label, self.CD[0].label, self.CD[1].label)

class EqualAnglesProperty(Property):
    def __init__(self, ABCD, EFGH):
        assert len(ABCD) == 4 and len(EFGH) == 4
        for point in ABCD:
            assert isinstance(point, Scene.Point)
        for point in EFGH:
            assert isinstance(point, Scene.Point)
        self.ABCD = ABCD
        self.EFGH = EFGH

    def __str__(self):
        def angle_str(four):
            if four[0] == four[2]:
                return '∠ %s %s %s' % (four[1].label, four[2].label, four[3].label)
            return '∠ (%s %s), (%s %s)' % (four[0].label, four[1].label, four[2].label, four[3].label)
        return '%s = %s' % (angle_str(self.ABCD), angle_str(self.EFGH))

class EqualDistancesProperty(Property):
    def __init__(self, AB, CD):
        assert len(AB) == 2
        for point in AB:
            assert isinstance(point, Scene.Point)
        assert len(CD) == 2
        for point in CD:
            assert isinstance(point, Scene.Point)
        self.AB = AB
        self.CD = CD

    def __str__(self):
        return '|%s %s| = |%s %s|' % (self.AB[0].label, self.AB[1].label, self.CD[0].label, self.CD[1].label)

class EquilateralTriangleProperty(Property):
    def __init__(self, ABC):
        assert len(ABC) == 3
        for point in ABC:
            assert isinstance(point, Scene.Point)
        self.ABC = ABC

    def __str__(self):
        return 'equilateral △ %s %s %s' % (self.ABC[0].label, self.ABC[1].label, self.ABC[2].label)

class IsoscelesTriangleProperty(Property):
    def __init__(self, A, BC):
        assert isinstance(A, Scene.Point)
        assert len(BC) == 2
        for point in BC:
            assert isinstance(point, Scene.Point)
        self.A = A
        self.BC = BC

    def __str__(self):
        return 'isosceles △ %s %s %s' % (self.A.label, self.BC[0].label, self.BC[1].label)

class SimilarTrianglesProperty(Property):
    def __init__(self, ABC, DEF):
        assert len(ABC) == 3 and len(DEF) == 3
        for point in ABC:
            assert isinstance(point, Scene.Point)
        for point in DEF:
            assert isinstance(point, Scene.Point)
        self.ABC = ABC
        self.DEF = DEF

    def __str__(self):
        return '△ %s %s %s ~ △ %s %s %s' % (
            self.ABC[0].label, self.ABC[1].label, self.ABC[2].label,
            self.DEF[0].label, self.DEF[1].label, self.DEF[2].label
        )

class EqualTrianglesProperty(Property):
    def __init__(self, ABC, DEF):
        assert len(ABC) == 3 and len(DEF) == 3
        for point in ABC:
            assert isinstance(point, Scene.Point)
        for point in DEF:
            assert isinstance(point, Scene.Point)
        self.ABC = ABC
        self.DEF = DEF

    def __str__(self):
        return '△ %s %s %s = △ %s %s %s' % (
            self.ABC[0].label, self.ABC[1].label, self.ABC[2].label,
            self.DEF[0].label, self.DEF[1].label, self.DEF[2].label
        )
