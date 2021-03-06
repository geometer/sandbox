from sandbox import Scene
from sandbox.property import ProportionalLengthsProperty

from visualiser import visualise

scene = Scene()

triangle = scene.nondegenerate_triangle(labels=('A', 'B', 'C'))
A, B, C = triangle.points
circ = scene.circumcircle(triangle)
H = scene.orthocentre_point(triangle, label='H')

altitudeA = scene.altitude(triangle, A)
A1 = altitudeA.intersection_point(B.line_through(C), label='A_1')
A2 = altitudeA.intersection_point(circ, label='A_2')
A2.not_equal_constraint(A)

altitudeB = scene.altitude(triangle, B)
B1 = altitudeB.intersection_point(A.line_through(C), label='B_1')
B2 = altitudeB.intersection_point(circ, label='B_2')
B2.not_equal_constraint(B)

altitudeC = scene.altitude(triangle, C)
C1 = altitudeC.intersection_point(B.line_through(A), label='C_1')
C2 = altitudeC.intersection_point(circ, label='C_2')
C2.not_equal_constraint(C)

A.angle(B, C).is_acute_constraint(comment='assumption')
B.angle(A, C).is_acute_constraint(comment='assumption')
C.angle(B, A).is_acute_constraint(comment='assumption')

prop = ProportionalLengthsProperty(B1.segment(H), B1.segment(B2), 1)

visualise(scene, prop, title='Problem 4.1.1', task=[
], reference='<a href="http://vivacognita.org/555geometry.html/_/4/4-1/41-1-r93">Problem 4.1.1</a> from the <a href="https://www.amazon.com/Geometry-Figures-Second-Arseniy-Akopyan/dp/1548710784">Akopyan\\\'s book</a> (case of acute triangle)')
