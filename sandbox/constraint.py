from .core import CoreScene
from .placement import TwoDCoordinates, TwoDVector

class Constraint:
    pass

class OppositeSideConstraint(Constraint):
    # Points A and B are located on opposite sides relative to the line

    def __init__(self, A: CoreScene.Point, B: CoreScene.Point, line: CoreScene.Line):
        self.A = A
        self.B = B
        self.line = line

    def validate(self, placement):
        def clockwise(p0: TwoDCoordinates, p1: TwoDCoordinates, p2: TwoDCoordinates) -> bool:
            return TwoDVector(p1, p0).vector_product(TwoDVector(p2, p0)) < 0

        a = placement.location(self.A)
        b = placement.location(self.B)
        p = placement.location(self.line.point0)
        q = placement.location(self.line.point1)
        return clockwise(p, q, a) != clockwise(p, q, b)

    def __str__(self):
        return 'Points %s and %s are located on opposite sides relative to the line %s' % (self.A.label, self.B.label, self.line.label)
