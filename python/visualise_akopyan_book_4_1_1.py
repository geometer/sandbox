from sandbox import Scene
from sandbox.property import ProportionalLengthsProperty

from visualiser import visualise

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

altitudeC = scene.altitude(triangle, C)
C1 = altitudeC.intersection_point(B.line_through(A), label='C_1')
C2 = altitudeC.intersection_point(circ, label='C_2')
C2.not_equal_constraint(C)

A.angle(B, C).is_acute_constraint()
B.angle(A, C).is_acute_constraint()
C.angle(B, A).is_acute_constraint()

prop = ProportionalLengthsProperty(B1.segment(H), B1.segment(B2), 1)

visualise(scene, prop)
