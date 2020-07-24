# Probably, these rules are to be removed; kept temporary for compatibility.

import itertools

from ..property import *
from ..util import Comment

from .abstract import Rule, processed_cache, source_type

@processed_cache(set())
class LineAndTwoAnglesRule(Rule):
    def sources(self):
        return [p for p in self.context.nondegenerate_angle_value_properties() \
            if p.angle.vertex and p.degree not in (0, 180)]

    def apply(self, prop):
        base = prop.angle
        for vec0, vec1 in [base.vectors, reversed(base.vectors)]:
            for pt in self.context.collinear_points(vec0.as_segment):
                col = self.context.collinearity_property(pt, *vec0.points)
                for angle in [pt.angle(vec1.end, p) for p in vec0.points]:
                    key = (base, pt, angle)
                    if key in self.processed:
                        continue
                    ka = self.context.angle_value_property(angle)
                    if ka is None:
                        continue
                    self.processed.add(key)
                    if ka.degree <= prop.degree:
                        continue
                    comment = Comment(
                        '$%{point:pt0}$, $%{point:pt1}$, $%{point:pt2}$ are collinear and $%{anglemeasure:angle0}$ > $%{anglemeasure:angle1}$',
                        {'pt0': pt, 'pt1': vec0.points[0], 'pt2': vec0.points[1], 'angle0': angle, 'angle1': base}
                    )
                    zero = base.vertex.angle(vec0.end, pt)
                    yield (AngleValueProperty(zero, 0), comment, [col, ka, prop])

@source_type(AngleKindProperty)
@processed_cache(set())
class LineAndAcuteAngleRule(Rule):
    def accepts(self, prop):
        return prop.angle.vertex and prop.kind == AngleKindProperty.Kind.acute

    def apply(self, prop):
        base = prop.angle
        for vec0, vec1 in [base.vectors, reversed(base.vectors)]:
            for pt in self.context.collinear_points(vec0.as_segment):
                col = self.context.collinearity_property(pt, *vec0.points)
                for angle in [pt.angle(vec1.end, p) for p in vec0.points]:
                    key = (base, pt, angle)
                    if key in self.processed:
                        continue
                    ka = self.context.angle_value_property(angle)
                    if ka is None:
                        continue
                    self.processed.add(key)
                    if ka.degree < 90:
                        continue
                    comment = Comment(
                        '$%{point:pt0}$, $%{point:pt1}$, $%{point:pt2}$ are collinear, $%{angle:base}$ is acute, and $%{anglemeasure:angle} = %{degree:degree}$',
                        {
                            'pt0': pt,
                            'pt1': vec0.points[0],
                            'pt2': vec0.points[1],
                            'base': base,
                            'angle': angle,
                            'degree': ka.degree
                        }
                    )
                    zero = base.vertex.angle(vec0.end, pt)
                    yield (AngleValueProperty(zero, 0), comment, [col, prop, ka])
