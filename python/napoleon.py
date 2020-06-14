from runner import run_sample
from sandbox import Scene
from sandbox.property import EquilateralTriangleProperty
from sandbox.util import LazyComment

scene = Scene()

triangle = scene.nondegenerate_triangle(labels=['A', 'B', 'C'])
A, B, C = triangle.points

def napoleonic(A, B, C):
    equilateral = scene.equilateral_triangle(A, B, '%s_1' % C.label)
    _, _, C1 = equilateral.points
    C1.comment = LazyComment('Third vertex of equilateral triangle with base %s', A.segment(B))
    line = A.line_through(B, layer='auxiliary')
    C1.opposite_side_constraint(C, line, comment=LazyComment('%s is outward of %s', C1, triangle))
    D = scene.centre_point(equilateral, label='%s_2' % C.label)

napoleonic(A, B, C)
napoleonic(C, A, B)
napoleonic(B, C, A)

prop = EquilateralTriangleProperty((scene.get('A_2'), scene.get('B_2'), scene.get('C_2')))

run_sample(scene, prop)
