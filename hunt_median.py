#!/var/www/sandbox/virtualenv/bin/python

from sandbox import *
from sandbox.hunter import hunt

scene = Scene()

A = scene.free_point(label='A')
B = scene.free_point(label='B')
C = scene.free_point(label='C')
M = scene.centre_point(A, B, label='M')
l = C.line_via(M)
D = l.free_point(label='D')
E = D.circle_with_radius(A, B).intersection_point(
    B.circle_with_radius(A, D),
    label='E'
)
E.add_constraint(OppositeSideConstraint(E, A, B, D))
para = D.line_via(E)
A1 = para.intersection_point(A.line_via(C), label='A1')
B1 = para.intersection_point(B.line_via(C), label='B1')

print(scene)

hunt(scene)
