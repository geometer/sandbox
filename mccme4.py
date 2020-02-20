#!/var/www/sandbox/virtualenv/bin/python

# Task 4 from http://zadachi.mccme.ru/2012/

from sys import stdout

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
line = P.line_through(scene.free_point())
X0 = line.intersection_point(circle, label='X0')
X1 = line.intersection_point(circle, label='X1')
X1.constraint(Constraint.Kind.not_equal, X0)
scene.constraint(Constraint.Kind.distance, X0, X1, 18)

while True:
    try:
        placement = Placement(scene)
        for index in range(0, 400):
            if index % 10 == 0:
                stdout.write('Deviation on step %d: %.7f\r' % (index, placement.deviation()))
                stdout.flush()
            new_placement = placement.iterate()
            if new_placement == placement:
                print('Deviation on step %d: %.7f' % (index, placement.deviation()))
                break
            placement = new_placement
        if placement.deviation() < 1e-6:
            break
    except PlacementFailedError as e:
        print(e)

print('|P X0| = %.5f' % placement.distance('P', 'X0'))
print('|P X1| = %.5f' % placement.distance('P', 'X1'))
