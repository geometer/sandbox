from runner import run_sample

from sandbox import Scene
from sandbox.property import EquilateralTriangleProperty

scene = Scene()

triangle = scene.nondegenerate_triangle(labels=('A', 'B', 'C'))
A, B, C = triangle.points
A1 = scene.free_point(label='A1')
B1 = scene.free_point(label='B1')
C1 = scene.free_point(label='C1')
A1.inside_triangle_constraint(triangle)
B1.inside_triangle_constraint(triangle)
C1.inside_triangle_constraint(triangle)
angleA = A.angle(B, C)
angleA.ratio_constraint(A.angle(B, C1), 3)
angleA.ratio_constraint(A.angle(C1, B1), 3)
angleA.ratio_constraint(A.angle(B1, C), 3)
angleB = B.angle(A, C)
angleB.ratio_constraint(B.angle(C, A1), 3)
angleB.ratio_constraint(B.angle(A1, C1), 3)
angleB.ratio_constraint(B.angle(C1, A), 3)
angleC = C.angle(A, B)
angleC.ratio_constraint(C.angle(A, B1), 3)
angleC.ratio_constraint(C.angle(B1, A1), 3)
angleC.ratio_constraint(C.angle(A1, B), 3)

#X = scene.perpendicular_foot_point(A1, B.line_through(C), label='X')

prop = EquilateralTriangleProperty((A1, B1, C1))

run_sample(scene, prop)
