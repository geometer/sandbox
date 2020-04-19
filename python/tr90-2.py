from runner import run_sample
from sandbox import Scene

scene = Scene()

A, B, C = scene.triangle(labels=('A', 'B', 'C'))
A.segment(C).perpendicular_constraint(B.segment(C), comment='Given: AC ⟂ BC')
D = A.segment(B).middle_point(label='D')
E = D.translated_point(C.vector(D), label='E')

run_sample(scene)
