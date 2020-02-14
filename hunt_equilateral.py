#!/var/www/sandbox/virtualenv/bin/python

from sandbox import *
from sandbox.hunter import hunt

scene = Scene()

A = FreePoint(scene, id='A')
B = FreePoint(scene, id='B')
c0 = Circle(centre=A, point=B)
c1 = Circle(centre=B, point=A)
C = CirclesIntersection(c0, c1, id='C')
CentrePoint([A, B, C], id='D')
CentrePoint([A, B], id='E')

hunt(scene)
