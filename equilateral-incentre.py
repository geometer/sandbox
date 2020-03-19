#!/var/www/sandbox/virtualenv/bin/python

from sandbox import Scene
from sandbox.hunter import Hunter
from sandbox.explainer import Explainer

scene = Scene()

A, B, C = scene.triangle(labels=['A', 'B', 'C'])
A.vector(C).length_equal_constraint(A.vector(B))
B.vector(C).length_equal_constraint(A.vector(B))
scene.incentre_point((A, B, C), label='D')

hunter = Hunter(scene)
hunter.hunt()

explainer = Explainer(scene, hunter.properties)
explainer.explain()
explainer.dump()
explainer.stats().dump()
