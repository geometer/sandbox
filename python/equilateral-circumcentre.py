from sandbox import Scene

from runner import run_sample

scene = Scene()

A, B, C = scene.triangle(labels=['A', 'B', 'C'])
scene.equilateral_constraint((A, B, C))
D = scene.circumcentre_point((A, B, C), label='D')

run_sample(scene)
