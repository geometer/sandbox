#!/var/www/sandbox/virtualenv/bin/python

from sandbox import *
from sandbox.hunter import hunt

scene = Scene()

A = scene.freePoint(id='A')
B = scene.freePoint(id='B')
c0 = scene.circle(centre=A, point=B)
c1 = scene.circle(centre=B, point=A)
C = scene.intersectionPoint(c0, c1, id='C')
scene.centrePoint(A, B, C, id='D')
scene.centrePoint(A, B, id='E')

hunt(scene)
