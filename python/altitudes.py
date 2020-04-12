from sandbox import Scene
from sandbox.explainer import Explainer
from sandbox.property import SimilarTrianglesProperty
from sandbox.property import AcuteAngleProperty, ObtuseAngleProperty, AngleValueProperty, PointsCollinearityProperty
from sandbox.propertyset import ContradictionError
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
        print('Trying variants for: %s' % angle)
        success_count = 0
        contradiction_count = 0
        for assumption in (AngleValueProperty(angle, 90), AcuteAngleProperty(angle), ObtuseAngleProperty(angle)):
            try:
                explainer = Explainer(scene, base=explainer0)
                assumption.reason = Reason(-2, -2, 'Assumption', [])
                assumption.reason.obsolete = False
                explainer.context.add(assumption)
                explainer.explain()
                if explainer.explained(prop):
                    success_count += 1
                else:
                    break
            except ContradictionError as error:
                contradiction_count += 1
        if success_count > 0 and success_count + contradiction_count == 3:
            print('Success: %s proof(s), %s contradiction(s) found' % (success_count, contradiction_count))
        else:
            print('Failed: %s proof(s), %s contradiction(s) found' % (success_count, contradiction_count))
