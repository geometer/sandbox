#!/var/www/sandbox/virtualenv/bin/python

from sandbox import *
from sandbox.hunter import hunt

scene = Scene()

A = scene.free_point(label='A')
B = scene.free_point(label='B')
c0 = A.circle_via(B)
c1 = B.circle_via(A)
C = c0.intersection_point(c1, label='C')

print('\n*** Equilateral ABC ***\n')
hunt(scene)

scene2 = Scene()

A = scene2.free_point(label='A')
B = scene2.free_point(label='B')
C = B.circle_via(A).free_point(label='C')

print('\n*** Isoscales ABC (AB = BC) ***\n')
hunt(scene2)
