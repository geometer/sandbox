#!/var/www/sandbox/virtualenv/bin/python

from sandbox import *
from sandbox.hunter import hunt

scene = Scene()

A = scene.freePoint(id='A')
B = scene.freePoint(id='B')
C = scene.freePoint(id='C')

def napoleonic(A: Scene.Point, B: Scene.Point, C: Scene.Point):
    c0 = scene.circle(centre=A, point=B)
    c1 = scene.circle(centre=B, point=A)
    V = scene.intersectionPoint(c0, c1, id=C.id + '1')
    V.add_constraint(OppositeSideConstraint(C, V, A, B))
    scene.centrePoint(A, B, V, id=C.id + '2')

napoleonic(A, B, C)
napoleonic(C, A, B)
napoleonic(B, C, A)

hunt(scene)
