from sandbox import Scene
from sandbox.hunter import Hunter

scene = Scene()

A = scene.free_point(label='A')
B = scene.free_point(label='B')
c0 = A.circle_through(B)
c1 = B.circle_through(A)
C = c0.intersection_point(c1, label='C')
scene.centroid_point((A, B, C), label='D')
A.segment(B).middle_point(label='E')

hunter = Hunter(scene)
hunter.hunt()
hunter.dump()
