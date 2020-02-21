#!/var/www/sandbox/virtualenv/bin/python

# Problem 7 from http://zadachi.mccme.ru/2012/

from sandbox import *
from sandbox.hunter import hunt

scene = Scene()

O = scene.free_point(label='O')
circle = O.circle_through(scene.free_point(auxiliary=True))
A = circle.free_point(label='A')
B = circle.free_point(label='B')
C = circle.free_point(label='C')
D = circle.free_point(label='D')
A.constraint(Constraint.Kind.quadrilateral, B, C, D)
A.distance_constraint(B, 3)
B.distance_constraint(C, 4)
C.distance_constraint(D, 5)
A.distance_constraint(D, 2)

scene.dump()

placement = iterative_placement(scene, print_progress=True)

print('|A C| = %.5f' % placement.distance('A', 'C'))

hunt(placement, ['proportional_segments'])
