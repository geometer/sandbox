# https://www.facebook.com/groups/parmenides52/, problem 4578

import math

from sandbox import *
from sandbox.hunter import Hunter
from sandbox.explainer import Explainer

scene = Scene()

A, B, C = scene.triangle(labels=('A', 'B', 'C'))
D = scene.orthocentre_point((A, B, C), label='D')
D.inside_triangle_constraint(A, B, C)
H = A.line_through(D, label='altitudeA').intersection_point(B.line_through(C, label='BC'), label='H')
G = C.line_through(D, label='altitudeC').intersection_point(A.line_through(B, label='AB'), label='G')
scene.equal_distances_constraint((A, B), (C, D))

scene.dump()

#Proof
# +* 1* |AB| = |CD|                                *given
# +* 2* ∠ A H B = 90º                              *given (altitude)
# +* 3* ∠ A H C = 90º                              *given (altitude)
# +* 4* ∠ C G B = 90º                              *given (altitude)
# +* 5* ∠ A H B = ∠ A H C (a.k.a ∠ D H C) = 90º    *2, *3             same arcs => equal angles
# +* 6* ∠ A H B = ∠ C G B                          *2, *4             same arcs => equal angles
# +* 7* ∠ A B H = ∠ C B G                          *same angle
# +* 8* △ A B H ∼ △ C B G                          *6, *7             two angles
# +* 9* ∠ H A B = ∠ G C B (a.k.a. ∠ D C H)         *8                 similar triangles => equal angles
# +*10* ∠ H A B = ∠ D C H                          *9                 similar triangles => equal angles
# +*11* △ A B H ∼ △ C D H                          *5, *10            two anlges
# +*12* △ A B H = △ C D H                          *1, *11            similarity, side
# *13* |AH| = |CH|                                *12                equal triangles => equal sides
# *14* isosceles △ A H C                          *13                equal sides => isosceles
# *15* ∠ A C H = (180º - ∠ A H C) / 2             *14                isocseles
# *16* ∠ A C H = 45º                              *3, *15            algebra

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

print('\n%.5f' % (placement.angle(C, A, C, B) / math.pi * 180))
