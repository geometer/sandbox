import sys

from runner import run_sample
from sandbox import Scene
from sandbox.property import EquilateralTriangleProperty
from sandbox.util import LazyComment

scene = Scene()

triangle = scene.nondegenerate_triangle(labels=('A', 'B', 'C'))
A, B, C = triangle.points

def napoleonic(A, B, C):
    circleAB = A.circle_through(B, layer='invisible')
    circleBA = B.circle_through(A, layer='invisible')
    V = circleAB.intersection_point(circleBA, label=C.label + '1')
    equilateral = Scene.Triangle((A, B, V))
    A.scene.equilateral_constraint(equilateral, comment=LazyComment('Given: %s is equilateral', equilateral))
    line = A.line_through(B)
    V.opposite_side_constraint(C, line, comment=LazyComment('Given: %s is outward of %s', V, triangle))
    D = scene.circumcentre_point(equilateral, label=C.label + '2')

napoleonic(A, B, C)
napoleonic(C, A, B)
napoleonic(B, C, A)

prop = EquilateralTriangleProperty((scene.get('A2'), scene.get('B2'), scene.get('C2')))

run_sample(scene, prop)
