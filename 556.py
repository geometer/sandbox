#!/var/www/sandbox/virtualenv/bin/python

from sandbox import *
from sandbox.hunter import hunt

scene = Scene()

A = scene.free_point(label='A')
B = scene.free_point(label='B')
C = scene.free_point(label='C')
C.ratio_point(A, 1, 1, label='D')
A.distance_constraint('B', 5)
C.distance_constraint('B', 5)
C.distance_constraint('A', 6)

scene.dump()

placement = iterative_placement(scene)

print('\n')
placement.dump()
print('\n')

print('|A B| = %.5f' % placement.distance('A', 'B'))
print('|B C| = %.5f' % placement.distance('B', 'C'))
print('|A C| = %.5f' % placement.distance('A', 'C'))

hunt(placement)
