import itertools

from .. import Scene
from ..property import *
from ..util import other_point

from .abstract import Rule, processed_cache, source_type

@source_type(PointsCollinearityProperty)
@processed_cache({})
class CollinearityToSameLineRule(Rule):
    def accepts(self, prop):
        return prop.collinear

    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0x7:
            return

        sides = Scene.Triangle(*prop.points).sides
        eqs = [(side, self.context.coincidence_property(*side.points)) for side in sides]
        original = mask
        for ((side0, eq0), (side1, eq1)), bit in zip(itertools.combinations(eqs, 2), (1, 2, 4)):
            if mask & bit:
                continue
            if not eq0 or not eq1:
                continue
            mask |= bit
            if eq0.coincident or eq1.coincident:
                continue
            yield (
                LinesCoincidenceProperty(side0, side1, True),
                Comment(
                    'points $%{point:pt0}$, $%{point:pt1}$, and $%{point:pt2}$ are collinear',
                    {'pt0': prop.points[0], 'pt1': prop.points[1], 'pt2': prop.points[2]}
                ),
                [prop, eq0, eq1]
            )

        if mask != original:
            self.processed[prop] = mask

@source_type(PointsCollinearityProperty)
@processed_cache({})
class CollinearityToPointOnLineRule(Rule):
    def accepts(self, prop):
        return prop.collinear

    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0x7:
            return

        sides = Scene.Triangle(*prop.points).sides
        eqs = [(side, self.context.coincidence_property(*side.points)) for side in sides]
        original = mask
        for (side, eq), bit in zip(eqs, (1, 2, 4)):
            if mask & bit:
                continue
            if not eq:
                continue
            mask |= bit
            if eq.coincident:
                continue
            third = next(pt for pt in prop.points if pt not in side.points)
            yield (
                PointOnLineProperty(third, side, True),
                Comment(
                    'points $%{point:pt0}$, $%{point:pt1}$, and $%{point:pt2}$ are collinear',
                    {'pt0': third, 'pt1': side.points[0], 'pt2': side.points[1]}
                ),
                [prop, eq]
            )

        if mask != original:
            self.processed[prop] = mask

@processed_cache(set())
class NonCollinearityToDifferentLinesRule(Rule):
    def sources(self):
        props = []
        for p in self.context.list(PointsCollinearityProperty):
            if p.collinear:
                continue
            key = frozenset(p.points) # same as p.property_key
            if key in self.processed:
                continue
            self.processed.add(key)
            props.append(p)

        for line in self.context.lines:
            for seg in line.segments:
                for pt in line.points_not_on:
                    key = frozenset((*seg.points, pt))
                    if key in self.processed:
                        continue
                    self.processed.add(key)
                    props.append(self.context.collinearity_property(*seg.points, pt))

        return props

    def apply(self, prop):
        sides = Scene.Triangle(*prop.points).sides
        for side0, side1 in itertools.combinations(sides, 2):
            yield (
                LinesCoincidenceProperty(side0, side1, False),
                Comment(
                    'points $%{point:pt0}$, $%{point:pt1}$, and $%{point:pt2}$ are not collinear',
                    {'pt0': prop.points[0], 'pt1': prop.points[1], 'pt2': prop.points[2]}
                ),
                [prop]
            )

@source_type(PointsCollinearityProperty)
@processed_cache(set())
class NonCollinearityToDifferentLinesRule2(Rule):
    def accepts(self, prop):
        return not prop.collinear

    def apply(self, prop):
        triangle = Scene.Triangle(*prop.points)
        for pt, segment in zip(triangle.points, triangle.sides):
            for nc in self.context.list(PointsCoincidenceProperty, [pt]):
                if nc.coincident:
                    continue
                other = other_point(nc.points, pt)
                if other in segment.points:
                    continue
                key = (prop, nc)
                if key in self.processed:
                    continue
                self.processed.add(key)
                yield (
                    LinesCoincidenceProperty(segment, pt.segment(other), False),
                    Comment(
                        'points $%{point:pt0}$, $%{point:pt1}$, and $%{point:pt2}$ are not collinear',
                        {'pt0': segment.points[0], 'pt1': segment.points[1], 'pt2': pt}
                    ),
                    [prop]
                )

@source_type(PointsCollinearityProperty)
@processed_cache(set())
class NonCollinearityToPointNotOnLineRule(Rule):
    def accepts(self, prop):
        return not prop.collinear and prop not in self.processed

    def apply(self, prop):
        self.processed.add(prop)

        triangle = Scene.Triangle(*prop.points)
        for side, vertex in zip(triangle.sides, triangle.points):
            yield (
                PointOnLineProperty(vertex, side, False),
                Comment(
                    'points $%{point:pt0}$, $%{point:pt1}$, and $%{point:pt2}$ are not collinear',
                    {'pt0': vertex, 'pt1': side.points[0], 'pt2': side.points[1]}
                ),
                [prop]
            )

class MissingLineKeysRule(Rule):
    def sources(self):
        return self.context.lines

    def apply(self, line):
        segments = set(line.segments)
        for pt0, pt1 in itertools.combinations(line.points_on, 2):
            key = pt0.segment(pt1)
            if key in segments:
                continue
            ne = self.context.coincidence_property(pt0, pt1)
            if ne is None or ne.coincident:
                continue
            for seg in segments:
                premises = []
                if pt0 not in seg.points:
                    premises.append(self.context.point_on_line_property(seg, pt0))
                if pt1 not in seg.points:
                    premises.append(self.context.point_on_line_property(seg, pt1))
                yield (
                    LinesCoincidenceProperty(key, seg, True),
                    Comment(
                        'non-coincident points $%{point:pt0}$ and $%{point:pt1}$ belong to $%{line:line}$',
                        {'pt0': pt0, 'pt1': pt1, 'line': seg}
                    ),
                    premises + [ne]
                )
