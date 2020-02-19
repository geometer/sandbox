#!/var/www/sandbox/virtualenv/bin/python

from sandbox import *
from sandbox.hunter import hunt

scene = Scene()

A = scene.free_point(label='A')
B = scene.free_point(label='B')
C = scene.free_point(label='C')

def napoleonic(A: Scene.Point, B: Scene.Point, C: Scene.Point):
    c0 = A.circle_through(B)
    c1 = B.circle_through(A)
    line = A.line_through(B, auxiliary=True)
    V = c0.intersection_point(c1, label=C.label + '1')
    V.constraint(Constraint.Kind.opposite_side, C, line)
    scene.gravity_centre_point(A, B, V, label=C.label + '2')

napoleonic(A, B, C)
napoleonic(C, A, B)
napoleonic(B, C, A)

hunt(scene)
