from runner import run_sample
from sandbox import Scene
from sandbox.property import *

scene = Scene()

square = scene.square('A', 'B', 'C', 'D', non_degenerate=True)
A, B, C, D = square.points
E = B.segment(C).free_point(label='E')
small = scene.square(B, E, 'F', 'K')
_, _, F, K = small.points
B.inside_constraint(A.segment(K))
N = A.line_through(C).intersection_point(E.line_through(K), label='N')
M = A.line_through(E).intersection_point(C.line_through(K), label='M')

prop = lambda: (
#    A.vector(D).angle(B.vector(C)),
#    A.vector(D).angle(B.vector(E)),
#    A.vector(D).angle(K.vector(F)),
#    SameOrOppositeSideProperty(K.segment(F), A, D, True),
#    SameOrOppositeSideProperty(D.segment(F), C, K, False),
#    SameCyclicOrderProperty(Cycle(D, F, C), Cycle(K, F, D)),
    MultiPointsCollinearityProperty(D, N, M, F),
)

run_sample(scene, prop)
