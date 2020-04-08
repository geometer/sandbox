# "Romantics of Geometry" group on Facebook, problem 4594
# https://www.facebook.com/groups/parmenides52/permalink/2784962828284072/

import sys

from runner import run_sample
from sandbox import Scene, iterative_placement
from sandbox.hunter import Hunter
from sandbox.explainer import Explainer
from sandbox.property import LengthRatioProperty
from sandbox.propertyset import PropertySet

scene = Scene()

A, B, C = scene.triangle(labels=('A', 'B', 'C'))
scene.perpendicular_constraint((A, B), (A, C), comment='Given: AB ⟂ AC')
I = scene.incentre_point((A, B, C), label='I')
J = scene.orthocentre_point((A, B, I), label='J')

# Additional constructions
#D = A.line_through(B).intersection_point(I.line_through(J), label='D')
#E = A.line_through(I).intersection_point(B.line_through(J), label='E')

prop = LengthRatioProperty(A.segment(J), B.segment(I), 1)

run_sample(scene, prop)
