#!/var/www/sandbox/virtualenv/bin/python

from sandbox import *
from sandbox.hunter import hunt

scene = Scene()

A = scene.free_point(label='A')
B = scene.free_point(label='B')
C = scene.free_point(label='C')
A1 = scene.perpendicular_foot_point(A, B.line_through(C), label='A1')

print(scene)

hunt(scene, 'all')
