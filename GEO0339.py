# GEO0339 from http://hilbert.mat.uc.pt/TGTP/Problems/listing.php

import time
from sandbox import *
from sandbox.hunter import Hunter
from sandbox.explainer import Explainer

scene = Scene()

A, B, C = scene.triangle(labels=('A', 'B', 'C'))
H = scene.orthocentre_point(A, B, C, label='H')
A1 = scene.circumcentre_point(H, B, C, label='A1')
B1 = scene.circumcentre_point(H, A, C, label='B1')
C1 = scene.circumcentre_point(H, A, B, label='C1')

placement = iterative_placement(scene, print_progress=True)

hunter = Hunter(placement)
hunter.hunt(['collinears', 'equal_triangles', 'right_angles', 'equal_segments', 'equal_angles', 'similar_triangles'])
print('')

explainer = Explainer(scene, hunter.properties)
explainer.explain()
explainer.dump()
