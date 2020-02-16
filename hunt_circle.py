#!/var/www/sandbox/virtualenv/bin/python

from sandbox import *
from sandbox.hunter import hunt

scene = Scene()

O = scene.free_point(id='O')
A = scene.free_point(id='A')
c = scene.circle(centre=O, point=A)
B = scene.free_point(circle=c, id='B')
C = scene.free_point(circle=c, id='C')

hunt(scene)
