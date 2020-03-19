#!/var/www/sandbox/virtualenv/bin/python

from sandbox import Scene
from sandbox.hunter import Hunter
from sandbox.explainer import Explainer

scene = Scene()

A, B, C = scene.triangle(labels=['A', 'B', 'C'])

def napoleonic(A: Scene.Point, B: Scene.Point, C: Scene.Point):
    c0 = A.circle_through(B)
    c1 = B.circle_through(A)
    line = A.line_through(B, auxiliary=True)
    V = c0.intersection_point(c1, label=C.label + '1')
    V.opposite_side_constraint(C, line)
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
