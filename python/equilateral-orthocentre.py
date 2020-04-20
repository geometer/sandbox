from sandbox import Scene

from runner import run_sample

scene = Scene()

triangle = scene.nondegenerate_triangle(labels=('A', 'B', 'C'))
triangle.sides[0].congruent_constraint(triangle.sides[1])
triangle.sides[0].congruent_constraint(triangle.sides[2])
scene.orthocentre_point(triangle, label='D')

run_sample(scene)
