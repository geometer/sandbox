#!/var/www/sandbox/virtualenv/bin/python

# https://www.facebook.com/groups/parmenides52/, problem 4578

import mpmath

from sandbox import *
from sandbox.hunter import hunt

scene = Scene()

A = scene.free_point(label='A')
B = scene.free_point(label='B')
C = scene.free_point(label='C')
A1 = scene.perpendicular_foot_point(A, B.line_through(C), label='A1')
B1 = scene.perpendicular_foot_point(B, C.line_through(A), label='B1')
D = A.line_through(A1).intersection_point(B.line_through(B1), label='D')
D.constraint(Constraint.Kind.inside_triangle, A, B, C)
scene.constraint(Constraint.Kind.equal_distances, A, B, C, D)

scene.dump()

placement = iterative_placement(scene, print_progress=True)

print(placement.angle(C, A, C, B) / mpmath.pi * 180)

#hunt(placement)
