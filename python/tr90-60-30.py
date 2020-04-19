from runner import run_sample
from sandbox import Scene

scene = Scene()

A, B, C = scene.triangle(labels=('A', 'B', 'C'))
A.segment(C).perpendicular_constraint(B.segment(C), comment='Given: AC ⟂ BC')
A.angle(B, C).ratio_constraint(B.angle(A, C), 2)

run_sample(scene)
