from sandbox import Scene
from sandbox.util import LazyComment
from sandbox.property import EquilateralTriangleProperty
from visualiser import visualise

scene = Scene()

triangle = scene.nondegenerate_triangle(labels=['A', 'B', 'C'])
A, B, C = triangle.points

def napoleonic(A, B, C):
    circleAB = A.circle_through(B, layer='invisible')
    circleBA = B.circle_through(A, layer='invisible')
    V = circleAB.intersection_point(circleBA, label=C.label + '_1')
    equilateral = Scene.Triangle(A, B, V)
    A.scene.equilateral_constraint(equilateral, comment=LazyComment('Given: %s is equilateral', equilateral))
    line = A.line_through(B, layer='auxiliary')
    V.opposite_side_constraint(C, line, comment=LazyComment('Given: %s is outward of %s', V, triangle))
    D = scene.circumcentre_point(equilateral, label=C.label + '_2')

napoleonic(A, B, C)
napoleonic(C, A, B)
napoleonic(B, C, A)

prop = EquilateralTriangleProperty((scene.get('A_2'), scene.get('B_2'), scene.get('C_2')))

visualise(scene, prop)
