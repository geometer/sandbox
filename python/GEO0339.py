# GEO0339 from http://hilbert.mat.uc.pt/TGTP/Problems/listing.php

from runner import run_sample
from sandbox import *
from sandbox.property import LengthRatioProperty

scene = Scene()

triangle = scene.nondegenerate_triangle(labels=('A', 'B', 'C'))
A, B, C = triangle.points
H = scene.orthocentre_point(triangle, label='H')
A1 = scene.circumcentre_point(Scene.Triangle(H, B, C), label='A1')
B1 = scene.circumcentre_point(Scene.Triangle(H, A, C), label='B1')
C1 = scene.circumcentre_point(Scene.Triangle(H, A, B), label='C1')

prop = LengthRatioProperty(A.segment(B), A1.segment(B1), 1)

run_sample(scene, prop)
