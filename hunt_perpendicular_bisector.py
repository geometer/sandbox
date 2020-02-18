#!/var/www/sandbox/virtualenv/bin/python

from sandbox import *
from sandbox.hunter import hunt

scene = Scene()

A = scene.free_point(label='A')
B = scene.free_point(label='B')
perp = scene.perpendicular_bisector_line(A, B)
C = perp.intersection_point(A.line_through(B), label='C')
D = perp.free_point(label='D')

print(scene)

hunt(scene, 'all')
