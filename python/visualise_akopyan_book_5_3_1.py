from sandbox import Scene
from sandbox.property import PointsCollinearityProperty

from visualiser import visualise

scene = Scene()

A, B, C, D = scene.square('A', 'B', 'C', 'D')
A.x = 0
A.y = 0
B.x = 1
B.y = 0
E = B.segment(C).free_point(label='E')
B, E, F, K = scene.square(B, E, 'F', 'K')
B.inside_constraint(A.segment(K))
N = A.line_through(C).intersection_point(E.line_through(K), label='N')

D.line_through(N)
N.line_through(F)

prop = PointsCollinearityProperty(D, N, F, True)

visualise(scene, prop)
