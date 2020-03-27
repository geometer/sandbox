import sys

from sandbox import Scene
from sandbox.hunter import Hunter
from sandbox.explainer import Explainer

scene = Scene()

A, B, C = scene.triangle(labels=['A', 'B', 'C'])
A.segment(C).congruent_constraint(A.segment(B))
B.segment(C).congruent_constraint(A.segment(B))
scene.orthocentre_point((A, B, C), label='D')

hunter = Hunter(scene)
hunter.hunt()

explainer = Explainer(scene, hunter.properties)
if '--profile' in sys.argv[1:]:
    import cProfile
    cProfile.run('explainer.explain()')
else:
    explainer.explain()
explainer.stats().dump()
