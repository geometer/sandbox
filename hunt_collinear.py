#!/var/www/sandbox/virtualenv/bin/python

from sandbox import *
from sandbox.hunter import hunt

scene = Scene()

A = scene.free_point(label='A')
B = scene.free_point(label='B')
C = scene.gravity_centre_point(A, B, label='C')
D = scene.gravity_centre_point(A, C, label='D')
E = scene.gravity_centre_point(A, D, label='E')

scene.dump()

hunt(scene, 'collinears')
