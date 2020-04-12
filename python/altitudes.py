from sandbox import Scene
from sandbox.explainer import Explainer
from sandbox.property import SimilarTrianglesProperty
from sandbox.property import AngleKindProperty, PointsCollinearityProperty
from sandbox.propertyset import ContradictionError
from sandbox.reason import Reason

scene = Scene()

A, B, C = scene.triangle(labels=('A', 'B', 'C'))
altitudeA = scene.altitude((A, B, C), A)
altitudeB = scene.altitude((A, B, C), B)
A1 = altitudeA.intersection_point(B.line_through(C), label='A1')
B1 = altitudeB.intersection_point(A.line_through(C), label='B1')

#B.angle(A, C).is_obtuse_constraint(comment='Test')
#C.angle(A, B).is_obtuse_constraint(comment='Test')
#C.angle(A, B).is_right_constraint(comment='Test')

prop = SimilarTrianglesProperty((A, B, C), (A1, B1, C))

def angles(context):
    collection = set()
    for ncl in [p for p in context.list(PointsCollinearityProperty) if not p.collinear]:
        collection.add(ncl.points[0].angle(ncl.points[1], ncl.points[2]))
        collection.add(ncl.points[1].angle(ncl.points[0], ncl.points[2]))
        collection.add(ncl.points[2].angle(ncl.points[0], ncl.points[1]))
    return [angle for angle in collection if context.angle_kind_property(angle) is None]

explainer0 = Explainer(scene)
explainer0.explain()
if explainer0.explained(prop):
    print('Explained: %s' % explainer0.explained(prop))
else:
    for angle in angles(explainer0.context):
        print('Trying variants for: %s' % angle)
        success_count = 0
        contradiction_count = 0
        for kind in AngleKindProperty.Kind:
            try:
                explainer = Explainer(scene, base=explainer0)
                assumption = AngleKindProperty(angle, kind)
                print('Assume: %s' % assumption)
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
