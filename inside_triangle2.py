# https://www.facebook.com/groups/parmenides52/, problem 4594

from sandbox import Scene, iterative_placement
from sandbox.hunter import Hunter
from sandbox.explainer import Explainer

scene = Scene()

A, B, C = scene.triangle(labels=('A', 'B', 'C'))
D = A.segment(B).free_point(label='D')
E = A.segment(C).free_point(label='E')
F = B.segment(C).free_point(label='F')
X = D.line_through(E).intersection_point(A.line_through(F), label='X')

hunter = Hunter(scene)
hunter.hunt()

explainer = Explainer(scene, hunter.properties)
explainer.explain()
explainer.dump()

explainer.stats().dump()
