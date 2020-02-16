#!/var/www/sandbox/virtualenv/bin/python

from sandbox import *
from sandbox.hunter import hunt

scene = Scene()

A = scene.free_point(label='A')
B = scene.free_point(label='B')
c0 = scene.circle(centre=A, point=B)
c1 = scene.circle(centre=B, point=A)
C = scene.intersection_point(c0, c1, label='C')
scene.centre_point(A, B, C, label='D')
scene.centre_point(A, B, label='E')

hunt(scene)
