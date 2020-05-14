from runner import run_sample
from sandbox import Scene
from sandbox.property import PointsCollinearityProperty

scene = Scene()

A, B, C, D = scene.square('A', 'B', 'C', 'D')
E = B.segment(C).free_point(label='E')
B, E, F, K = scene.square(B, E, 'F', 'K')
B.inside_constraint(A.segment(K))
N = A.line_through(C).intersection_point(E.line_through(K), label='N')

prop = PointsCollinearityProperty(D, N, F, True)

run_sample(scene, prop)
