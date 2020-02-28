# https://www.facebook.com/groups/parmenides52/, problem 4578

import math

from sandbox import *
from sandbox.hunter import Hunter
from sandbox.explainer import Explainer

scene = Scene()

A = scene.free_point(label='A')
B = scene.free_point(label='B')
C = scene.free_point(label='C')
heightA = scene.perpendicular_line(A, B.line_through(C), label='heightA')
heightC = scene.perpendicular_line(C, A.line_through(B), label='heightC')
D = heightA.intersection_point(heightC, label='D')
D.inside_triangle_constraint(A, B, C)
H = heightA.intersection_point(B.line_through(C, label='BC'), label='H')
G = heightC.intersection_point(A.line_through(B, label='AB'), label='G')
scene.equal_distances_constraint((A, B), (C, D))

scene.dump()

#Proof
# * 1* |AB| = |CD|                                *given
# * 2* ∠ A H B = 90º                              *given (height)
# * 3* ∠ A H C = 90º                              *given (height)
# * 4* ∠ C G B = 90º                              *given (height)
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
hunter.hunt(['collinears', 'equal_triangles', 'right_angles', 'equal_segments', 'equal_angles', 'similar_triangles'])
print('')

explainer = Explainer(scene, hunter.properties)
explainer.explain()
explainer.dump()

print('\n%.5f' % (placement.angle(C, A, C, B) / math.pi * 180))
