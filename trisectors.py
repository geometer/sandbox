from sandbox import *
from sandbox.hunter import Hunter

scene = Scene()

A = scene.free_point(label='A')
B = scene.free_point(label='B')
C = scene.free_point(label='C')
A1 = scene.free_point(label='A1')
#A1.inside_triangle_constraint(A, B, C)
B1 = scene.free_point(label='B1')
#B1.inside_triangle_constraint(A, B, C)
C1 = scene.free_point(label='C1')
#C1.inside_triangle_constraint(A, B, C)
A.angle(B, C).ratio_constraint(A.angle(B, C1), 3)
A.angle(B, C).ratio_constraint(A.angle(B1, C), 3)
B.angle(C, A).ratio_constraint(B.angle(C, A1), 3)
B.angle(C, A).ratio_constraint(B.angle(C1, A), 3)
C.angle(A, B).ratio_constraint(C.angle(A, B1), 3)
C.angle(A, B).ratio_constraint(C.angle(A1, B), 3)

placement = iterative_placement(scene, print_progress=True)

placement.dump()

print('∠ C B A1 = %.5f' % placement.angle(B.angle(C, A1)))
print('∠ C B A = %.5f' % placement.angle(B.angle(C, A)))
helper = PlacementHelper(placement)
print('|A1 B1| = %.5f' % helper.distance(A1, B1))
print('|A1 C1| = %.5f' % helper.distance(A1, C1))
print('|C1 B1| = %.5f' % helper.distance(C1, B1))

hunter = Hunter(placement)
hunter.hunt()
hunter.dump()
