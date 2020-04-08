import sys

from runner import run_sample
from sandbox import Scene
from sandbox.property import EquilateralTriangleProperty
from sandbox.util import _comment

scene = Scene(strategy='constraints')

A, B, C = scene.triangle(labels=['A', 'B', 'C'])

def napoleonic(A, B, C):
    V = A.scene.free_point(label=C.label + '1')
    A.scene.equilateral_constraint((A, B, V), comment=_comment('Given: △ %s %s %s is an equilateral triangle', V, A, B))
    line = A.line_through(B, layer='auxiliary')
    V.same_side_constraint(C, line, comment=_comment('Given: %s is inward of △ %s %s %s', V, A, B, C))
    D = scene.incentre_point((A, B, V), label=C.label + '2')

napoleonic(A, B, C)
napoleonic(C, A, B)
napoleonic(B, C, A)

prop = EquilateralTriangleProperty((scene.get('A2'), scene.get('B2'), scene.get('C2')))

run_sample(scene, prop)
