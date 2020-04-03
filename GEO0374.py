# GEO0339 from http://hilbert.mat.uc.pt/TGTP/Problems/listing.php
import sys

from sandbox import *
from sandbox.hunter import Hunter
from sandbox.explainer import Explainer

scene = Scene()

A, B, C = scene.triangle(labels=('A', 'B', 'C'))
scene.equilateral_constraint((A, B, C))
D = B.translated_point(A.vector(B), 2)
F = scene.perpendicular_foot_point(D, B.line_through(C), label='F')

scene.dump()

placement = iterative_placement(scene)

hunter = Hunter(placement)
hunter.hunt()

angle = A.angle(C, F)

explainer = Explainer(scene, hunter.properties)
print('\tGuessed: %s = %s' % (angle, explainer.guessed(angle)))
if '--profile' in sys.argv[1:]:
    import cProfile
    cProfile.run('explainer.explain()')
else:
    explainer.explain()
if '--dump' in sys.argv[1:]:
    explainer.dump()
explainer.stats().dump()
print('\tExplained: %s = %s' % (angle, explainer.explained(angle)))
