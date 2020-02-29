from . import Scene

class Property:
    pass

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
