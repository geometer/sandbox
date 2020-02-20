#!/var/www/sandbox/virtualenv/bin/python

from sandbox import *
from sandbox.hunter import hunt

scene = Scene()

A = scene.free_point(label='A')
B = scene.free_point(label='B')
C = scene.free_point(label='C')
M = scene.gravity_centre_point(A, B, label='M')
l = C.line_through(M)
D = l.free_point(label='D')
para = scene.parallel_line(A.line_through(B), D)
A1 = para.intersection_point(A.line_through(C), label='A1')
B1 = para.intersection_point(B.line_through(C), label='B1')

#scene.dump()

#hunt(scene, 'similar_triangles')
hunt(scene, 'all')
