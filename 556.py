#!/var/www/sandbox/virtualenv/bin/python

from sandbox import *
from sandbox.hunter import hunt

scene = Scene()

A = scene.free_point(label='A')
scene.free_point(label='B')
scene.free_point(label='C').ratio_point(A, 1, 1, label='D')
scene.constraint(Constraint.Kind.distance, 'A', 'B', 5)
scene.constraint(Constraint.Kind.distance, 'C', 'B', 5)
scene.constraint(Constraint.Kind.distance, 'C', 'A', 6)

scene.dump()

placement = Placement(scene)

for index in range(0, 10000):
    print('Deviation %d: %.7f' % (index, placement.deviation()))
    new_placement = placement.iterate()
    if new_placement == placement:
        break
    placement = new_placement

print('\n')
placement.dump()
print('\n')

print('|A B| = %.5f' % placement.distance('A', 'B'))
print('|B C| = %.5f' % placement.distance('B', 'C'))
print('|A C| = %.5f' % placement.distance('A', 'C'))

hunt(placement)
