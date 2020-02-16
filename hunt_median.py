#!/var/www/sandbox/virtualenv/bin/python

from sandbox import *
from sandbox.hunter import hunt

scene = Scene()

A = scene.freePoint(id='A')
B = scene.freePoint(id='B')
C = scene.freePoint(id='C')
M = scene.centrePoint(A, B, id='M')
l = scene.line(C, M)
D = scene.freePoint(line=l, id='D')
E = scene.intersectionPoint(
    scene.circle(centre=D, radius_start=A, radius_end=B),
    scene.circle(centre=B, radius_start=A, radius_end=D)
)

print(scene)

hunt(scene)
