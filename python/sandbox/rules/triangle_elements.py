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
            if segments[0] != segments[1] and segments[0] != segments[2] and \
               segments[1] != segments[3] and segments[2] != segments[3]:
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

class CorrespondingAnglesInCongruentTrianglesRule(SingleSourceRule):
    property_type = CongruentTrianglesProperty

    def apply(self, prop):
        ncl = self.context.not_collinear_property(*prop.triangle0.points)
        if ncl is None:
            ncl = self.context.not_collinear_property(*prop.triangle1.points)
        if ncl is None or prop.reason.obsolete and ncl.reason.obsolete:
            return
        angles0 = prop.triangle0.angles
        angles1 = prop.triangle1.angles
        for i in range(0, 3):
            if angles0[i] != angles1[i]:
                yield (
                    AngleRatioProperty(angles0[i], angles1[i], 1),
                    'Corresponding angles in congruent non-degenerate triangles',
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
                    'Corresponding sides in congruent triangles',
                    [prop]
                )

class CorrespondingSidesInSimilarTrianglesRule(SingleSourceRule):
    property_type = SimilarTrianglesProperty

    def apply(self, prop):
        sides0 = prop.triangle0.sides
        sides1 = prop.triangle1.sides
        for i in range(0, 3):
            lr, ratio = self.context.length_ratio_property_and_value(sides0[i], sides1[i], True)
            if lr is None:
                continue
            if ratio == 1 or prop.reason.obsolete and lr.reason.obsolete:
                break
            for j in [j for j in range(0, 3) if j != i]:
                yield (
                    ProportionalLengthsProperty(sides0[j], sides1[j], ratio),
                    'Ratios of sides in similar triangles',
                    [prop, lr]
                )
            break

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
                LazyComment('Angle of non-degenerate equilateral %s', prop.triangle),
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
