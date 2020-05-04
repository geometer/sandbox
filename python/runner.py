import argparse
import re

from sandbox import iterative_placement
from sandbox.core import CoreScene
from sandbox.explainer import Explainer
from sandbox.hunter import Hunter
from sandbox.propertyset import PropertySet

def run_sample(scene, prop=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-layer', default='user', choices=CoreScene.layers)
    parser.add_argument('--dump', nargs='+', choices=('scene', 'constraints', 'stats', 'result', 'properties', 'explanation'), default=('stats', 'result'))
    parser.add_argument('--run-hunter', action='store_true')
    parser.add_argument('--extra-rules', nargs='+', choices=('advanced', 'trigonometric'), default=())
    parser.add_argument('--profile', action='store_true')
    args = parser.parse_args()

    if 'scene' in args.dump:
        scene.dump(include_constraints='constraints' in args.dump, max_layer=args.max_layer)

    if args.run_hunter:
        placement = iterative_placement(scene)
        hunter = Hunter(placement)
        hunter.hunt()
        properties = hunter.properties
    else:
        properties = []

    options = { 'max_layer': args.max_layer }
    for extra in args.extra_rules:
        options[extra] = True
    explainer = Explainer(scene, options=options)

    if args.profile:
        import cProfile
        cProfile.runctx('explainer.explain()', {'explainer': explainer}, {})
    else:
        explainer.explain()
    if 'properties' in args.dump:
        explainer.dump(properties)
    if 'stats' in args.dump:
        explainer.stats(properties).dump()

    if prop and 'result' in args.dump:
        explanation = explainer.explanation(prop)
        if explanation:
            print('\tExplained: %s' % explanation)
        else:
            print('\tNot explained: %s' % prop)

    if 'explanation' in args.dump:
        def dump(prop, level=0):
            print('\t' + '  ' * level + str(prop) + ': ' + str(prop.reason.comment))
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
            count_essentials = explanation.reason.essential_premises_count
            count_all = len(explanation.reason.all_premises)
            print('Props = %d (%d + %d)' % (count_all, count_essentials, count_all - count_essentials))
            all_premises(explanation).stats().dump()
            rules_map = {}
            for prop in explanation.reason.all_premises:
                if prop.reason.generation == -1:
                    key = 'Given'
                elif hasattr(prop, 'rule') and prop.rule == 'synthetic':
                    key = 'Synthetic (transitivity)'
                else:
                    key = type(prop.rule).__name__ if hasattr(prop, 'rule') else 'Unknown'
                rules_map[key] = rules_map.get(key, 0) + 1
            items = list(rules_map.items())
            items.sort(key=lambda pair: -pair[1])
            print('Rules:')
            for pair in items:
                print('\t%s: %s' % pair)
