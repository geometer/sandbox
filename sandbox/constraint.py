from .objects import Point
from .placement import TwoDCoordinates, TwoDVector

class Constraint:
    pass

class OppositeSideConstraint(Constraint):
    # Points A and B are located on opposite sides relative to the line PQ

    def __init__(self, A: Point, B: Point, P: Point, Q: Point):
        self.A = A
        self.B = B
        self.P = P
        self.Q = Q

    def validate(self, placement):
        def clockwise(p0: TwoDCoordinates, p1: TwoDCoordinates, p2: TwoDCoordinates) -> bool:
            return TwoDVector(p1, p0).vector_product(TwoDVector(p2, p0)) < 0

        a = placement.location(self.A)
        b = placement.location(self.B)
        p = placement.location(self.P)
        q = placement.location(self.Q)
        return clockwise(p, q, a) != clockwise(p, q, b)

    def __str__(self):
        return 'Points %s and %s are located on opposite sides relative to the line (%s %s)' % (self.A.id, self.B.id, self.P.id, self.Q.id)
