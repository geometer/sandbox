from runner import run_sample
from sandbox import Scene
from sandbox.property import EquilateralTriangleProperty
from sandbox.util import Comment

scene = Scene()

triangle = scene.nondegenerate_triangle(labels=['A', 'B', 'C'])
A, B, C = triangle.points

def napoleonic(A, B, C):
    equilateral = scene.equilateral_triangle(A, B, '%s_1' % C.label)
    _, _, C1 = equilateral.points
    C1.comment = Comment('Third vertex of equilateral triangle with base $%{segment:AB}$', {'AB': A.segment(B)})
    comment = Comment('$%{triangle:equilateral}$ is facing away from $%{triangle:triangle}$', {'equilateral': equilateral, 'triangle': triangle})
    C1.opposite_side_constraint(C, A.segment(B), comment=comment)
    D = scene.centre_point(equilateral, label='%s_2' % C.label)

napoleonic(A, B, C)
napoleonic(C, A, B)
napoleonic(B, C, A)

def props():
    return EquilateralTriangleProperty((scene.get('A_2'), scene.get('B_2'), scene.get('C_2'))),

run_sample(scene, props)
