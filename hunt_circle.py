#!/var/www/sandbox/virtualenv/bin/python

from sandbox import *
from sandbox.hunter import hunt

scene = Scene()

O = scene.free_point(label='O')
A = scene.free_point(label='A')
c = scene.circle(centre=O, point=A)
B = c.free_point(label='B')
C = c.free_point(label='C')

hunt(scene)
