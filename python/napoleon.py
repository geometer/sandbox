from runner import run_sample
from sandbox import Scene
from sandbox.property import EquilateralTriangleProperty
from sandbox.util import LazyComment

scene = Scene()

triangle = scene.nondegenerate_triangle(labels=['A', 'B', 'C'])
A, B, C = triangle.points

def napoleonic(A, B, C):
    # Change to True, if you want to construct the point explicitly.
    # This change does not affect the explanation but makes placement a little bit quicker.
    # Not a matter for the sample, but for more complicated construction this might be useful
    # if you want to run the hunter.
    constructive = False

    label = '%s_1' % C.label
    comment = LazyComment('Third vertex of equilateral triangle with base %s', A.segment(B))
    if constructive:
        circleAB = A.circle_through(B, layer='invisible')
        circleBA = B.circle_through(A, layer='invisible')
        V = circleAB.intersection_point(circleBA, label=label, comment=comment)
    else:
        V = A.scene.free_point(label=label, comment=comment)
    equialteral = Scene.Triangle((A, B, V))
    A.scene.equilateral_constraint(equialteral, comment=LazyComment('given: %s is equilateral', equialteral))
    line = A.line_through(B, layer='auxiliary')
    V.opposite_side_constraint(C, line, comment=LazyComment('given: %s is outward of %s', V, triangle))
    D = scene.incentre_point(equialteral, label='%s_2' % C.label, comment=LazyComment('Centre of %s', equialteral))

napoleonic(A, B, C)
napoleonic(C, A, B)
napoleonic(B, C, A)

prop = EquilateralTriangleProperty((scene.get('A_2'), scene.get('B_2'), scene.get('C_2')))

run_sample(scene, prop)
