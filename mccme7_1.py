#!/var/www/sandbox/virtualenv/bin/python

# Task 7 from http://zadachi.mccme.ru/2012/

from sys import stdout

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
D.constraint(Constraint.Kind.quadrilateral, A, B, C)
scene.constraint(Constraint.Kind.distance, A, B, 3)
scene.constraint(Constraint.Kind.distance, B, C, 4)
scene.constraint(Constraint.Kind.distance, C, D, 5)
scene.constraint(Constraint.Kind.distance, A, D, 2)

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

print('|O A| = %.5f' % placement.distance('O', 'A'))
print('|A C| = %.5f' % placement.distance('A', 'C'))

hunt(placement, ['proportional_segments'])
