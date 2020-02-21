#!/var/www/sandbox/virtualenv/bin/python

# Problem 4 from http://zadachi.mccme.ru/2012/

from sandbox import *

scene = Scene()

O = scene.free_point(label='O')
B = scene.free_point(label='B')
circle = O.circle_through(B)
O.distance_constraint(B, 11)
P = scene.free_point(label='P')
O.distance_constraint(P, 7)
line = scene.line_through(P)
X0 = line.intersection_point(circle, label='X0')
X1 = line.intersection_point(circle, label='X1')
X0.distance_constraint(X1, 18)

scene.dump()

placement = iterative_placement(scene, print_progress=True)

print('|P X0| = %.5f' % placement.distance('P', 'X0'))
print('|P X1| = %.5f' % placement.distance('P', 'X1'))
