from runner import run_sample
from sandbox import Scene

scene = Scene()

A, B, C = scene.nondegenerate_triangle(labels=('A', 'B', 'C')).points
A.segment(C).perpendicular_constraint(B.segment(C), comment='Given: AC ⟂ BC')
D = A.segment(B).middle_point(label='D')
E = A.translated_point(C.vector(B), label='E')

run_sample(scene)
