import itertools

from sandbox.property import *
from sandbox.util import LazyComment

from .abstract import SingleSourceRule

class SideProductsInSimilarTrianglesRule(SingleSourceRule):
    property_type = SimilarTrianglesProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = {}

    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0x7:
            return

        sides0 = prop.triangle0.sides
        sides1 = prop.triangle1.sides
        original = mask
        for i, j in itertools.combinations(range(0, 3), 2):
            bit = 1 << next(k for k in range(0, 3) if k not in (i, j))
            if mask & bit:
                continue
            segments = (sides0[i], sides0[j], sides1[i], sides1[j])
            for inds in [(0, 1, 2, 3), (0, 2, 1, 3), (1, 0, 3, 2), (2, 0, 3, 1)]:
                if not self.context.length_ratios_are_equal(*[segments[n] for n in inds]):
                    break
            else:
                continue
            mask |= bit
            if segments[0] != segments[1] and segments[0] != segments[2] and \
               segments[1] != segments[3] and segments[2] != segments[3]:
                yield (
                    EqualLengthProductsProperty(*segments),
                    LazyComment('ratios of sides in similar %s and %s', prop.triangle0, prop.triangle1),
                    [prop]
                )

        if original != mask:
            self.processed[prop] = mask

class CorrespondingAnglesInSimilarTrianglesRule(SingleSourceRule):
    property_type = SimilarTrianglesProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = {}

    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0x7:
            return

        ne0 = []
        ne1 = []
        sides0 = prop.triangle0.sides
        sides1 = prop.triangle1.sides
        for i in range(0, 3):
            ne0.append(self.context.not_equal_property(*sides0[i].points))
            ne1.append(self.context.not_equal_property(*sides1[i].points))

        angles0 = prop.triangle0.angles
        angles1 = prop.triangle1.angles
        original = mask
        for i in range(0, 3):
            bit = 1 << i
            if mask & bit:
                continue
            if angles0[i] == angles1[i]:
                mask |= bit
                continue
            ne = []
            for j in range(0, 3):
                if i != j:
                    if ne0[j]:
                        ne.append(ne0[j])
                    if ne1[j]:
                        ne.append(ne1[j])
            if len(ne) < 3:
                continue
            mask |= bit
            yield (
                AngleRatioProperty(angles0[i], angles1[i], 1),
                LazyComment('corresponding angles in similar %s and %s', prop.triangle0, prop.triangle1),
                [prop] + ne
            )

        if original != mask:
            self.processed[prop] = mask

class BaseAnglesOfIsoscelesRule(SingleSourceRule):
    property_type = IsoscelesTriangleProperty

    def apply(self, prop):
        if prop.reason.obsolete:
            return
        yield (
            AngleRatioProperty(
                prop.base.points[0].angle(prop.apex, prop.base.points[1]),
                prop.base.points[1].angle(prop.apex, prop.base.points[0]),
                1
            ),
            LazyComment('base angles of isosceles %s', prop.triangle),
            [prop]
        )

class LegsOfIsoscelesRule(SingleSourceRule):
    property_type = IsoscelesTriangleProperty

    def apply(self, prop):
        if prop.reason.obsolete:
            return
        yield (
            ProportionalLengthsProperty(
                prop.apex.segment(prop.base.points[0]),
                prop.apex.segment(prop.base.points[1]),
                1
            ),
            LazyComment('Legs of isosceles %s', prop.triangle),
            [prop]
        )

class CorrespondingAnglesInCongruentTrianglesRule(SingleSourceRule):
    property_type = CongruentTrianglesProperty

    def apply(self, prop):
        ncl = self.context.collinearity_property(*prop.triangle0.points)
        if ncl is None:
            ncl = self.context.collinearity_property(*prop.triangle1.points)
        if ncl is None or ncl.collinear or prop.reason.obsolete and ncl.reason.obsolete:
            return
        angles0 = prop.triangle0.angles
        angles1 = prop.triangle1.angles
        for i in range(0, 3):
            if angles0[i] != angles1[i]:
                yield (
                    AngleRatioProperty(angles0[i], angles1[i], 1),
                    LazyComment('corresponding angles in congruent %s and %s', prop.triangle0, prop.triangle1),
                    [prop, ncl]
                )

class CorrespondingSidesInCongruentTrianglesRule(SingleSourceRule):
    property_type = CongruentTrianglesProperty

    def apply(self, prop):
        if prop.reason.obsolete:
            return
        sides0 = prop.triangle0.sides
        sides1 = prop.triangle1.sides
        for i in range(0, 3):
            segment0 = sides0[i]
            segment1 = sides1[i]
            if segment0 != segment1:
                yield (
                    ProportionalLengthsProperty(segment0, segment1, 1),
                    LazyComment('corresponding sides in congruent %s and %s', prop.triangle0, prop.triangle1),
                    [prop]
                )

class CorrespondingSidesInSimilarTrianglesRule(SingleSourceRule):
    property_type = SimilarTrianglesProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = {}

    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0x7:
            return
        sides0 = prop.triangle0.sides
        sides1 = prop.triangle1.sides
        original = mask
        for i in range(0, 3):
            if mask & (1 << i):
                continue
            lr, ratio = self.context.length_ratio_property_and_value(sides0[i], sides1[i], True)
            if lr is None:
                continue
            mask |= (1 << i)
            if ratio == 1:
                mask = 0x7
                break
            for j in [j for j in range(0, 3) if j != i]:
                yield (
                    ProportionalLengthsProperty(sides0[j], sides1[j], ratio),
                    'Ratios of sides in similar triangles',
                    [prop, lr]
                )

        if original != mask:
            self.processed[prop] = mask

class EquilateralTriangleAnglesRule(SingleSourceRule):
    property_type = EquilateralTriangleProperty

    def apply(self, prop):
        ne = None
        for side in prop.triangle.sides:
            ne = self.context.not_equal_property(*side.points)
            if ne:
                break
        else:
            return
        if prop.reason.obsolete and ne.reason.obsolete:
            return
        for angle in prop.triangle.angles:
            yield (
                AngleValueProperty(angle, 60),
                LazyComment('angle of non-degenerate equilateral %s', prop.triangle),
                [prop]
            )

class EquilateralTriangleSidesRule(SingleSourceRule):
    property_type = EquilateralTriangleProperty

    def apply(self, prop):
        if prop.reason.obsolete:
            return
        sides = prop.triangle.sides
        for side0, side1 in itertools.combinations(prop.triangle.sides, 2):
            yield (
                ProportionalLengthsProperty(side0, side1, 1),
                LazyComment('Sides of equilateral %s', prop.triangle),
                [prop]
            )
