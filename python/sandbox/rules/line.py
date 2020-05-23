import itertools

from sandbox import Scene
from sandbox.property import *
from sandbox.util import LazyComment

from .abstract import Rule, SingleSourceRule

class CollinearityToSameLineRule(SingleSourceRule):
    property_type = PointsCollinearityProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = {}

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
                LineCoincidenceProperty(side0, side1, True),
                LazyComment('points %s, %s, and %s are collinear', *prop.points),
                [prop, eq0, eq1]
            )

        if mask != original:
            self.processed[prop] = mask

class CollinearityToPointOnLineRule(SingleSourceRule):
    property_type = PointsCollinearityProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = {}

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
                PointOnLineProperty(side, third, True),
                LazyComment('points %s, %s, and %s are collinear', third, *side.points),
                [prop, eq]
            )

        if mask != original:
            self.processed[prop] = mask

class NonCollinearityToDifferentLinesRule(SingleSourceRule):
    property_type = PointsCollinearityProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def accepts(self, prop):
        return not prop.collinear and prop not in self.processed

    def apply(self, prop):
        self.processed.add(prop)

        sides = Scene.Triangle(*prop.points).sides
        for side0, side1 in itertools.combinations(sides, 2):
            yield (
                LineCoincidenceProperty(side0, side1, False),
                LazyComment('points %s, %s, and %s are not collinear', *prop.points),
                [prop]
            )

class NonCollinearityToPointNotOnLineRule(SingleSourceRule):
    property_type = PointsCollinearityProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def accepts(self, prop):
        return not prop.collinear and prop not in self.processed

    def apply(self, prop):
        self.processed.add(prop)

        triangle = Scene.Triangle(*prop.points)
        for side, vertex in zip(triangle.sides, triangle.points):
            yield (
                PointOnLineProperty(side, vertex, False),
                LazyComment('points %s, %s, and %s are not collinear', vertex, *side.points),
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
                    LineCoincidenceProperty(key, seg, True),
                    LazyComment('non-coincident points %s and %s belong to %s', pt0, pt1, seg.as_line),
                    premises + [ne]
                )
