from runner import run_sample
from sandbox import Scene

scene = Scene()

A, B, C = scene.nondegenerate_triangle(labels=('A', 'B', 'C')).points
A.segment(C).perpendicular_constraint(B.segment(C), comment='Given: AC ⟂ BC')
A.segment(C).ratio_constraint(B.segment(C), 1, comment='Given: AC = BC')
D = A.segment(B).middle_point(label='D')
perp = D.perpendicular_line(A.line_through(B))
E = perp.intersection_point(A.line_through(C), label='E')

run_sample(scene)
