from sandbox import Scene
from sandbox.sketcher import sketch
from sandbox.util import LazyComment

scene = Scene()

A, B, C = scene.triangle(labels=['A', 'B', 'C'])

def napoleonic(A, B, C):
    circleAB = A.circle_through(B, layer='invisible')
    circleBA = B.circle_through(A, layer='invisible')
    V = circleAB.intersection_point(circleBA, label=C.label + '_1')
    A.scene.equilateral_constraint((A, B, V), comment=LazyComment('Given: △ %s %s %s is an equilateral triangle', V, A, B))
    line = A.line_through(B, layer='auxiliary')
    V.opposite_side_constraint(C, line, comment=LazyComment('Given: %s is outward of △ %s %s %s', V, A, B, C))
    D = scene.circumcentre_point((A, B, V), label=C.label + '_2')

napoleonic(A, B, C)
napoleonic(C, A, B)
napoleonic(B, C, A)

sketch(scene)
