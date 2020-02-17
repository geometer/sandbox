#!/var/www/sandbox/virtualenv/bin/python

from sandbox import *
from sandbox.hunter import hunt

scene = Scene()

A = scene.free_point(label='A')
B = scene.free_point(label='B')
C = scene.free_point(label='C')

def napoleonic(A: Scene.Point, B: Scene.Point, C: Scene.Point):
    c0 = A.circle_via(B)
    c1 = B.circle_via(A)
    V = c0.intersection_point(c1, label=C.label + '1')
    V.add_constraint(OppositeSideConstraint(C, V, A, B))
    scene.centre_point(A, B, V, label=C.label + '2')

napoleonic(A, B, C)
napoleonic(C, A, B)
napoleonic(B, C, A)

hunt(scene)
