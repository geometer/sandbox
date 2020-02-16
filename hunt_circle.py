#!/var/www/sandbox/virtualenv/bin/python

from sandbox import *
from sandbox.hunter import hunt

scene = Scene()

O = scene.freePoint(id='O')
A = scene.freePoint(id='A')
c = scene.circle(centre=O, point=A)
B = scene.freePoint(circle=c, id='B')
C = scene.freePoint(circle=c, id='C')

hunt(scene)
