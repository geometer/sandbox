from runner import run_sample
from sandbox import Scene
from sandbox.explainer import Explainer
from sandbox.property import SimilarTrianglesProperty
from sandbox.property import AcuteAngleProperty, ObtuseAngleProperty, AngleValueProperty, PointsCollinearityProperty
from sandbox.reason import Reason

scene = Scene()

A, B, C = scene.triangle(labels=('A', 'B', 'C'))
altitudeA = scene.altitude((A, B, C), A)
altitudeB = scene.altitude((A, B, C), B)
A1 = altitudeA.intersection_point(B.line_through(C), label='A1')
B1 = altitudeB.intersection_point(A.line_through(C), label='B1')

B.angle(A, C).is_obtuse_constraint(comment='Test')
#C.angle(A, B).is_obtuse_constraint(comment='Test')
#C.angle(A, B).is_right_constraint(comment='Test')

prop = SimilarTrianglesProperty((A, B, C), (A1, B1, C))

def angles(context):
    collection = set()
    for ncl in [p for p in context.list(PointsCollinearityProperty) if not p.collinear]:
        collection.add(ncl.points[0].angle(ncl.points[1], ncl.points[2]))
        collection.add(ncl.points[1].angle(ncl.points[0], ncl.points[2]))
        collection.add(ncl.points[2].angle(ncl.points[0], ncl.points[1]))
    def in_use(angle):
        if AcuteAngleProperty(angle) in context:
            return True
        if ObtuseAngleProperty(angle) in context:
            return True
        if AngleValueProperty(angle, 90) in context:
            return True
        return False
    return [angle for angle in collection if not in_use(angle)]

explainer0 = Explainer(scene)
explainer0.explain()
if explainer0.explained(prop):
    print('Explained: %s' % explainer0.explained(prop))
else:
    for angle in angles(explainer0.context):
        for variant in (AngleValueProperty(angle, 90), AcuteAngleProperty(angle), ObtuseAngleProperty(angle)):
            print('With assumption: %s' % variant)
            explainer = Explainer(scene, base=explainer0)
            variant.reason = Reason(-2, -2, 'Variant', [])
            variant.reason.obsolete = False
            explainer.context.add(variant)
            explainer.explain()
            print('Explained: %s' % explainer.explained(prop))
