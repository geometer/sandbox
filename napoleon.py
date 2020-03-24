#!/var/www/sandbox/virtualenv/bin/python

from sandbox import Scene
from sandbox.hunter import Hunter
from sandbox.explainer import Explainer
from sandbox.util import _comment

scene = Scene()

A, B, C = scene.triangle(labels=['A', 'B', 'C'])

def napoleonic(A: Scene.Point, B: Scene.Point, C: Scene.Point):
    V = A.circle_through(B).intersection_point(B.circle_through(A), label=C.label + '1')
    line = A.line_through(B, auxiliary=True)
    V.opposite_side_constraint(C, line, comment=_comment('Given: %s is outward of △ %s %s %s', V, A, B, C))
    D = scene.gravity_centre_point(A, B, V, label=C.label + '2')
    #D = scene.free_point(label=C.label + '2')
    segmentA = A.segment(D)
    segmentB = B.segment(D)
    segmentV = V.segment(D)
    segmentA.congruent_constraint(segmentB)
    segmentA.congruent_constraint(segmentV)
    D.inside_triangle_constraint(A, B, V)

napoleonic(A, B, C)
napoleonic(C, A, B)
napoleonic(B, C, A)

hunter = Hunter(scene)
hunter.hunt()

angle = scene.get('A2').angle(scene.get('B2'), scene.get('C2'))

explainer = Explainer(scene, hunter.properties)
print('\tGuessed: %s = %s' % (angle, explainer.guessed(angle)))

explainer.explain()
explainer.dump()
explainer.stats().dump()
print('\tExplained: %s = %s' % (angle, explainer.explained(angle)))
