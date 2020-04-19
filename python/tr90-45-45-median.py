from runner import run_sample
from sandbox import Scene

scene = Scene()

A, B, C = scene.triangle(labels=('A', 'B', 'C'))
A.segment(C).perpendicular_constraint(B.segment(C), comment='Given: AC ⟂ BC')
A.segment(C).ratio_constraint(B.segment(C), 1, comment='Given: AC = BC')
D = A.segment(B).middle_point(label='D')

run_sample(scene)
