from ..property import *
from ..util import Comment

from .abstract import Rule, accepts_auto, processed_cache, source_type

@processed_cache(set())
class CongruentOrientedAnglesWithPerpendicularSidesRule(Rule):
    def sources(self):
        return self.context.congruent_oriented_angles()

    def apply(self, pair):
        key = frozenset(pair)
        if key in self.processed:
            return
        a0, a1 = pair
        side0 = a0.vertex.segment(a0.endpoints[0])
        side1 = a1.vertex.segment(a1.endpoints[0])
        perp = self.context[PerpendicularSegmentsProperty(side0, side1)]
        if perp is None:
            return
        self.processed.add(key)
        cong = self.context.congruent_oriented_angles_property(a0, a1)
        yield (
            PerpendicularSegmentsProperty(
                a0.vertex.segment(a0.endpoints[1]),
                a1.vertex.segment(a1.endpoints[1])
            ),
            Comment(
                'congruent oriented angles $%{orientedangle:a0}$ and $%{orientedangle:a1}$ with perpendicular sides $%{segment:side0}$ and $%{segment:side1}$',
                {'a0': a0, 'a1': a1, 'side0': side0, 'side1': side1}
            ),
            [cong, perp]
        )

@source_type(LineAndTwoPointsProperty)
@processed_cache(set())
class CyclicOrderRule(Rule):
    def apply(self, prop):
        line = self.context.line_for_key(prop.line_key)
        pt_set = frozenset(prop.points)
        for segment in line.segments:
            key = (segment, pt_set)
            if key in self.processed:
                continue
            self.processed.add(key)

            if segment == prop.line_key:
                premises = [prop]
            else:
                premises = [self.context.line_and_two_points_property(segment, *prop.points)]
            cycle0 = prop.points[0].cycle(*segment.points)
            cycle1 = prop.points[1].cycle(*segment.points)
            if not prop.same_side:
                cycle1 = cycle1.reversed
                pattern = '$%{line:line}$ separates $%{point:pt0}$ and $%{point:pt1}$'
            else:
                pattern = '$%{point:pt0}$ and $%{point:pt1}$ are on the same side of $%{line:line}$'
            comment = Comment(pattern, {'line': segment, 'pt0': prop.points[0], 'pt1': prop.points[1]})
            yield (SameCyclicOrderProperty(cycle0, cycle1), comment, premises)
            yield (SameCyclicOrderProperty(cycle0.reversed, cycle1.reversed), comment, premises)

@processed_cache(set())
class RotatedAngleRule(Rule):
    def sources(self):
        return [(a0, a1) for a0, a1 in self.context.congruent_oriented_angles() if a0.vertex == a1.vertex]

    def apply(self, src):
        ang0, ang1 = src

        key = frozenset((ang0, ang1))
        if key in self.processed:
            return
        self.processed.add(key)

        vertex = ang0.vertex
        pts0 = ang0.endpoints
        pts1 = ang1.endpoints
        if next((p for p in pts0 if p in pts1), None) is not None:
            return
        if self.context.collinearity(vertex, *pts0):
            return
        eq = self.context.congruent_oriented_angles_property(ang0, ang1)
        new_angle0 = vertex.angle(pts0[0], pts1[0])
        new_angle1 = vertex.angle(pts0[1], pts1[1])
        yield (
            AngleRatioProperty(new_angle0, new_angle1, 1),
            Comment(
                '$%{angle:angle1}$ is $%{angle:angle0}$ rotated by $%{orientedangle:rot_angle0} \\cong %{orientedangle:rot_angle1}$',
                {'angle0': new_angle0, 'angle1': new_angle1, 'rot_angle0': ang0, 'rot_angle1': ang1}
            ),
            [eq]
        )
