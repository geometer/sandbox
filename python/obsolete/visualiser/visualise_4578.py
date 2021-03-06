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
A.segment(B).congruent_constraint(C.segment(D), comment='given')

visualise(scene, C.angle(A, B), title='Problem 4578', task=[
    LazyComment('%s is a non-degenerate triangle', triangle),
    LazyComment('%s is the orthocentre of %s', D, triangle),
    LazyComment('%s lies inside %s', D, triangle),
    LazyComment('%s is an altitude of %s', A.segment(H), triangle),
    LazyComment('%s is an altitude of %s', C.segment(G), triangle),
    LazyComment('|%s| = |%s|', A.segment(B), C.segment(D)),
    LazyComment('Find %s', C.angle(A, B))
], reference='<a href="https://www.facebook.com/groups/parmenides52/permalink/2779763428804012/">Problem 4578</a> from <a href="https://www.facebook.com/groups/parmenides52/">“Romantics of geometry”</a> facebook group')
