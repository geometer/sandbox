# https://www.facebook.com/groups/parmenides52/, problem 4594

from sandbox import Scene, iterative_placement
from sandbox.hunter import Hunter
from sandbox.explainer import Explainer

scene = Scene()

A, B, C = scene.triangle(labels=('A', 'B', 'C'))
I = scene.incentre_point((A, B, C), label='I')
J = scene.orthocentre_point((A, B, I), label='J')
scene.perpendicular_constraint((A, B), (A, C))

placement = iterative_placement(scene)

hunter = Hunter(placement)
hunter.hunt()
print('')

explainer = Explainer(scene, hunter.properties)
explainer.explain()
explainer.dump()

print('|%s%s| = %.5f' % (A.label, J.label, placement.distance(A, J)))
print('|%s%s| = %.5f' % (B.label, I.label, placement.distance(B, I)))
