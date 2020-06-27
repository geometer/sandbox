import itertools

from ..property import *
from ..util import LazyComment, Comment

from .abstract import Rule

class CyclicQuadrilateralRule(Rule):
    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def sources(self):
        right_angles = self.context.angle_value_properties_for_degree(90, lambda a: a.vertex)
        return itertools.combinations(right_angles, 2)

    def apply(self, src):
        key = frozenset(src)
        if key in self.processed:
            return

        av0, av1 = src
        endpoints = av0.angle.endpoints
        if set(endpoints) != set(av1.angle.endpoints):
            self.processed.add(key)
            return

        oppo0 = self.context.two_points_relatively_to_line_property(endpoints[0].segment(endpoints[1]), av0.angle.vertex, av1.angle.vertex)
        oppo1 = self.context.two_points_relatively_to_line_property(av0.angle.vertex.segment(av1.angle.vertex), *endpoints)
        if oppo0 is None and oppo1 is None:
            return
        self.processed.add(key)
        for oppo in filter(None, (oppo0, oppo1)):
            if oppo.same:
                return
            yield (
                ConcyclicPointsProperty(av0.angle.vertex, av1.angle.vertex, *endpoints),
                Comment(
                    'convex quadrilateral $%{polygon:quad}$ with two right angles $%{angle:a0}$ and $%{angle:a1}$ is cyclic',
                    {
                        'quad': Scene.Polygon(av0.angle.vertex, endpoints[0], av1.angle.vertex, endpoints[1]),
                        'a0': av0.angle,
                        'a1': av1.angle
                    }
                ),
                [av0, av1, oppo]
            )
