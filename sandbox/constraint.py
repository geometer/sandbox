from .objects import Scene
from .placement import TwoDCoordinates, TwoDVector

class Constraint:
    pass

class OppositeSideConstraint(Constraint):
    # Points A and B are located on opposite sides relative to the line PQ

    def __init__(self, A: Scene.Point, B: Scene.Point, P: Scene.Point, Q: Scene.Point):
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
        return 'Points %s and %s are located on opposite sides relative to the line (%s %s)' % (self.A.label, self.B.label, self.P.label, self.Q.label)
