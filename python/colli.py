from runner import run_sample
from sandbox import Scene
from sandbox.property import PointsCollinearityProperty

scene = Scene()

A = scene.free_point(label='A')
B = scene.free_point(label='B')
B.not_equal_constraint(A)
C = scene.free_point(label='C')
D = scene.free_point(label='D')
C.collinear_constraint(A, B)
D.collinear_constraint(A, B)

prop = PointsCollinearityProperty(A, C, D, True)

run_sample(scene, prop)
