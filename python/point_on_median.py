from sandbox import *
from sandbox.hunter import Hunter
from sandbox.explainer import Explainer

scene = Scene()

A = scene.free_point(label='A')
B = scene.free_point(label='B')
C = scene.free_point(label='C')
M = A.segment(B).middle_point(label='M')
l = C.line_through(M)
D = l.free_point(label='D')
para = scene.parallel_line(A.line_through(B), D)
A1 = para.intersection_point(A.line_through(C), label='A1')
B1 = para.intersection_point(B.line_through(C), label='B1')

hunter = Hunter(scene)
hunter.hunt()
print('')

explainer = Explainer(scene, hunter.properties)
explainer.explain()
explainer.dump()
