from sandbox import Scene
from sandbox.property import PointsCollinearityProperty
from sandbox.util import LazyComment

from visualiser import visualise

scene = Scene()

A, B, C, D = scene.square('A', 'B', 'C', 'D')
A.x = 0
A.y = 0
B.x = 1
B.y = 0
E = B.segment(C).free_point(label='E')
B, E, F, K = scene.square(B, E, 'F', 'K')
B.inside_constraint(A.segment(K))
N = A.line_through(C).intersection_point(E.line_through(K), label='N')

D.line_through(N)
N.line_through(F)

prop = PointsCollinearityProperty(D, N, F, True)

visualise(scene, prop, title='Problem 5.3.1', task=[
    LazyComment('%s is a square', Scene.Polygon(A, B, C, D)),
    LazyComment('%s is a point inside segment %s', E, B.segment(C)),
    LazyComment('%s is a square', Scene.Polygon(B, E, F, K)),
    LazyComment('%s lies inside segment %s', B, A.segment(K)),
    LazyComment('%s is the intersection point of %s and %s', N, A.segment(C).as_line, E.segment(K).as_line),
    LazyComment('Prove, that %s, %s, and %s are collinear', D, N, F)
], reference='<a href="http://vivacognita.org/555geometry.html/_/5/5-3/53-1-r371">Problem 5.3.1</a> from the <a href="https://www.amazon.com/Geometry-Figures-Second-Arseniy-Akopyan/dp/1548710784">Akopyan\\\'s book</a>')
