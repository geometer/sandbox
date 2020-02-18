#!/var/www/sandbox/virtualenv/bin/python

from sandbox import *
from sandbox.hunter import hunt

scene = Scene()

A = scene.free_point(label='A')
B = scene.free_point(label='B')
C = scene.free_point(label='C')
A1 = scene.perpendicular_foot_point(A, B.line_through(C), label='A1')
B1 = scene.perpendicular_foot_point(B, C.line_through(A), label='B1')
C1 = scene.perpendicular_foot_point(C, A.line_through(B), label='C1')
O = A.line_through(A1).intersection_point(B.line_through(B1), label='O')

print(scene)

hunt(scene, 'rational_angles')
