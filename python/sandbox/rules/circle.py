from sandbox.property import *
from sandbox.util import LazyComment

from .abstract import Rule, SingleSourceRule

class TrivialPointOnCircleRule(SingleSourceRule):
    property_type = PointsCollinearityProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def accepts(self, prop):
        return not prop.collinear and prop not in self.processed

    def apply(self, prop):
        self.processed.add(prop)
        for pt in prop.points:
            yield(
                PointAndCircleProperty(pt, *prop.points, 0),
                LazyComment('%s %s %s is a circle goes through %s', *prop.points, pt),
                [prop]
            )

class InscribedAnglesWithCommonCircularArcRule(SingleSourceRule):
    property_type = ConcyclicPointsProperty

    def apply(self, prop):
        for inds0, inds1 in [((0, 1), (2, 3)), ((0, 2), (1, 3)), ((0, 3), (1, 2))]:
            pair0 = [prop.points[i] for i in inds0]
            pair1 = [prop.points[i] for i in inds1]
            for p0, p1 in ((pair0, pair1), (pair1, pair0)):
                sos = self.context.two_points_and_line_configuration_property(
                    p0[0].segment(p0[1]), *p1
                )
                if sos is None or prop.reason.obsolete and sos.reason.obsolete:
                    continue
                ang0 = p0[0].angle(*p1)
                ang1 = p0[1].angle(*p1)
                if sos.same:
                    yield (
                        AngleRatioProperty(ang0, ang1, 1),
                        LazyComment('%s and %s are inscribed and subtend the same arc', ang0, ang1),
                        [prop, sos]
                    )
                else:
                    # TODO: sum = 180 degree
                    pass
                ang0 = p1[0].angle(*p0)
                ang1 = p1[1].angle(*p0)
                if sos.same:
                    yield (
                        AngleRatioProperty(ang0, ang1, 1),
                        LazyComment('%s and %s are inscribed and subtend the same arc', ang0, ang1),
                        [prop, sos]
                    )
                else:
                    # TODO: sum = 180 degree
                    pass
