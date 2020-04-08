# https://www.facebook.com/groups/parmenides52/, problem 4594

from sandbox import Scene, iterative_placement
from sandbox.hunter import Hunter
from sandbox.explainer import Explainer

scene = Scene()

A, B, C = scene.triangle(labels=('A', 'B', 'C'))
scene.perpendicular_constraint((A, C), (B, C), comment='Given: AC ⟂ BC')
A.angle(B, C).ratio_constraint(B.angle(A, C), 2)
D = C.translated_point(A.vector(C), label='D')

placement = iterative_placement(scene)

hunter = Hunter(placement)
hunter.hunt()
print('')

explainer = Explainer(scene)
explainer.explain()
explainer.dump(hunter.properties)

explainer.stats(hunter.properties).dump()