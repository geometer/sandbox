#!/var/www/sandbox/virtualenv/bin/python

import math

from sandbox import *

scene = Scene()

#A = FreePoint(scene, id='A', x=0, y=0)
#B = FreePoint(scene, id='B', x=0, y=100)
#C = FreePoint(scene, id='C', x=50, y=50)
A = scene.freePoint(id='A')
B = scene.freePoint(id='B')
C = scene.freePoint(id='C')

def napoleonic(A: Scene.Point, B: Scene.Point, C: Scene.Point):
    c0 = scene.circle(centre=A, point=B)
    c1 = scene.circle(centre=B, point=A)
    V = scene.intersectionPoint(c0, c1, id=C.id + '1')
    V.add_constraint(OppositeSideConstraint(C, V, A, B))
    scene.centrePoint(A, B, V, id=C.id + '2')

napoleonic(A, B, C)
napoleonic(C, A, B)
napoleonic(B, C, A)

print(scene)

placement = Placement(scene)
for p in scene.points:
    print('%s => %s' % (p.id, placement.location(p)))

#print('|A B| = %.5f' % placement.distance('A', 'B'))
#print('|A C1| = %.5f' % placement.distance('A', 'C1'))
#print('|B C1| = %.5f' % placement.distance('B', 'C1'))

#print('|A C2| = %.5f' % placement.distance('A', 'C2'))
#print('|B C2| = %.5f' % placement.distance('B', 'C2'))
#print('|C1 C2| = %.5f' % placement.distance('C1', 'C2'))

#print('|A C| = %.5f' % placement.distance('A', 'C'))
#print('|A B1| = %.5f' % placement.distance('A', 'B1'))
#print('|C B1| = %.5f' % placement.distance('C', 'B1'))

#print('|A B2| = %.5f' % placement.distance('A', 'B2'))
#print('|C B2| = %.5f' % placement.distance('C', 'B2'))
#print('|B1 B2| = %.5f' % placement.distance('B1', 'B2'))

print('|A2 B2| = %.5f' % placement.distance('A2', 'B2'))
print('|A2 C2| = %.5f' % placement.distance('A2', 'C2'))
print('|B2 C2| = %.5f' % placement.distance('B2', 'C2'))
print('|A A1| / sqrt(3) = %.5f' % (placement.distance('A', 'A1') / math.sqrt(3)))
print('angle between AA1 and B2A2 = %.5f degrees' % (placement.angle('A', 'A1', 'B2', 'A2') / math.pi * 180))
