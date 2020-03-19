# https://www.facebook.com/groups/parmenides52/, problem 4594

from sandbox import Scene, iterative_placement
from sandbox.hunter import Hunter
from sandbox.explainer import Explainer

scene = Scene()

A, B, C = scene.triangle(labels=('A', 'B', 'C'))
scene.perpendicular_constraint((A, C), (B, C), comment='Given: AC ⟂ BC')
A.vector(C).length_ratio_constraint(B.vector(C), 1, comment='Given: AC = BC')
D = scene.middle_point(A, B, label='D')
perp = D.perpendicular_line(A.line_through(B))
E = perp.intersection_point(A.line_through(C), label='E')

placement = iterative_placement(scene)

hunter = Hunter(placement)
hunter.hunt()
print('')

explainer = Explainer(scene, hunter.properties)
explainer.explain()
explainer.dump()

explainer.stats().dump()