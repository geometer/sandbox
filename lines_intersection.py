#!/var/www/sandbox/virtualenv/bin/python

from sandbox import *

scene = Scene()

A = scene.free_point(id='A', x=1, y=1)
B = scene.free_point(id='B', x=5, y=-3)
C = scene.free_point(id='C', x=3, y=10)
D = scene.free_point(id='D', x=4, y=11)
AB = scene.line(A, B)
CD = scene.line(C, D)
scene.intersection_point(AB, CD, id='E')

print(scene)
print(Placement(scene))
