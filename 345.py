#!/var/www/sandbox/virtualenv/bin/python

from sandbox import *
from sandbox.hunter import hunt

scene = Scene()

scene.free_point(label='A')
scene.free_point(label='B')
scene.free_point(label='C')
scene.constraint(Constraint.Kind.distance, 'A', 'B', 5)
scene.constraint(Constraint.Kind.distance, 'C', 'B', 4)
scene.constraint(Constraint.Kind.distance, 'C', 'A', 3)

scene.dump()

placement = iterative_placement(scene)

print('\n')
placement.dump()
print('\n')

print('|A B| = %.5f' % placement.distance('A', 'B'))
print('|B C| = %.5f' % placement.distance('B', 'C'))
print('|A C| = %.5f' % placement.distance('A', 'C'))
