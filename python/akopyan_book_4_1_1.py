from runner import run_sample
from sandbox import Scene
from sandbox.property import AngleRatioProperty, ProportionalLengthsProperty

scene = Scene()

triangle = scene.nondegenerate_triangle(labels=('A', 'B', 'C'))
A, B, C = triangle.points
circ = scene.circumcircle(triangle)
H = scene.orthocentre_point(triangle, label='H')

altitudeA = scene.altitude(triangle, A)
A1 = altitudeA.intersection_point(B.line_through(C), label='A_1')
A2 = altitudeA.intersection_point(circ, label='A_2')
A2.not_equal_constraint(A)

altitudeB = scene.altitude(triangle, B)
B1 = altitudeB.intersection_point(A.line_through(C), label='B_1')
B2 = altitudeB.intersection_point(circ, label='B_2')
B2.not_equal_constraint(B)
#B2.opposite_side_constraint(B, A.line_through(C))

altitudeC = scene.altitude(triangle, C)
C1 = altitudeC.intersection_point(B.line_through(A), label='C_1')
C2 = altitudeC.intersection_point(circ, label='C_2')
C2.not_equal_constraint(C)

A.angle(B, C).is_acute_constraint()
B.angle(A, C).is_acute_constraint()
C.angle(B, A).is_acute_constraint()

props = (
    AngleRatioProperty(B.angle(B1, C), A.angle(B1, B2), 1),
    AngleRatioProperty(A.angle(B1, H), B.angle(B1, C), 1),
    AngleRatioProperty(A.angle(B1, H), A.angle(B1, B2), 1),
    ProportionalLengthsProperty(B1.segment(H), B1.segment(B2), 1),
)

run_sample(scene, *props)
