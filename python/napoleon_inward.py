import sys

from runner import run_sample
from sandbox import Scene
from sandbox.property import EquilateralTriangleProperty
from sandbox.util import Comment

scene = Scene()

triangle = scene.nondegenerate_triangle(labels=('A', 'B', 'C'))
A, B, C = triangle.points

def napoleonic(A, B, C):
    equilateral = scene.equilateral_triangle(A, B, '%s_1' % C.label)
    _, _, C1 = equilateral.points
    C1.comment = Comment('Third vertex of equilateral triangle with base $%{segment:AB}$', {'AB': A.segment(B)})
    line = A.line_through(B, layer='auxiliary')
    comment = Comment('$%{triangle:equilateral}$ is facing into $%{triangle:triangle}$', {'equilateral': equilateral, 'triangle': triangle})
    C1.same_side_constraint(C, line, comment=comment)
    D = scene.centre_point(equilateral, label='%s_2' % C.label)

napoleonic(A, B, C)
napoleonic(C, A, B)
napoleonic(B, C, A)

prop = EquilateralTriangleProperty((scene.get('A_2'), scene.get('B_2'), scene.get('C_2')))

run_sample(scene, prop)
