# GEO0339 from http://hilbert.mat.uc.pt/TGTP/Problems/listing.php

from runner import run_sample
from sandbox import Scene
from sandbox.property import LengthRatioProperty

scene = Scene()

A, B, C = scene.triangle(labels=('A', 'B', 'C'))
F = B.segment(C).middle_point(label='F')
D = scene.perpendicular_foot_point(C, A.line_through(B), label='D')
E = scene.perpendicular_foot_point(B, A.line_through(C), label='E')
G = scene.perpendicular_foot_point(F, D.line_through(E), label='G')

prop = LengthRatioProperty(G.segment(D), G.segment(E), 1)

run_sample(scene, prop)
