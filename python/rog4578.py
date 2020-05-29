# "Romantics of Geometry" group on Facebook, problem 4578
# https://www.facebook.com/groups/parmenides52/permalink/2779763428804012/

from runner import run_sample
from sandbox import *
from sandbox.property import AngleValueProperty

scene = Scene()

triangle = scene.nondegenerate_triangle(labels=('A', 'B', 'C'))
D = scene.orthocentre_point(triangle, label='D')
D.inside_triangle_constraint(triangle)
A, B, C = triangle.points
H = A.line_through(D).intersection_point(B.line_through(C), label='H')
G = C.line_through(D).intersection_point(A.line_through(B), label='G')
A.segment(B).congruent_constraint(C.segment(D), comment='given')

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
# +*13* |AH| = |CH|                                *12                equal triangles => equal sides
# +*14* isosceles △ A H C                          *13                equal sides => isosceles
# +*15* ∠ A C H = (180º - ∠ A H C) / 2 = 45º       *14                isocseles
# +*16* ∠ A C B = ∠ A C H                          *same angle
# +*17* ∠ A C B = ∠ A C H = 45º                    *15, *16           transitivity

run_sample(scene, C.angle(A, B))
