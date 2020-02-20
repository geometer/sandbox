#!/var/www/sandbox/virtualenv/bin/python

# Problem 7 from http://zadachi.mccme.ru/2012/

from sandbox import *
from sandbox.placement import PlacementFailedError
from sandbox.hunter import hunt

scene = Scene()

O = scene.free_point(label='O', x=0, y=0)
A = scene.free_point(label='A')
circle = O.circle_through(A)
B = circle.free_point(label='B')
C = circle.free_point(label='C')
D = circle.free_point(label='D')
scene.constraint(Constraint.Kind.quadrilateral, A, B, C, D)
scene.constraint(Constraint.Kind.distance, A, B, 3)
scene.constraint(Constraint.Kind.distance, B, C, 4)
scene.constraint(Constraint.Kind.distance, C, D, 5)
scene.constraint(Constraint.Kind.distance, A, D, 2)

scene.dump()

placement = iterative_placement(scene, print_progress=True)

print('|O A| = %.5f' % placement.distance('O', 'A'))
print('|A C| = %.5f' % placement.distance('A', 'C'))

hunt(placement, ['proportional_segments'])
