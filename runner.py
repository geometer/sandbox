import sys

from sandbox import iterative_placement
from sandbox.explainer import Explainer
from sandbox.hunter import Hunter
from sandbox.propertyset import PropertySet

def run_sample(scene, prop):
    if '--dump-scene' in sys.argv[1:]:
        scene.dump()

    if '--run-hunter' in sys.argv[1:]:
        placement = iterative_placement(scene)
        hunter = Hunter(placement)
        hunter.hunt()
        properties = hunter.properties
    else:
        properties = []

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
        explainer.dump(properties)
    explainer.stats(properties).dump()
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
