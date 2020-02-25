# https://www.facebook.com/groups/parmenides52/, problem 4594

from sandbox import Scene, iterative_placement
from sandbox.hunter import Hunter

scene = Scene()

A = scene.free_point(label='A')
B = scene.free_point(label='B')
C = scene.free_point(label='C')
I = scene.incentre_point(A, B, C, label='I')
J = scene.orthocentre_point(A, B, I, label='J')
scene.right_angle_constraint((A, B), (A, C))

placement = iterative_placement(scene)

hunter = Hunter(placement)
hunter.hunt(['collinears', 'equal_triangles', 'right_angles', 'equal_segments', 'equal_angles', 'similar_triangles'])
print('')
hunter.dump()

print('|%s%s| = %.5f' % (A.label, J.label, placement.distance(A, J)))
print('|%s%s| = %.5f' % (B.label, I.label, placement.distance(B, I)))
