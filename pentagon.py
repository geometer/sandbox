import math

from sandbox import Scene, iterative_placement

scene = Scene()

A = scene.free_point(label='A')
B = scene.free_point(label='B')
C = scene.free_point(label='C')
D = scene.free_point(label='D')
E = scene.free_point(label='E')
scene.convex_polygon_constraint(A, B, C, D, E)
scene.equal_distances_constraint((A, B), (B, C))
scene.equal_distances_constraint((A, B), (C, D))
scene.equal_distances_constraint((A, B), (D, E))
scene.equal_distances_constraint((A, B), (E, A))
scene.equal_distances_constraint((A, C), (B, D))
scene.equal_distances_constraint((A, C), (C, E))
scene.equal_distances_constraint((A, C), (D, A))
scene.equal_distances_constraint((A, C), (E, B))

placement = iterative_placement(scene, print_progress=True)

placement.dump()

print('∠ A B C = %.5f' % (placement.angle(B, A, B, C) / math.pi * 180))
print('|A B| = %.5f' % placement.distance(A, B))
print('|A C| = %.5f' % placement.distance(A, C))
