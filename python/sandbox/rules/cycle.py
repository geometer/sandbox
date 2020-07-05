from ..property import *
from ..util import Comment

from .abstract import Rule, accepts_auto, processed_cache, source_type

@source_type(SameOrOppositeSideProperty)
@processed_cache(set())
@accepts_auto
class CyclicOrderRule(Rule):
    def apply(self, prop):
        self.processed.add(prop)

        cycle0 = Cycle(*prop.segment.points, prop.points[0])
        cycle1 = Cycle(*prop.segment.points, prop.points[1])
        if not prop.same:
            cycle1 = cycle1.reversed
            pattern = '$%{line:line}$ separates $%{point:pt0}$ and $%{point:pt1}$'
        else:
            pattern = '$%{point:pt0}$ and $%{point:pt1}$ are on the same side of $%{line:line}$'
        comment = Comment(pattern, {'line': prop.segment, 'pt0': prop.points[0], 'pt1': prop.points[1]})
        yield (SameCyclicOrderProperty(cycle0, cycle1), comment, [prop])
        yield (SameCyclicOrderProperty(cycle0.reversed, cycle1.reversed), comment, [prop])

@processed_cache(set())
class RotatedAngleRule(Rule):
    def sources(self):
        return [(a0, a1) for a0, a1 in self.context.congruent_angles_with_vertex() if a0.vertex == a1.vertex and (a0, a1) not in self.processed]

    def apply(self, src):
        ang0, ang1 = src
        vertex = ang0.vertex
        pts0 = ang0.endpoints
        pts1 = ang1.endpoints
        if next((p for p in pts0 if p in pts1), None) is not None:
            self.processed.add(src)
            return
        co = self.context.same_cyclic_order_property(Cycle(vertex, *pts0), Cycle(vertex, *pts1))
        if co is None:
            pts1 = (pts1[1], pts1[0])
            co = self.context.same_cyclic_order_property(Cycle(vertex, *pts0), Cycle(vertex, *pts1))
        if co is None:
            return
        self.processed.add(src)
        ca = self.context.angle_ratio_property(ang0, ang1)
        new_angle0 = vertex.angle(pts0[0], pts1[0])
        new_angle1 = vertex.angle(pts0[1], pts1[1])
        yield (
            AngleRatioProperty(new_angle0, new_angle1, 1),
            Comment(
                '$%{angle:angle0}$ is $%{angle:angle1}$ rotated by $%{anglemeasure:rot_angle0} = %{anglemeasure:rot_angle1}$',
                {'angle0': new_angle0, 'angle1': new_angle1, 'rot_angle0': ang0, 'rot_angle1': ang1}
            ),
            [ca, co]
        )
