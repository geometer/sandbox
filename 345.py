#!/var/www/sandbox/virtualenv/bin/python

from sandbox import *
from sandbox.hunter import hunt

scene = Scene()

A = scene.free_point(label='A')
B = scene.free_point(label='B')
C = scene.free_point(label='C')
A.distance_constraint('B', 5)
C.distance_constraint('B', 4)
C.distance_constraint('A', 3)

scene.dump()

placement = iterative_placement(scene)

print('\n')
placement.dump()
print('\n')

print('|A B| = %.5f' % placement.distance('A', 'B'))
print('|B C| = %.5f' % placement.distance('B', 'C'))
print('|A C| = %.5f' % placement.distance('A', 'C'))
