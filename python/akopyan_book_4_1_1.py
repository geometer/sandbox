from runner import run_sample
from sandbox import Scene
from sandbox.property import *

scene = Scene()

triangle = scene.nondegenerate_triangle(labels=('A', 'B', 'C'))
A, B, C = triangle.points
H = scene.orthocentre_point(triangle, label='H')

altitudeA = scene.altitude(triangle, A)
A1 = altitudeA.intersection_point(B.line_through(C), label='A_1')
A2 = H.symmetric_point(A1, label='A_2')

altitudeB = scene.altitude(triangle, B)
B1 = altitudeB.intersection_point(A.line_through(C), label='B_1')
B2 = H.symmetric_point(B1, label='B_2')

altitudeC = scene.altitude(triangle, C)
C1 = altitudeC.intersection_point(B.line_through(A), label='C_1')
C2 = H.symmetric_point(C1, label='C_2')

#A.angle(B, C).is_obtuse_constraint()
#A.angle(B, C).is_right_constraint()
A.angle(B, C).is_acute_constraint(comment='assumption')
B.angle(A, C).is_acute_constraint(comment='assumption')
C.angle(B, A).is_acute_constraint(comment='assumption')

props = (
    ConcyclicPointsProperty(A, B, C, A2),
)

run_sample(scene, *props)
