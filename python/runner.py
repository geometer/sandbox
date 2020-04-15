import sys

from sandbox import iterative_placement
from sandbox.explainer import Explainer
from sandbox.hunter import Hunter
from sandbox.propertyset import PropertySet

def run_sample(scene, prop=None):
    if '--dump-scene' in sys.argv[1:]:
        scene.dump()

    if '--run-hunter' in sys.argv[1:]:
        placement = iterative_placement(scene)
        hunter = Hunter(placement)
        hunter.hunt()
        properties = hunter.properties
    else:
        properties = []

    options = {}
    if '--use-trigonometry' in sys.argv[1:]:
        options['trigonometric'] = True
    if '--use-advanced' in sys.argv[1:]:
        options['advanced'] = True
    if '--max-layer-auxiliary' in sys.argv[1:]:
        options['max_layer'] = 'auxiliary'
    if '--max-layer-invisible' in sys.argv[1:]:
        options['max_layer'] = 'invisible'
    explainer = Explainer(scene, options=options)

    if '--profile' in sys.argv[1:]:
        import cProfile
        cProfile.runctx('explainer.explain()', {'explainer': explainer}, {})
    else:
        explainer.explain()
    if '--dump' in sys.argv[1:]:
        explainer.dump(properties)
    explainer.stats(properties).dump()

    if prop:
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
            for p in prop.reason.all_premises:
                premises.add(p)
            return premises

        explanation = explainer.explanation(prop)
        if explanation:
            dump(explanation)
            print('Depth = %s' % depth(explanation))
            print('Props = %s' % len(explanation.reason.all_premises))
            all_premises(explanation).stats().dump()
