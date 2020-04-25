import argparse
from itertools import combinations
import json
import numpy as np
import re

from sandbox.core import CoreScene
from sandbox.explainer import Explainer
from sandbox.placement import iterative_placement

def drawScene(scene, args, attempts=10, extra_points=()):
    points = scene.points(max_layer=args.max_layer) + list(extra_points)
    lines = scene.lines(max_layer=args.max_layer)

    placements = [iterative_placement(scene) for i in range(0, attempts)]

    def sizes(placement):
        values = []
        for pt0, pt1 in combinations(points, 2):
            values.append(placement.length2(pt0.vector(pt1)))
        connected = set()
        for line in lines:
            for pts in combinations(line.all_points, 2):
                connected.add(frozenset(pts))
        for pt0, pt1, pt2 in combinations(points, 3):
            if not all(frozenset(pts) in connected for pts in combinations((pt0, pt1, pt2), 2)):
                continue
            vec0 = pt0.vector(pt1)
            vec1 = pt0.vector(pt2)
            values.append(np.abs(placement.vector_product(vec0, vec1)))
        values.sort()
        return [v / values[-1] for v in values]

    def number_of_zeroes(placement):
        return sum(1 if d < 1e-6 else 0 for d in sizes(placement))

    index = min(number_of_zeroes(p) for p in placements)

    placements.sort(key=lambda p: sizes(p)[index])
    placement = placements[-1]

    coords = {}
    for pt in points:
        coords[pt] = placement.location(pt)

    scene_points = []
    for pt, coo in coords.items():
        scene_points.append({'name': pt.name, 'x': float(coo.x), 'y': float(coo.y)})
    scene_lines = []
    for line in lines:
        pts = [pt for pt in line.all_points if pt in coords]
        if len(pts) < 2:
            continue
        pts.sort(key=lambda pt: coords[pt].x)
        pts.sort(key=lambda pt: coords[pt].y)
        scene_lines.append({'pt0': pts[0].name, 'pt1': pts[-1].name})
    print('sandbox$.createScene(\'%s\');' % json.dumps({'points': scene_points, 'lines': scene_lines}));

def drawTree(scene, prop, args):
    options = { 'max_layer': args.max_layer }
    for extra in args.extra_rules:
        options[extra] = True
    explainer = Explainer(scene, options=options)
    explainer.explain()
    explanation = explainer.explanation(prop)
    if not explanation:
        print('\tNot explained: %s' % prop)

    def dump(prop):
        def html(comment):
            while hasattr(comment, 'html'):
                comment = comment.html()
            return str(comment)
        s = '%s<span class="implication">⇐</span>%s' % (html(prop), ', '.join([html(com) for com in prop.reason.comments]))
        s = re.sub('\|', '<span style="font-size:130%;vertical-align:-2px;">|</span>', s)
        print('<li class="%s"><span class="handler"></span>%s' % ('essential' if prop.essential else 'normal', s))
        if prop.reason.premises:
            print('<ul>')
            for premise in prop.reason.premises:
                dump(premise)
            print('</ul>')
        print('</li>')

    print('<ul>')
    dump(explanation)
    print('</ul>')

def visualise(scene, prop):
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-layer', default='user', choices=CoreScene.layers)
    parser.add_argument('--extra-rules', nargs='+', choices=('advanced', 'trigonometric'), default=())
    args = parser.parse_args()

    with open('../html/pattern.html') as f:
        for line in f.readlines():
            line = line.strip()
            if line == '$$SCENE$$':
                drawScene(scene, args)
            elif line == '$$TREE$$':
                drawTree(scene, prop, args)
            else:
                print(line)
