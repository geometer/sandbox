#!/var/www/sandbox/virtualenv/bin/python

# https://www.facebook.com/groups/parmenides52/, problem 4578

import mpmath

from sandbox import *
from sandbox.hunter import hunt

scene = Scene()

A = scene.free_point(label='A')
B = scene.free_point(label='B')
C = scene.free_point(label='C')
heightA = scene.perpendicular_line(A, B.line_through(C))
heightB = scene.perpendicular_line(B, C.line_through(A))
D = heightA.intersection_point(heightB, label='D')
scene.equal_distances_constraint((A, B), (C, D))

scene.dump()

placement = iterative_placement(scene, print_progress=True)

print(placement.angle(C, A, C, B) / mpmath.pi * 180)

#hunt(placement)
