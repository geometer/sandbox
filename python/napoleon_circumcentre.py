import sys

from runner import run_sample
from sandbox import Scene
from sandbox.property import EquilateralTriangleProperty
from sandbox.util import LazyComment

#scene = Scene(strategy='constraints')
scene = Scene()

A, B, C = scene.triangle(labels=['A', 'B', 'C'])

def napoleonic(A, B, C):
    V = A.scene.free_point(label=C.label + '1')
    A.scene.equilateral_constraint((A, B, V), comment=LazyComment('Given: △ %s %s %s is an equilateral triangle', V, A, B))
    line = A.line_through(B)
    V.opposite_side_constraint(C, line, comment=LazyComment('Given: %s is outward of △ %s %s %s', V, A, B, C))
    D = scene.circumcentre_point((A, B, V), label=C.label + '2')

napoleonic(A, B, C)
napoleonic(C, A, B)
napoleonic(B, C, A)

prop = EquilateralTriangleProperty((scene.get('A2'), scene.get('B2'), scene.get('C2')))

run_sample(scene, prop)
