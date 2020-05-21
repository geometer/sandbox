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

visualise(scene, C.angle(A, B), title='Problem 4578', description=LazyComment('''
<p>%s is a non-degenerate triangle.</p>
<p>%s is the orthocentre of %s.</p>
<p>%s lies inside %s.</p>
<p>%s is an altitude of %s.</p>
<p>%s is an altitude of %s.</p>
<p>|%s| = |%s|.</p>
<p>Find %s.</p>
<p style="font-size:80%%"><a href="https://www.facebook.com/groups/parmenides52/permalink/2779763428804012/">Problem 4578</a> from <a href="https://www.facebook.com/groups/parmenides52/">“Romantics of geometry”</a> facebook group</p>
''', triangle, D, triangle, D, triangle, A.segment(H), triangle, C.segment(G), triangle, A.segment(B), C.segment(D), C.angle(A, B)).html())
