#!/var/www/sandbox/virtualenv/bin/python

from sandbox import *
from sandbox.hunter import hunt

scene = Scene()

A = scene.free_point(id='A')
B = scene.free_point(id='B')
C = scene.free_point(id='C')

def napoleonic(A: Scene.Point, B: Scene.Point, C: Scene.Point):
    c0 = scene.circle(centre=A, point=B)
    c1 = scene.circle(centre=B, point=A)
    V = scene.intersection_point(c0, c1, id=C.id + '1')
    V.add_constraint(OppositeSideConstraint(C, V, A, B))
    scene.centre_point(A, B, V, id=C.id + '2')

napoleonic(A, B, C)
napoleonic(C, A, B)
napoleonic(B, C, A)

hunt(scene)
