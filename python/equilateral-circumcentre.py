from sandbox import Scene

from runner import run_sample

scene = Scene()

triangle = scene.nondegenerate_triangle(labels=('A', 'B', 'C'))
scene.equilateral_constraint(triangle)
D = scene.circumcentre_point(triangle, label='D')

run_sample(scene)
