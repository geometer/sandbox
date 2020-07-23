# https://www.facebook.com/groups/parmenides52/permalink/3023880614392291/

from sandbox import Scene
from sandbox.property import *
from runner import run_sample

scene = Scene()

A = scene.free_point(label='A')
B = scene.free_point(label='B')
C = scene.free_point(label='C')
D = scene.free_point(label='D')
E = scene.free_point(label='E')
for pt0, pt1 in itertools.combinations((A, B, C, D, E), 2):
    pt0.not_equal_constraint(pt1)
A.segment(E).congruent_constraint(B.segment(E))
A.segment(B).congruent_constraint(A.segment(C))
A.segment(B).congruent_constraint(B.segment(D))
B.opposite_side_constraint(C, A.line_through(E))
A.opposite_side_constraint(D, B.line_through(E))
C.same_side_constraint(E, A.line_through(B))
D.same_side_constraint(E, A.line_through(B))
A.angle(B, E).value_constraint(63)
A.angle(C, E).value_constraint(27)
B.angle(E, D).value_constraint(45)

#M = A.segment(B).middle_point(label='M')
##perp = M.perpendicular_line(A.line_through(B), label='Perp')
##F = perp.intersection_point(D.line_through(A), label='F')
##F = M.line_through(E).intersection_point(D.line_through(A), label='F')
#F = A.line_through(D).free_point(label='F')
#D.angle(A, F).value_constraint(0)
##F.angle(A, D).value_constraint(180)
##A.angle(D, F).value_constraint(0)
#B.segment(D).congruent_constraint(F.segment(D))

def props():
    return (
#        D.angle(F, A),
#        F.angle(A, D),
#        LengthsInequalityProperty(F.segment(D), A.segment(D)),
    #    B.angle(A, D),
    #    D.angle(A, B),
    #    PointOnLineProperty(E, M.segment(F), True),
        PointsCollinearityProperty(C, E, D, True),
    #    A.angle(D, B),
    #    D.angle(A, B),
    #    F.angle(A, B),
    #    A.angle(M, B),
    #    PerpendicularSegmentsProperty(A.segment(M), F.segment(M)),
    #    A.angle(D, F),
    #    D.angle(A, F),
    #    F.angle(A, D),
    #    SameOrOppositeSideProperty(A.segment(B), E, D, same=True),
    #    SameOrOppositeSideProperty(A.segment(B), D, F, same=True),
    #    SameOrOppositeSideProperty(A.segment(B), E, D, same=True),
    #    SameOrOppositeSideProperty(B.segment(D), A, E, same=True),
    #    SameOrOppositeSideProperty(D.segment(E), B, A, same=True),
    #    SameOrOppositeSideProperty(A.segment(E), B, D, same=True),
    #    SameOrOppositeSideProperty(A.segment(D), B, E, same=False),
    #    SameOrOppositeSideProperty(B.segment(E), A, D, same=False),
    #    PointInsideAngleProperty(C, B.angle(A, D)),
    #    SameOrOppositeSideProperty(A.segment(C), M, D, same=True),
    #    E.angle(F, M),
    #    M.angle(E, F),
    #    F.angle(E, M),
    #    A.angle(E, D),
    #    B.angle(A, E),
    #    E.angle(D, F),
    #    ProportionalLengthsProperty(A.segment(F), E.segment(F), 1),
    #    PointsCollinearityProperty(D, E, C, True),
    #    B.angle(A, F),
    #    D.angle(A, B),
    #    PerpendicularSegmentsProperty(M.segment(F), M.segment(B)),
    #    B.angle(D, M),
    #    PointsCoincidenceProperty(D, F, False),
    #    AngleRatioProperty(A.angle(C, F), F.angle(A, M), 1),
    #    AngleRatioProperty(A.angle(C, D), F.angle(A, M), 1),
        #ParallelVectorsProperty(A.vector(C), F.vector(E)),
#        A.vector(C).angle(F.vector(E)),
        #ParallelVectorsProperty(A.vector(C), M.vector(E)),
        #A.vector(C).angle(M.vector(E)),
#        E.angle(F, M),
#        C.vector(A).angle(E.vector(M)),
#        C.vector(A).angle(E.vector(F)),
#        D.angle(A, F),
#        AngleRatioProperty(A.angle(C, D), F.angle(E, D), 1),
#        ConvexQuadrilateralProperty(Scene.Polygon(A, E, D, M)),
    #    AngleRatioProperty(A.angle(C, F), A.angle(C, D), 1),
    #    AngleValueProperty(A.vector(C).angle(F.vector(M)), 180),
    #    AngleValueProperty(A.vector(C).angle(F.vector(E)), 0),
    #    AngleValueProperty(A.vector(C).angle(M.vector(E)), 0),
#        F.angle(E, M),
#        A.angle(B, F),
#        A.angle(E, F),
#        A.angle(B, E),
    #    AngleRatioProperty(A.angle(C, F), F.angle(D, E), 1),
    )
run_sample(scene, props)
