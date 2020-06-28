import itertools
import sympy as sp

from ..property import *
from ..util import Comment

from .abstract import Rule, SingleSourceRule

class ConvexQuadrilateralRule(Rule):
    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def sources(self):
        return [p for p in self.context.list(NondegenerateSquareProperty) if p not in self.processed]

    def apply(self, prop):
        self.processed.add(prop)

        comment = Comment('$%{polygon:square}$ is a non-degenerate square', {'square': prop.square})
        points = prop.square.points * 2
        for i in range(0, 4):
            pts = [points[j] for j in range(i, i + 4)]
            yield (
                SameOrOppositeSideProperty(pts[0].segment(pts[1]), pts[2], pts[3], True),
                comment,
                [prop]
            )
        for i in range(0, 2):
            pts = [points[j] for j in range(i, i + 4)]
            yield (
                SameOrOppositeSideProperty(pts[0].segment(pts[2]), pts[1], pts[3], False),
                comment,
                [prop]
            )

class SquareRule(Rule):
    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def sources(self):
        return [p for p in self.context.list(SquareProperty) + self.context.list(NondegenerateSquareProperty) if p not in self.processed]

    def apply(self, prop):
        self.processed.add(prop)

        sq = prop.square
        params = {'square': sq}
        diagonals = [sq.points[0].segment(sq.points[2]), sq.points[1].segment(sq.points[3])]
        for side0, side1 in itertools.combinations(sq.sides, 2):
            yield (
                ProportionalLengthsProperty(side0, side1, 1),
                Comment('sides of square $%{polygon:square}$', params),
                [prop]
            )
        yield (
            ProportionalLengthsProperty(diagonals[0], diagonals[1], 1),
            Comment('diagonals of square $%{polygon:square}$', params),
            [prop]
        )
        for side, diagonal in itertools.product(sq.sides, diagonals):
            yield (
                ProportionalLengthsProperty(diagonal, side, sp.sqrt(2)),
                Comment('diagonal and side of square $%{polygon:square}$', params),
                [prop]
            )

        pts = sq.points * 2
        pattern = 'sides $%{segment:side0}$ and $%{segment:side1}$ of square $%{polygon:square}$'
        for i in range(0, 2):
            side0 = pts[i].vector(pts[i + 1])
            side1 = pts[i + 3].vector(pts[i + 2])
            yield (
                ParallelVectorsProperty(side0, side1),
                Comment(pattern, {'side0': side0, 'side1': side1, 'square': sq}),
                [prop]
            )
        for i in range(0, 4):
            side0 = pts[i + 1].segment(pts[i])
            side1 = pts[i + 1].segment(pts[i + 2])
            yield (
                PerpendicularSegmentsProperty(side0, side1),
                Comment(pattern, {'side0': side0, 'side1': side1, 'square': sq}),
                [prop]
            )

class SquareDegeneracyRule(SingleSourceRule):
    property_type = SquareProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = {}

    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0xF:
            return
        original = mask

        sq = prop.square
        params = {'square': sq}

        for index, side in enumerate(sq.sides):
            bit = 1 << index
            if mask & bit:
                continue
            ne = self.context.coincidence_property(*side.points)
            if ne is None:
                continue
            mask |= bit

            if ne.coincident:
                pattern = 'square $%{polygon:square}$ has zero-length side $%{segment:side}$'
            else:
                pattern = 'square $%{polygon:square}$ has nonzero-length side $%{segment:side}$'
            comment = Comment(pattern, {'square': sq, 'side': side})
            if ne.coincident:
                for other in [s for s in sq.sides if s != side]:
                    yield (
                        PointsCoincidenceProperty(*other.points, ne.coincident),
                        comment,
                        [prop, ne]
                    )
            else:
                yield (
                    NondegenerateSquareProperty(prop.square),
                    comment,
                    [prop, ne]
                )

        if mask != original:
            self.processed[prop] = mask

class NondegenerateSquareRule(SingleSourceRule):
    property_type = NondegenerateSquareProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def accepts(self, prop):
        return prop not in self.processed

    def apply(self, prop):
        self.processed.add(prop)

        sq = prop.square
        pts = sq.points * 2
        params = {'square': sq}
        diagonals = [pts[0].segment(pts[2]), pts[1].segment(pts[3])]

        comment = Comment('vertices of non-degenerate square $%{polygon:square}$', params)
        for pt0, pt1, pt2 in itertools.combinations(sq.points, 3):
            yield (PointsCollinearityProperty(pt0, pt1, pt2, False), comment, [prop])
        for side in sq.sides:
            yield (PointsCoincidenceProperty(*side.points, False), comment, [prop])
        comment = Comment('diagonals of non-degenerate square $%{polygon:square}$', params)
        for diagonal in diagonals:
            yield (PointsCoincidenceProperty(*diagonal.points, False), comment, [prop])
        comment = Comment('angle of non-degenerate square $%{polygon:square}$', params)
        for angle in sq.angles:
            yield (AngleValueProperty(angle, 90), comment, [prop])
        
        pattern = 'parallel sides $%{segment:side0}$ and $%{segment:side1}$ of non-degenerate square $%{polygon:square}$'
        for i in range(0, 2):
            side0 = pts[i].vector(pts[i + 1])
            side1 = pts[i + 3].vector(pts[i + 2])
            yield (
                AngleValueProperty(side0.angle(side1), 0),
                Comment(pattern, {'side0': side0, 'side1': side1, 'square': sq}),
                [prop]
            )
            yield (
                AngleValueProperty(side0.angle(side1.reversed), 180),
                Comment(pattern, {'side0': side0, 'side1': side1.reversed, 'square': sq}),
                [prop]
            )

        pattern = 'angle between side $%{segment:side}$ and diagonal $%{segment:diagonal}$ of non-degenerate square $%{polygon:square}$'
        for i in range(0, 4):
            diagonal = pts[i + 1].vector(pts[i + 3])
            for pt in (pts[i], pts[i + 2]):
                side = pts[i + 1].vector(pt)
                yield (
                    AngleValueProperty(side.angle(diagonal), 45),
                    Comment(pattern, {'side': side, 'diagonal': diagonal, 'square': sq}),
                    [prop]
                )
