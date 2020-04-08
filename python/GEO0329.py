# GEO0339 from http://hilbert.mat.uc.pt/TGTP/Problems/listing.php
import sys

from sandbox import *
from sandbox.hunter import Hunter
from sandbox.explainer import Explainer

scene = Scene()

A, B, C, D = scene.parallelogram(labels=('A', 'B', 'C', 'D'))
A1 = scene.perpendicular_foot_point(A, B.line_through(D), label='A1')
B1 = scene.perpendicular_foot_point(B, A.line_through(C), label='B1')
C1 = scene.perpendicular_foot_point(C, B.line_through(D), label='C1')
D1 = scene.perpendicular_foot_point(D, A.line_through(C), label='D1')

scene.dump()

placement = iterative_placement(scene)

hunter = Hunter(placement)
hunter.hunt()

explainer = Explainer(scene, hunter.properties)
if '--profile' in sys.argv[1:]:
    import cProfile
    cProfile.run('explainer.explain()')
else:
    explainer.explain()
if '--dump' in sys.argv[1:]:
    explainer.dump()
explainer.stats().dump()
