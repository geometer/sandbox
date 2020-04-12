from sandbox import Scene

from runner import run_sample

scene = Scene()

A, B, C = scene.triangle(labels=['A', 'B', 'C'])
A.segment(C).congruent_constraint(A.segment(B))
B.segment(C).congruent_constraint(A.segment(B))
scene.incentre_point((A, B, C), label='D')

run_sample(scene)
