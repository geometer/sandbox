#!/var/www/sandbox/virtualenv/bin/python

from sandbox import Scene
from sandbox.hunter import Hunter
from sandbox.explainer import Explainer

scene = Scene()

A, B, C = scene.triangle(labels=['A', 'B', 'C'])
scene.equilateral_constraint((A, B, C))
D = scene.circumcentre_point((A, B, C), label='D')

hunter = Hunter(scene, max_layer='auxiliary')
hunter.hunt()

explainer = Explainer(scene, hunter.properties)
explainer.explain()
explainer.dump()
explainer.stats().dump()
