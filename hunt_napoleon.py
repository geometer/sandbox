#!/var/www/sandbox/virtualenv/bin/python

from sandbox import *
from sandbox.hunter import hunt

scene = Scene()

A = FreePoint(scene, id='A')
B = FreePoint(scene, id='B')
C = FreePoint(scene, id='C')

def napoleonic(A: Point, B: Point, C: Point):
    c0 = Circle(centre=A, point=B)
    c1 = Circle(centre=B, point=A)
    V = CirclesIntersection(c0, c1, id=C.id + '1')
    V.add_constraint(OppositeSideConstraint(C, V, A, B))
    CentrePoint([A, B, V], id=C.id + '2')

napoleonic(A, B, C)
napoleonic(C, A, B)
napoleonic(B, C, A)

hunt(scene)
