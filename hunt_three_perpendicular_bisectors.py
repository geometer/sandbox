#!/var/www/sandbox/virtualenv/bin/python

from sandbox import *
from sandbox.hunter import hunt

scene = Scene()

A = scene.free_point(label='A')
B = scene.free_point(label='B')
C = scene.free_point(label='C')
perp_AB = scene.perpendicular_bisector_line(A, B)
perp_AC = scene.perpendicular_bisector_line(A, C)
perp_BC = scene.perpendicular_bisector_line(B, C)
O = perp_AB.intersection_point(perp_AC, label='O')
P = perp_AB.intersection_point(perp_BC, label='P')
Q = perp_AC.intersection_point(perp_BC, label='Q')

scene.dump()

hunt(scene, 'coincidences')
