#!/var/www/sandbox/virtualenv/bin/python

from sandbox import *
from sandbox.hunter import hunt

scene = Scene()

A = scene.free_point(label='A')
B = scene.free_point(label='B')
C = scene.free_point(label='C')
M = scene.centre_point(A, B, label='M')
l = scene.line(C, M)
D = l.free_point(label='D')
E = scene.circle(centre=D, radius_start=A, radius_end=B).intersection_point(
    scene.circle(centre=B, radius_start=A, radius_end=D),
    label='E'
)
E.add_constraint(OppositeSideConstraint(E, A, B, D))
para = scene.line(D, E)
A1 = para.intersection_point(scene.line(A, C), label='A1')
B1 = para.intersection_point(scene.line(B, C), label='B1')

print(scene)

hunt(scene)
