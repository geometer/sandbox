# "Romantics of Geometry" group on Facebook, problem 4578
# https://www.facebook.com/groups/parmenides52/permalink/2779763428804012/

import math

from sandbox import *
from sandbox.hunter import Hunter
from sandbox.explainer import Explainer

scene = Scene()

A, B, C = scene.triangle(labels=('A', 'B', 'C'))
altitudeA = scene.altitude((A, B, C), A, label='altitudeA')
altitudeC = scene.altitude((A, B, C), C, label='altitudeC')
D = altitudeA.intersection_point(altitudeC, label='D')
D.inside_triangle_constraint(A, B, C)
H = altitudeA.intersection_point(B.line_through(C, label='BC'), label='H')
G = altitudeC.intersection_point(A.line_through(B, label='AB'), label='G')
A.segment(B).congruent_constraint(C.segment(D), comment='Given: |AB| = |CD|')

scene.dump()

#Proof
# * 1* |AB| = |CD|                                *given
# * 2* ∠ A H B = 90º                              *given (altitude)
# * 3* ∠ A H C = 90º                              *given (altitude)
# * 4* ∠ C G B = 90º                              *given (altitude)
# * 5* ∠ A H B = ∠ A H C (a.k.a ∠ D H C) = 90º    *2, *3             same arcs => equal angles
# * 6* ∠ A H B = ∠ C G B                          *2, *4             same arcs => equal angles
# * 7* ∠ A B H = ∠ C B G                          *same angle
# * 8* △ A B H ∼ △ C B G                          *6, *7             two angles
# * 9* ∠ H A B = ∠ G C B (a.k.a. ∠ D C H)         *8                 similar triangles => equal angles
# *10* △ A B H = △ C D H                          *1, *5, *9         two anlges, side
# *11* |AH| = |CH|                                *10                equal triangles => equal sides
# *12* isosceles △ A H C                          *11                equal sides => isosceles
# *13* ∠ A C H = (180º - ∠ A H C) / 2             *12                isocseles
# *14* ∠ A C H = 45º                              *3, *13            algebra

#Facts
# *+ right angles
# *+ equal angles
# *+ similar triangles
# * equal triangles
# *+ equal segments
# *+ isosceles

placement = iterative_placement(scene)

hunter = Hunter(placement)
hunter.hunt()
print('')

explainer = Explainer(scene, hunter.properties)
explainer.explain()
explainer.dump()
explainer.stats().dump()