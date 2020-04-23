from sandbox import Scene
from sandbox.property import EquilateralTriangleProperty
from sketcher import sketch

scene = Scene()

A, B, C = scene.nondegenerate_triangle(labels=('A', 'B', 'C')).points
A1 = scene.free_point(label='A_1')
B1 = scene.free_point(label='B_1')
C1 = scene.free_point(label='C_1')
angleA = A.angle(B, C)
angleA.ratio_constraint(A.angle(B, C1), 3)
angleA.ratio_constraint(A.angle(C1, B1), 3)
angleA.ratio_constraint(A.angle(B1, C), 3)
B1.inside_constraint(angleA)
C1.inside_constraint(angleA)
angleB = B.angle(A, C)
angleB.ratio_constraint(B.angle(C, A1), 3)
angleB.ratio_constraint(B.angle(A1, C1), 3)
angleB.ratio_constraint(B.angle(C1, A), 3)
A1.inside_constraint(angleB)
C1.inside_constraint(angleB)
angleC = C.angle(A, B)
angleC.ratio_constraint(C.angle(A, B1), 3)
angleC.ratio_constraint(C.angle(B1, A1), 3)
angleC.ratio_constraint(C.angle(A1, B), 3)
A1.inside_constraint(angleC)
B1.inside_constraint(angleC)

A.line_through(B)
A.line_through(C)
B.line_through(C)

A.line_through(B1)
A.line_through(C1)
B.line_through(A1)
B.line_through(C1)
C.line_through(A1)
C.line_through(B1)

A1.line_through(B1)
A1.line_through(C1)
B1.line_through(C1)

sketch(scene)
