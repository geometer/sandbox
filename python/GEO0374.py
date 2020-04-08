# GEO0339 from http://hilbert.mat.uc.pt/TGTP/Problems/listing.php
import sys

from runner import run_sample
from sandbox import Scene
from sandbox.property import AngleValueProperty

scene = Scene()

A, B, C = scene.triangle(labels=('A', 'B', 'C'))
scene.equilateral_constraint((A, B, C))
D = B.translated_point(A.vector(B), 2, label='D')
F = scene.perpendicular_foot_point(D, B.line_through(C), label='F')

prop = AngleValueProperty(A.angle(C, F), 90)

run_sample(scene, prop)
