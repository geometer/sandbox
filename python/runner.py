import argparse
import re

from sandbox import iterative_placement
from sandbox.core import CoreScene
from sandbox.explainer import Explainer
from sandbox.hunter import Hunter
from sandbox.propertyset import PropertySet

def run_sample(scene, *props):
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-layer', default='user', choices=CoreScene.layers)
    parser.add_argument('--dump', nargs='+', choices=('scene', 'constraints', 'stats', 'result', 'properties', 'explanation'), default=('stats', 'result'))
    parser.add_argument('--run-hunter', action='store_true')
    parser.add_argument('--extra-rules', nargs='+', choices=('advanced', 'circles', 'trigonometric'), default=())
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
        try:
            explainer.explain()
        except Exception as e:
            explainer.dump()
            raise e
    if 'properties' in args.dump:
        explainer.dump(properties)
    if 'stats' in args.dump:
        explainer.stats(properties).dump()

    if 'result' in args.dump:
        for prop in props:
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

        def full_size(prop):
            if prop.reason.premises:
                return 1 + sum(full_size(p) for p in prop.reason.premises)
            return 1

        def all_premises(prop):
            premises = PropertySet(explainer.context.points)
            for p in prop.reason.all_premises:
                premises.add(p)
            return premises

        for prop in props:
            explanation = explainer.explanation(prop)
            if explanation:
                dump(explanation)
                print('Depth = %s' % depth(explanation))
                print('Full size = %s' % full_size(explanation))
                cumulative_priorities = {}
                def cumu(prop):
                    cached = cumulative_priorities.get(prop)
                    if cached is not None:
                        return cached
                    if prop.reason.premises:
                        cu = 0.7 * prop.priority + 0.3 * max(cumu(p) for p in prop.reason.premises)
                    else:
                        cu = prop.priority
                    cumulative_priorities[prop] = cu
                    return cu

                priorities = {}
                for p in explanation.reason.all_premises:
                    priority = cumu(p)
                    priorities[priority] = priorities.get(priority, 0) + 1
                pairs = list(priorities.items())
                pairs.sort(key=lambda pair: -pair[0])
                count_all = len(explanation.reason.all_premises)
                print('Props = %d (%s)' % (count_all, ', '.join(['%.3f: %d' % p for p in pairs])))
                all_premises(explanation).stats().dump()
                rules_map = {}
                for prop in explanation.reason.all_premises:
                    key = type(prop.rule).__name__ if hasattr(prop, 'rule') else 'Unknown'
                    rules_map[key] = rules_map.get(key, 0) + 1
                items = list(rules_map.items())
                items.sort(key=lambda pair: -pair[1])
                print('Rules:')
                for pair in items:
                    print('\t%s: %s' % pair)
