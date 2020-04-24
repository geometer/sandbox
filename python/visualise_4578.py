from sandbox import Scene
from sandbox.util import LazyComment
from visualiser import visualise

scene = Scene()

triangle = scene.nondegenerate_triangle(labels=('A', 'B', 'C'))
D = scene.orthocentre_point(triangle, label='D')
D.inside_triangle_constraint(triangle)
A, B, C = triangle.points
H = A.line_through(D).intersection_point(B.line_through(C), label='H')
G = C.line_through(D).intersection_point(A.line_through(B), label='G')
A.line_through(C)
A.segment(B).congruent_constraint(C.segment(D), comment='given: |AB| = |CD|')

visualise(scene, C.angle(A, B))
