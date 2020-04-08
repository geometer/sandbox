# GEO0339 from http://hilbert.mat.uc.pt/TGTP/Problems/listing.php

from runner import run_sample
from sandbox import *

scene = Scene()

A, B, C, D = scene.parallelogram(labels=('A', 'B', 'C', 'D'))
A1 = scene.perpendicular_foot_point(A, B.line_through(D), label='A1')
B1 = scene.perpendicular_foot_point(B, A.line_through(C), label='B1')
C1 = scene.perpendicular_foot_point(C, B.line_through(D), label='C1')
D1 = scene.perpendicular_foot_point(D, A.line_through(C), label='D1')

run_sample(scene)
