#!/var/www/sandbox/virtualenv/bin/python

from sandbox import Scene
from sandbox.hunter import Hunter
from sandbox.explainer import Explainer
from sandbox.util import _comment

scene = Scene()

A, B, C = scene.triangle(labels=['A', 'B', 'C'])

def napoleonic(A: Scene.Point, B: Scene.Point, C: Scene.Point):
    V = A.scene.free_point(label=C.label + '1')
    A.scene.is_equilateral_constraint((A, B, V), comment=_comment('Given: △ %s %s %s is equilateral', A, B, V))
    line = A.line_through(B, auxiliary=True)
    V.opposite_side_constraint(C, line, comment=_comment('Given: %s is outward of △ %s %s %s', V, A, B, C))
    scene.gravity_centre_point(A, B, V, label=C.label + '2')

napoleonic(A, B, C)
napoleonic(C, A, B)
napoleonic(B, C, A)

hunter = Hunter(scene)
hunter.hunt()

angle = scene.get('A2').angle(scene.get('B2'), scene.get('C2'))

explainer = Explainer(scene, hunter.properties)
print('\tGuessed: %s = %s' % (angle, explainer.guessed(angle)))

explainer.explain()
explainer.stats().dump()
print('\tExplained: %s = %s' % (angle, explainer.explained(angle)))
