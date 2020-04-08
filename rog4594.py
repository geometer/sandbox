# "Romantics of Geometry" group on Facebook, problem 4594
# https://www.facebook.com/groups/parmenides52/permalink/2784962828284072/

import sys

from sandbox import Scene, iterative_placement
from sandbox.hunter import Hunter
from sandbox.explainer import Explainer
from sandbox.property import LengthRatioProperty
from sandbox.propertyset import PropertySet

scene = Scene()

A, B, C = scene.triangle(labels=('A', 'B', 'C'))
scene.perpendicular_constraint((A, B), (A, C), comment='Given: AB ⟂ AC')
I = scene.incentre_point((A, B, C), label='I')
J = scene.orthocentre_point((A, B, I), label='J')

# Additional constructions
D = A.line_through(B).intersection_point(I.line_through(J), label='D')
E = A.line_through(I).intersection_point(B.line_through(J), label='E')

if '--dump-scene' in sys.argv[1:]:
    scene.dump()

placement = iterative_placement(scene)

hunter = Hunter(placement)
hunter.hunt()
print('')

if '--use-trigonometry' in sys.argv[1:]:
    explainer = Explainer(scene, options={'trigonometry'})
else:
    explainer = Explainer(scene)

if '--profile' in sys.argv[1:]:
    import cProfile
    cProfile.run('explainer.explain()')
else:
    explainer.explain()
if '--dump' in sys.argv[1:]:
    explainer.dump(hunter.properties)
explainer.stats(hunter.properties).dump()

prop = LengthRatioProperty(A.segment(J), B.segment(I), 1)

if explainer.explained(prop):
    print('\tExplained: %s' % prop)
else:
    print('\tNot explained: %s' % prop)

if '--explain' in sys.argv[1:]:
    def dump(prop, level=0):
        print('\t' + '  ' * level + str(prop) + ': ' + ' + '.join([str(com) for com in prop.reason.comments]))
        if prop.reason.premises:
            for premise in prop.reason.premises:
                dump(premise, level + 1)

    def depth(prop):
        if prop.reason.premises:
            return 1 + max(depth(p) for p in prop.reason.premises)
        return 0

    def all_premises(prop):
        premises = PropertySet()
        def collect(p):
            premises.add(p)
            if p.reason.premises:
                for pre in p.reason.premises:
                    collect(pre)
        collect(prop)
        return premises

    explanation = explainer.explanation(prop)
    if explanation:
        dump(explanation)
        print('Depth = %s' % depth(explanation))
        print('Props = %s' % len(all_premises(explanation)))
        all_premises(explanation).stats().dump()
