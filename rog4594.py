# https://www.facebook.com/groups/parmenides52/, problem 4594

from sandbox import Scene, iterative_placement, PlacementHelper
from sandbox.hunter import Hunter
from sandbox.explainer import Explainer

scene = Scene()

A, B, C = scene.triangle(labels=('A', 'B', 'C'))
I = scene.incentre_point((A, B, C), label='I')
J = scene.orthocentre_point((A, B, I), label='J')
scene.perpendicular_constraint((A, B), (A, C), comment='Given: AB ⟂ AC')

# Additional constructions
D = A.line_through(B).intersection_point(I.line_through(J), label='D')
E = A.line_through(I).intersection_point(B.line_through(J), label='E')

placement = iterative_placement(scene)

hunter = Hunter(placement)
hunter.hunt()
print('')

explainer = Explainer(scene, hunter.properties)
explainer.explain()
explainer.dump()

helper = PlacementHelper(placement)
print('|%s%s| = %.5f' % (A.label, J.label, helper.distance(A, J)))
print('|%s%s| = %.5f' % (B.label, I.label, helper.distance(B, I)))
