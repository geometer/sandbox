from . import Scene

class Property:
    def __str__(self):
        return str(self.description)

class EquilateralTriangleProperty(Property):
    def __init__(self, ABC):
        assert len(ABC) == 3
        for point in ABC:
            assert isinstance(point, Scene.Point)
        self.ABC = ABC

    def __str__(self):
        return 'equilateral △ %s %s %s' % (self.ABC[0].label, self.ABC[1].label, self.ABC[2].label)
