# https://www.facebook.com/groups/parmenides52/, problem 4594

from sandbox import Scene, iterative_placement
from sandbox.hunter import Hunter
from sandbox.explainer import Explainer

scene = Scene()

A, B, C = scene.triangle(labels=('A', 'B', 'C'))
scene.perpendicular_constraint((A, C), (B, C), comment='Given: AC ⟂ BC')
A.segment(C).ratio_constraint(B.segment(C), 1, comment='Given: AC = BC')
D = scene.middle_point(A, B, label='D')

placement = iterative_placement(scene)

hunter = Hunter(placement)
hunter.hunt()
print('')

explainer = Explainer(scene, hunter.properties)
explainer.explain()
explainer.dump()

explainer.stats().dump()
