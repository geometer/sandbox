#!/var/www/sandbox/virtualenv/bin/python

from sandbox import *
from sandbox.hunter import hunt

scene = Scene()

O = scene.free_point(label='O')
A = scene.free_point(label='A')
c = scene.circle(centre=O, point=A)
B = scene.free_point(circle=c, label='B')
C = scene.free_point(circle=c, label='C')

hunt(scene)
