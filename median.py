#!/var/www/sandbox/virtualenv/bin/python

from sandbox import *
from sandbox.hunter import hunt

scene = Scene()

A = scene.free_point(id='A')
B = scene.free_point(id='B')
C = scene.free_point(id='C')
M = scene.centre_point(A, B, id='M')
l = scene.line(C, M)
D = scene.free_point(line=l, id='D')
E = scene.intersection_point(
    scene.circle(centre=D, radius_start=A, radius_end=B),
    scene.circle(centre=B, radius_start=A, radius_end=D),
    id='E'
)
E.add_constraint(OppositeSideConstraint(E, A, B, D))
para = scene.line(D, E)
A1 = scene.intersection_point(para, scene.line(A, C), id='A1')
B1 = scene.intersection_point(para, scene.line(B, C), id='B1')

print(scene)
placement = Placement(scene)
print('|D A1| = %.5f' % placement.distance('D', 'A1'))
print('|D B1| = %.5f' % placement.distance('D', 'B1'))
