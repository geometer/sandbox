#!/var/www/sandbox/virtualenv/bin/python

from sandbox import *
from sandbox.hunter import hunt

scene = Scene()

O = FreePoint(scene, id='O')
A = FreePoint(scene, id='A')
c = Circle(centre=O, point=A)
B = FreePointOnCircle(c, id='B')
C = FreePointOnCircle(c, id='C')

hunt(scene)
