from runner import run_sample
from sandbox import Scene

scene = Scene()

A, B, C = scene.nondegenerate_triangle(labels=('A', 'B', 'C')).points
A.segment(C).perpendicular_constraint(B.segment(C), comment='Given: AC ⟂ BC')
A.segment(C).ratio_constraint(B.segment(C), 1, comment='Given: AC = BC')
D = scene.perpendicular_foot_point(C, A.line_through(B), label='D')

run_sample(scene)
