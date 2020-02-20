#!/var/www/sandbox/virtualenv/bin/python

# Problem 7 from http://zadachi.mccme.ru/2012/

from sandbox import *
from sandbox.placement import PlacementFailedError
from sandbox.hunter import hunt

scene = Scene()

O = scene.free_point(label='O')
circle = O.circle_through(scene.free_point(auxiliary=True))
A = circle.free_point(label='A')
B = circle.free_point(label='B')
C = circle.free_point(label='C')
D = circle.free_point(label='D')
A.constraint(Constraint.Kind.quadrilateral, B, C, D)
A.constraint(Constraint.Kind.distance, B, 3)
B.constraint(Constraint.Kind.distance, C, 4)
C.constraint(Constraint.Kind.distance, D, 5)
A.constraint(Constraint.Kind.distance, D, 2)

scene.dump()

placement = iterative_placement(scene, print_progress=True)

print('|A C| = %.5f' % placement.distance('A', 'C'))

hunt(placement, ['proportional_segments'])
