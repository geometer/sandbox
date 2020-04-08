from runner import run_sample

from sandbox import Scene
from sandbox.property import LengthRatioProperty

scene = Scene()

A, B, C = scene.triangle(labels=('A', 'B', 'C'))
scene.perpendicular_constraint((A, C), (B, C), comment='Given: AC ⟂ BC')
D = A.segment(B).middle_point(label='D')

prop = LengthRatioProperty(A.segment(D), C.segment(D), 1)

run_sample(scene, prop)
