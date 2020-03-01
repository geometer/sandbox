from . import Scene

class Property:
    pass

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
