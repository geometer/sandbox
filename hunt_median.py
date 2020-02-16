#!/var/www/sandbox/virtualenv/bin/python

from sandbox import *
from sandbox.hunter import hunt

scene = Scene()

A = scene.freePoint(id='A')
B = scene.freePoint(id='B')
C = scene.freePoint(id='C')
M = scene.centrePoint(A, B, id='M')
l = scene.line(C, M)
D = scene.freePoint(line=l, id='D')
E = scene.intersectionPoint(
    scene.circle(centre=D, radius_start=A, radius_end=B),
    scene.circle(centre=B, radius_start=A, radius_end=D),
    id='E'
)
E.add_constraint(OppositeSideConstraint(E, A, B, D))
para = scene.line(D, E)
A1 = scene.intersectionPoint(para, scene.line(A, C), id='A1')
B1 = scene.intersectionPoint(para, scene.line(B, C), id='B1')

print(scene)

hunt(scene)
