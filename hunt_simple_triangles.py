#!/var/www/sandbox/virtualenv/bin/python

from sandbox import *
from sandbox.hunter import Hunter

scene = Scene()

A = scene.free_point(label='A')
B = scene.free_point(label='B')
c0 = A.circle_through(B)
c1 = B.circle_through(A)
C = c0.intersection_point(c1, label='C')

print('\n*** Equilateral ABC ***\n')
hunter = Hunter(scene)
hunter.hunt('all')
hunter.dump()

scene2 = Scene()

A = scene2.free_point(label='A')
B = scene2.free_point(label='B')
C = B.circle_through(A).free_point(label='C')

print('\n*** Isosceles ABC (AB = BC) ***\n')
hunter = Hunter(scene2)
hunter.hunt('all')
hunter.dump()
