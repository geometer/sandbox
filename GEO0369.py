# GEO0339 from http://hilbert.mat.uc.pt/TGTP/Problems/listing.php
import sys

from sandbox import *
from sandbox.hunter import Hunter
from sandbox.explainer import Explainer

scene = Scene()

A, B, C = scene.triangle(labels=('A', 'B', 'C'))
F = B.segment(C).middle_point(label='F')
D = scene.perpendicular_foot_point(C, A.line_through(B), label='D')
E = scene.perpendicular_foot_point(B, A.line_through(C), label='E')
G = scene.perpendicular_foot_point(F, D.line_through(E), label='G')

placement = iterative_placement(scene)

hunter = Hunter(placement)
hunter.hunt()
print('')

explainer = Explainer(scene)
explainer.explain()
if '--dump' in sys.argv[1:]:
    explainer.dump(hunter.properties)
explainer.stats(hunter.properties).dump()

helper = PlacementHelper(placement)
print('%.5f = %.5f' % (helper.distance(D, G), helper.distance(E, G)))
