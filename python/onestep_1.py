from runner import run_sample
from sandbox import Scene
from sandbox.property import ProportionalLengthsProperty

scene = Scene()

A, B, C, D = scene.square('A', 'B', 'C', 'D', non_degenerate=True).points
I = scene.incentre_point(Scene.Triangle(A, B, C), label='I')

prop = ProportionalLengthsProperty(B.segment(C), D.segment(I), 1)

run_sample(scene, prop)
