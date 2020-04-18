import itertools

from sandbox.property import *
from sandbox.util import LazyComment

from .abstract import SingleSourceRule

class SideProductsInSimilarTrianglesRule(SingleSourceRule):
    property_type = SimilarTrianglesProperty

    def apply(self, prop):
        sides0 = prop.triangle0.sides
        sides1 = prop.triangle1.sides
        for i, j in itertools.combinations(range(0, 3), 2):
            segments = (sides0[i], sides0[j], sides1[i], sides1[j])
            found_four_ratio_equalities = True
            for inds in [(0, 1, 2, 3), (0, 2, 1, 3), (1, 0, 3, 2), (2, 0, 3, 1)]:
                if not self.context.length_ratios_are_equal(*[segments[n] for n in inds]):
                    found_four_ratio_equalities = False
                    break
            if found_four_ratio_equalities:
                continue
            if segments[0] == segments[1]:
                yield (
                    ProportionalLengthsProperty(segments[2], segments[3], 1),
                    'Relation of sides in similar triangles',
                    [prop]
                )
            elif segments[0] == segments[2]:
                yield (
                    ProportionalLengthsProperty(segments[1], segments[3], 1),
                    'Relation of sides in similar triangles',
                    [prop]
                )
            elif segments[1] == segments[3]:
                yield (
                    ProportionalLengthsProperty(segments[0], segments[2], 1),
                    'Relation of sides in similar triangles',
                    [prop]
                )
            elif segments[2] == segments[3]:
                yield (
                    ProportionalLengthsProperty(segments[0], segments[1], 1),
                    'Relation of sides in similar triangles',
                    [prop]
                )
            else:
                yield (
                    EqualLengthProductsProperty(*segments),
                    'Relation of sides in similar triangles',
                    [prop]
                )

class CorrespondingAnglesInSimilarTrianglesRule(SingleSourceRule):
    property_type = SimilarTrianglesProperty

    def apply(self, prop):
        ne0 = []
        ne1 = []
        sides0 = prop.triangle0.sides
        sides1 = prop.triangle1.sides
        for i in range(0, 3):
            ne0.append(self.context.not_equal_property(*sides0[i].points))
            ne1.append(self.context.not_equal_property(*sides1[i].points))

        angles0 = prop.triangle0.angles
        angles1 = prop.triangle1.angles
        for i in range(0, 3):
            if angles0[i] == angles1[i]:
                continue
            ne = []
            for j in range(0, 3):
                if i != j:
                    if ne0[j]:
                        ne.append(ne0[j])
                    if ne1[j]:
                        ne.append(ne1[j])
            if len(ne) < 3 or prop.reason.obsolete and all(p.reason.obsolete for p in ne):
                continue
            yield (
                AngleRatioProperty(angles0[i], angles1[i], 1),
                'Corresponding non-degenerate angles in similar triangles',
                [prop] + ne
            )

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
            LazyComment('Base angles of isosceles %s', prop.triangle),
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