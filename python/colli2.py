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
E = scene.free_point(label='E')
E.not_collinear_constraint(C, D)
F = scene.free_point(label='F')
F.collinear_constraint(C, D)

props = (
    PointsCollinearityProperty(A, C, D, True),
    PointsCollinearityProperty(B, D, F, True),
    PointsCollinearityProperty(A, B, E, False),
)

run_sample(scene, *props)
