from runner import run_sample
from sandbox import Scene

scene = Scene()

A, B, C = scene.triangle(labels=('A', 'B', 'C'))
A.segment(C).perpendicular_constraint(B.segment(C), comment='Given: AC ⟂ BC')
E = A.translated_point(C.vector(B), label='E')
D = A.line_through(B).intersection_point(C.line_through(E), label='D')

run_sample(scene)
