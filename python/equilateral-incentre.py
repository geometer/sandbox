#!/var/www/sandbox/virtualenv/bin/python

from sandbox import Scene
from sandbox.hunter import Hunter
from sandbox.explainer import Explainer

scene = Scene()

A, B, C = scene.triangle(labels=['A', 'B', 'C'])
A.segment(C).congruent_constraint(A.segment(B))
B.segment(C).congruent_constraint(A.segment(B))
scene.incentre_point((A, B, C), label='D')

hunter = Hunter(scene, max_layer='auxiliary')
hunter.hunt()

explainer = Explainer(scene)
explainer.explain()
explainer.dump(hunter.properties)
explainer.stats(hunter.properties).dump()