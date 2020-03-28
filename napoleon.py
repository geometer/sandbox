#!/var/www/sandbox/virtualenv/bin/python

import sys

from sandbox import Scene
from sandbox.hunter import Hunter
from sandbox.explainer import Explainer
from sandbox.util import _comment

scene = Scene()

A, B, C = scene.triangle(labels=['A', 'B', 'C'])

def napoleonic(A: Scene.Point, B: Scene.Point, C: Scene.Point):
    V = A.circle_through(B).intersection_point(B.circle_through(A), label=C.label + '1')
    line = A.line_through(B, layer='auxiliary')
    V.opposite_side_constraint(C, line, comment=_comment('Given: %s is outward of △ %s %s %s', V, A, B, C))
    D = scene.incentre_point((A, B, V), label=C.label + '2')

napoleonic(A, B, C)
napoleonic(C, A, B)
napoleonic(B, C, A)

hunter = Hunter(scene)
hunter.hunt()

angle = scene.get('A2').angle(scene.get('B2'), scene.get('C2'))

explainer = Explainer(scene, hunter.properties)
print('\tGuessed: %s = %s' % (angle, explainer.guessed(angle)))

if '--profile' in sys.argv[1:]:
    import cProfile
    cProfile.run('explainer.explain()')
else:
    explainer.explain()
if '--dump' in sys.argv[1:]:
    explainer.dump()
explainer.stats().dump()
print('\tExplained: %s = %s' % (angle, explainer.explained(angle)))

if '--explain' in sys.argv[1:]:
    def dump(prop, level=0):
        print('\t' + '  ' * level + str(prop) + ': ' + ' + '.join([str(com) for com in prop.reason.comments]))
        if prop.reason.premises:
            for premise in prop.reason.premises:
                dump(premise, level + 1)

    explanation = explainer.explanation(angle)
    if explanation:
        dump(explanation)
