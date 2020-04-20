from itertools import combinations
import numpy as np
import matplotlib.pyplot as plt

from .placement import iterative_placement

def sketch(scene, attempts=10):
    points = scene.points(max_layer='user')

    placements = [iterative_placement(scene) for i in range(0, attempts)]

    def sizes(placement):
        values = []
        for pt0, pt1 in combinations(points, 2):
            values.append(placement.length2(pt0.vector(pt1)))
        connected = set()
        for line in scene.lines():
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

    fig, ax = plt.subplots(figsize=(6, 6))

    max_x = max(coo.x for coo in coords.values())
    min_x = min(coo.x for coo in coords.values())
    max_y = max(coo.y for coo in coords.values())
    min_y = min(coo.y for coo in coords.values())
    mid_x = (min_x + max_x) / 2
    mid_y = (min_y + max_y) / 2
    size = max(max_x - min_x, max_y - min_y) * 1.2
    ax.set_xlim(mid_x - size / 2, mid_x + size / 2)
    ax.set_ylim(mid_y - size / 2, mid_y + size / 2)
    ax.set_axis_off()

    for line in scene.lines():
        pts = [coords[pt] for pt in line.all_points if pt in coords]
        pts.sort(key=lambda coo: coo.x)
        pts.sort(key=lambda coo: coo.y)
        ax.plot([pts[0].x, pts[-1].x], [pts[0].y, pts[-1].y], lw=3, color='#64B5F6')

    for pt, coo in coords.items():
        ax.plot(coo.x, coo.y, fillstyle='full', color='#42A5F5', marker='o', markersize=20)
        ax.text(coo.x, coo.y - size * 0.004, pt.name, horizontalalignment='center', verticalalignment='center', fontsize=13, color='#FFFFFF')

    plt.show()
