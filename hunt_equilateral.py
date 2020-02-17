#!/var/www/sandbox/virtualenv/bin/python

from sandbox import *
from sandbox.hunter import hunt

scene = Scene()

A = scene.free_point(label='A')
B = scene.free_point(label='B')
c0 = A.circle_through(B)
c1 = B.circle_through(A)
C = c0.intersection_point(c1, label='C')
scene.gravity_centre_point(A, B, C, label='D')
scene.gravity_centre_point(A, B, label='E')

hunt(scene)
