#!/var/www/sandbox/virtualenv/bin/python

# Problem 4 from http://zadachi.mccme.ru/2012/

from sandbox import *
from sandbox.placement import PlacementFailedError
from sandbox.hunter import hunt

scene = Scene()

O = scene.free_point(label='O')
B = scene.free_point(label='B')
circle = O.circle_through(B)
scene.constraint(Constraint.Kind.distance, O, B, 11)
P = scene.free_point(label='P')
scene.constraint(Constraint.Kind.distance, O, P, 7)
line = scene.line_through(P)
X0 = line.intersection_point(circle, label='X0')
X1 = line.intersection_point(circle, label='X1')
X1.constraint(Constraint.Kind.not_equal, X0)
scene.constraint(Constraint.Kind.distance, X0, X1, 18)

scene.dump()

placement = iterative_placement(scene, print_progress=True)

print('|P X0| = %.5f' % placement.distance('P', 'X0'))
print('|P X1| = %.5f' % placement.distance('P', 'X1'))
