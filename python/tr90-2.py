# https://www.facebook.com/groups/parmenides52/, problem 4594

from sandbox import Scene, iterative_placement
from sandbox.hunter import Hunter
from sandbox.explainer import Explainer

scene = Scene()

A, B, C = scene.triangle(labels=('A', 'B', 'C'))
scene.perpendicular_constraint((A, C), (B, C), comment='Given: AC ⟂ BC')
D = A.segment(B).middle_point(label='D')
E = D.translated_point(C.vector(D), label='E')

placement = iterative_placement(scene)

hunter = Hunter(placement)
hunter.hunt()
print('')

explainer = Explainer(scene, hunter.properties)
explainer.explain()
explainer.dump()

hunter.stats().dump()
explainer.stats().dump()
