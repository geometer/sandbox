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
scene.angles_ratio_constraint(((B, C), (B, A)), ((B, C), (B, A1)), 3)
scene.angles_ratio_constraint(((C, A), (C, B)), ((C, A1), (C, B)), 3)
scene.angles_ratio_constraint(((C, A), (C, B)), ((C, A), (C, B1)), 3)
scene.angles_ratio_constraint(((A, B), (A, C)), ((A, B1), (A, C)), 3)
scene.angles_ratio_constraint(((A, B), (A, C)), ((A, B), (A, C1)), 3)
scene.angles_ratio_constraint(((B, C), (B, A)), ((B, C1), (B, A)), 3)

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
