# GEO0339 from http://hilbert.mat.uc.pt/TGTP/Problems/listing.php
import sys

from sandbox import *
from sandbox.hunter import Hunter
from sandbox.explainer import Explainer

scene = Scene()

A, B, C = scene.triangle(labels=('A', 'B', 'C'))
H = scene.orthocentre_point((A, B, C), label='H')
A1 = scene.circumcentre_point((H, B, C), label='A1')
B1 = scene.circumcentre_point((H, A, C), label='B1')
C1 = scene.circumcentre_point((H, A, B), label='C1')

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
print('%.5f = %.5f' % (helper.distance(A, B), helper.distance(A1, B1)))
