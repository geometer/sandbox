from runner import run_sample
from sandbox import Scene
from sandbox.property import *

scene = Scene()

square = scene.square('A', 'B', 'C', 'D', non_degenerate=True)
A, B, C, D = square.points
E = A.segment(B).free_point(label='E')
F = B.segment(C).free_point(label='F')
G = A.segment(D).middle_point(label='G')
scene.add_property(AngleValueProperty(G.vector(E).angle(D.vector(F)), 0), None)
O = A.line_through(C).intersection_point(B.line_through(D), label='O')
#X = A.segment(B).middle_point(label='X')
Y = B.segment(C).middle_point(label='Y')
Z = E.segment(F).free_point(label='Z')
scene.add_property(PerpendicularSegmentsProperty(O.segment(Z), E.segment(F)), None)
#E1 = G.line_through(E).intersection_point(B.line_through(C), label='E_1')
#F1 = D.line_through(F).intersection_point(A.line_through(B), label='F_1')
H = E.line_through(F).intersection_point(A.line_through(D), label='H')
#H2 = E.line_through(F).intersection_point(C.line_through(D), label='H_2')

def props():
    return (
    #    ProportionalLengthsProperty(O.segment(X), O.segment(Y), 1),
        ProportionalLengthsProperty(O.segment(Y), O.segment(Z), 1),
    #    PointsCollinearityProperty(C, B, X, False),
    #    PointsCollinearityProperty(D, F, X, False),
    #    PointsCoincidenceProperty(B, X, False),
    #    PointsCoincidenceProperty(C, X, False),
    #    PointsCoincidenceProperty(D, X, False),
    #    PointsCoincidenceProperty(F, X, False),
   #     SumOfAnglesProperty(X.angle(F, C), X.angle(B, C), degree=90),
    #    SameOrOppositeSideProperty(C.segment(X), F, B, False),
     #   X.angle(B, F),
    #    PerpendicularSegmentsProperty(B.segment(X), F.segment(X)),
    #    AngleKindProperty(C.angle(E, D), AngleKindProperty.Kind.acute),
    #    PointInsideAngleProperty(E, C.angle(B, D)),
    #    PointInsideTriangleProperty(X, Scene.Triangle(A, C, D)),
    #    X.angle(E, C),
    #    EqualLengthRatiosProperty(F.segment(D), B.segment(C), E.segment(D), C.segment(B)),
    #    EqualLengthRatiosProperty(F.segment(D), B.segment(C), E.segment(D), C.segment(D)),
    )

run_sample(scene, props)
