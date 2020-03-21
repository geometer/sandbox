#!/var/www/sandbox/virtualenv/bin/python

from sandbox import Scene
from sandbox.hunter import Hunter
from sandbox.explainer import Explainer

scene = Scene()

A, B, C = scene.triangle(labels=['A', 'B', 'C'])
A.vector(C).length_equal_constraint(A.vector(B))
B.vector(C).length_equal_constraint(A.vector(B))
A1 = scene.middle_point(B, C, label='A1')
B1 = scene.middle_point(A, C, label='B1')
A.line_through(A1).intersection_point(B.line_through(B1), label='D')

hunter = Hunter(scene)
hunter.hunt()

explainer = Explainer(scene, hunter.properties)
explainer.explain()
explainer.dump()
explainer.stats().dump()
