from sandbox import Scene
from sandbox.property import PointOnLineProperty
from sandbox.util import LazyComment

from visualiser import visualise

scene = Scene()

triangle = scene.nondegenerate_triangle(labels=('A', 'B', 'C'))
A, B, C = triangle.points
altitudeA = scene.altitude(triangle, A)
altitudeB = scene.altitude(triangle, B)
altitudeC = scene.altitude(triangle, C)
D = altitudeA.intersection_point(B.line_through(C), label='D')
E = altitudeB.intersection_point(A.line_through(C), label='E')
F = altitudeC.intersection_point(A.line_through(B), label='F')
H = altitudeA.intersection_point(altitudeB, label='H')
#A.angle(B, C).is_obtuse_constraint()
A.angle(B, C).is_acute_constraint(comment='assumption')
B.angle(A, C).is_acute_constraint(comment='assumption')
C.angle(A, B).is_acute_constraint(comment='assumption')

prop = PointOnLineProperty(C.segment(H), F, True)

visualise(scene, prop, title='Altitudes of (acute) triangle', task=[
    LazyComment('%s is a non-degenerate triangle', triangle),
    LazyComment('%s is an altitude of %s', A.segment(D), triangle),
    LazyComment('%s is an altitude of %s', B.segment(E), triangle),
    LazyComment('%s is an altitude of %s', C.segment(F), triangle),
    LazyComment('%s is the intersection of %s and %s', H, A.segment(D), B.segment(E)),
    LazyComment('%s is acute', A.angle(B, C)),
    LazyComment('%s is acute', B.angle(A, C)),
    LazyComment('%s is acute', C.angle(A, B)),
    LazyComment('Prove, that %s lies on %s', F, C.segment(H))
]);
