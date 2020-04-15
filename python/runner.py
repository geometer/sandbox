import argparse

from sandbox import iterative_placement
from sandbox.core import CoreScene
from sandbox.explainer import Explainer
from sandbox.hunter import Hunter
from sandbox.propertyset import PropertySet

def run_sample(scene, prop=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-layer', default='user', choices=CoreScene.layers)
    parser.add_argument('--dump-scene', action='store_true')
    parser.add_argument('--run-hunter', action='store_true')
    parser.add_argument('--use-trigonometry', action='store_true')
    parser.add_argument('--use-advanced', action='store_true')
    parser.add_argument('--profile', action='store_true')
    parser.add_argument('--dump', action='store_true')
    parser.add_argument('--explain', action='store_true')
    args = parser.parse_args()

    if args.dump_scene:
        scene.dump()

    if args.run_hunter:
        placement = iterative_placement(scene)
        hunter = Hunter(placement)
        hunter.hunt()
        properties = hunter.properties
    else:
        properties = []

    options = {
        'max_layer': args.max_layer,
        'trigonometric': args.use_trigonometry,
        'advanced': args.use_advanced,
    }
    explainer = Explainer(scene, options=options)

    if args.profile:
        import cProfile
        cProfile.runctx('explainer.explain()', {'explainer': explainer}, {})
    else:
        explainer.explain()
    if args.dump:
        explainer.dump(properties)
    explainer.stats(properties).dump()

    if prop:
        if explainer.explained(prop):
            print('\tExplained: %s' % prop)
        else:
            print('\tNot explained: %s' % prop)

    if args.explain:
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
