import sys

from sandbox import Scene
from sandbox.hunter import Hunter
from sandbox.explainer import Explainer

scene = Scene(strategy='constraints')

A, B, C = scene.triangle(labels=['A', 'B', 'C'])
scene.equilateral_constraint((A, B, C))
D = scene.circumcentre_point((A, B, C), label='D')

hunter = Hunter(scene, max_layer='auxiliary')
hunter.hunt()

explainer = Explainer(scene)
if '--profile' in sys.argv[1:]:
    import cProfile
    cProfile.run('explainer.explain()')
else:
    explainer.explain()
explainer.dump(hunter.properties)
explainer.stats(hunter.properties).dump()