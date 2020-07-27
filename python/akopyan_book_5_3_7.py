from runner import run_sample
from sandbox import Scene
from sandbox.property import *

scene = Scene()

A, B, C, D = scene.square('A', 'B', 'C', 'D', non_degenerate=True).points
A.x = 0
A.y = 0
B.x = 1
B.y = 0
E = scene.free_point(label='E')
E.inside_triangle_constraint(Scene.Triangle(A, C, D))
#E.x = 0.17
#E.y = 0.6
F = scene.free_point(label='F')
F.opposite_side_constraint(C, A.segment(B))
F.opposite_side_constraint(A, C.segment(B))
A.angle(D, E).ratio_constraint(C.angle(B, F), 1)
C.angle(D, E).ratio_constraint(A.angle(B, F), 1)

G = scene.perpendicular_foot_point(E, A.line_through(C), label='G')
E1 = E.symmetric_point(G, label='E_1')

props = lambda: (
#    PointsCollinearityProperty(E, F, E1, True),
#    SumOfAnglesProperty(A.angle(E, F), C.angle(E, F), degree=180),
#    AngleRatioProperty(A.angle(E1, F), C.angle(E1, F), 1),
#    SameCyclicOrderProperty(Cycle(A, B, E1), Cycle(C, B, F)),
#    PerpendicularSegmentsProperty(E.segment(E1), A.segment(C)),
#    PerpendicularSegmentsProperty(C.segment(F), A.segment(E1)),
#    PerpendicularSegmentsProperty(A.segment(F), C.segment(E1)),
#    PerpendicularSegmentsProperty(E1.segment(F), A.segment(C)),
    PerpendicularSegmentsProperty(E.segment(F), A.segment(C)),
#    PerpendicularSegmentsProperty(E.segment(G), A.segment(C)),
#    ProportionalLengthsProperty(E1.segment(A), E.segment(A), 1),
#    PointInsideTriangleProperty(E1, Scene.Triangle(A, C, B)),
#    SameOrOppositeSideProperty(A.segment(C), E, E1, False),
#    SameOrOppositeSideProperty(A.segment(C), B, E1, True),
#    SameOrOppositeSideProperty(A.segment(B), C, E1, True),
#    AnglesInequalityProperty(A.angle(E, C), A.angle(D, C)),
#    AnglesInequalityProperty(A.angle(E1, C), A.angle(B, C)),
)

run_sample(scene, props)
