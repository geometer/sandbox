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

print(scene)
print('\n'.join([str(cnstr) for cnstr in scene.constraints]))

placement = Placement(scene)

for index in range(0, 10000):
    print('Deviation %d: %.12f' % (index, placement.deviation()))
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
