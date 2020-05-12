# "Romantics of Geometry" group on Facebook, problem 4578
# https://www.facebook.com/groups/parmenides52/permalink/2779763428804012/

from sandbox import Scene
from sketcher import sketch

scene = Scene()

triangle = scene.nondegenerate_triangle(labels=('A', 'B', 'C'))
D = scene.orthocentre_point(triangle, label='D')
D.inside_triangle_constraint(triangle)
A, B, C = triangle.points
H = A.line_through(D).intersection_point(B.line_through(C), layer='auxiliary')
G = C.line_through(D).intersection_point(A.line_through(B), layer='auxiliary')
A.segment(B).congruent_constraint(C.segment(D), comment='Given: |AB| = |CD|')

sketch(scene, extra_points=(H, G))
