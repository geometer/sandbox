import itertools

from sandbox.core import CoreScene
from sandbox.property import *
from sandbox.scene import Triangle
from sandbox.util import LazyComment

from .abstract import Rule, SingleSourceRule, RuleWithHints

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

class SimilarTrianglesByTwoAnglesRule(RuleWithHints):
    property_type = SimilarTrianglesProperty

    def apply(self, prop):
        ncl = self.context.not_collinear_property(*prop.triangle0.points)
        non_degenerate = prop.triangle0
        if ncl is None:
            ncl = self.context.not_collinear_property(*prop.triangle1.points)
            non_degenerate = prop.triangle1
        if ncl is None:
            return

        angles0 = prop.triangle0.angles
        angles1 = prop.triangle1.angles

        cas = []
        ca = self.context.angle_ratio_property(angles0[0], angles1[0])
        if ca:
            #TODO: report contradiction if ca.value != 1
            cas.append(ca)
        ca = self.context.angle_ratio_property(angles0[1], angles1[1])
        if ca:
            #TODO: report contradiction if ca.value != 1
            cas.append(ca)
        if len(cas) == 0:
            return
        if len(cas) == 1:
            ca = self.context.angle_ratio_property(angles0[2], angles1[2])
            if ca:
                #TODO: report contradiction if ca.value != 1
                cas.append(ca)

        if len(cas) == 2:
            yield (
                prop,
                LazyComment('Two pairs of congruent angles, and %s is non-degenerate', non_degenerate),
                cas + [ncl]
            )

class CongruentTrianglesByAngleAndTwoSidesRule(RuleWithHints):
    property_type = CongruentTrianglesProperty

    def apply(self, prop):
        angles0 = prop.triangle0.angles
        angles1 = prop.triangle1.angles
        sides0 = prop.triangle0.sides
        sides1 = prop.triangle1.sides

        def congruent_segments(seg0, seg1):
            if seg0 == seg1:
                return True
            return self.context.congruent_segments_property(seg0, seg1, allow_zeroes=True)

        for i in range(0, 3):
            ang0, ang1 = angles0[i], angles1[i]
            ca = self.context.angle_ratio_property(ang0, ang1)
            if ca is None:
                continue
            # TODO: report contradiction in ca.value != 1
            j, k = (i + 1) % 3, (i + 2) % 3
            rsn0 = congruent_segments(sides0[j], sides1[j])
            if rsn0 is None:
                continue
            rsn1 = congruent_segments(sides0[k], sides1[k])
            if rsn1 is None:
                continue
            if rsn0 == True:
                comment = LazyComment('Common side %s, pair of congruent sides, and angle between the sides', sides0[j])
                premises = [rsn1, ca]
            elif rsn1 == True:
                comment = LazyComment('Common side %s, pair of congruent sides, and angle between the sides', sides0[k])
                premises = [rsn0, ca]
            else:
                comment = 'Two pairs of congruent sides, and angle between the sides'
                premises = [rsn0, rsn1, ca]
            yield (prop, comment, premises)
            return

class SimilarTrianglesByAngleAndTwoSidesRule(RuleWithHints):
    property_type = SimilarTrianglesProperty

    def apply(self, prop):
        angles0 = prop.triangle0.angles
        angles1 = prop.triangle1.angles
        sides0 = prop.triangle0.sides
        sides1 = prop.triangle1.sides
        for i in range(0, 3):
            ang0, ang1 = angles0[i], angles1[i]
            ca = self.context.angle_ratio_property(ang0, ang1)
            if ca is None:
                continue
            # TODO: report contradiction in ca.value != 1
            j, k = (i + 1) % 3, (i + 2) % 3
            segments = (sides0[j], sides0[k], sides1[j], sides1[k])
            for inds in [(0, 1, 2, 3), (0, 2, 1, 3), (1, 0, 3, 2), (2, 0, 3, 1)]:
                elr = self.context.equal_length_ratios_property(*[segments[n] for n in inds])
                if elr:
                    break
            else:
                continue
            yield (
                prop,
                'Two pairs of sides with the same ratio, and angle between the sides',
                [elr, ca]
            )
            return

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

class SimilarTrianglesWithCongruentSideRule(RuleWithHints):
    property_type = CongruentTrianglesProperty

    def apply(self, prop):
        similar = self.context[SimilarTrianglesProperty(prop.triangle0, prop.triangle1)]
        if not similar:
            return
        sides0 = prop.triangle0.sides
        sides1 = prop.triangle1.sides
        for i in range(0, 3):
            if sides0[i] == sides1[i]:
                cs = sides0[i]
                break
        else:
            for i in range(0, 3):
                cs = self.context.congruent_segments_property(sides0[i], sides1[i], allow_zeroes=True)
                if cs:
                    break
            else:
                return

        if isinstance(cs, CoreScene.Segment):
            yield (
                prop,
                LazyComment('Similar triangles with common side %s', cs),
                [similar]
            )
        else:
            yield (
                prop,
                'Similar triangles with congruent corresponding sides',
                [similar, cs]
            )

class CongruentTrianglesByThreeSidesRule(RuleWithHints):
    property_type = CongruentTrianglesProperty

    def apply(self, prop):
        sides0 = prop.triangle0.sides
        sides1 = prop.triangle1.sides
        premises = []
        common_side = None
        for side0, side1 in zip(sides0, sides1):
            if side0 == side1:
                common_side = side0
            else:
                ratio_prop = self.context.congruent_segments_property(side0, side1, allow_zeroes=True)
                if ratio_prop:
                    premises.append(ratio_prop)
                else:
                    return

        if common_side:
            yield (
                prop,
                LazyComment('Common side %s, two pairs of congruent sides', common_side),
                premises
            )
        else:
            yield (
                prop,
                'Three pairs of congruent sides',
                premises
            )

class SimilarTrianglesByThreeSidesRule(RuleWithHints):
    property_type = SimilarTrianglesProperty

    def apply(self, prop):
        sides0 = prop.triangle0.sides
        sides1 = prop.triangle1.sides
        premises = []
        failures = 0
        for i, j in [(0, 1), (0, 2), (1, 2)]:
            segments = (sides0[i], sides0[j], sides1[i], sides1[j])
            for inds in [(0, 1, 2, 3), (0, 2, 1, 3), (1, 0, 3, 2), (2, 0, 3, 1)]:
                elr = self.context.equal_length_ratios_property(*[segments[n] for n in inds])
                if elr:
                    premises.append(elr)
                    break
            else:
                failures += 1
                if failures == 2:
                    return

        yield (prop, 'Same sides ratios', premises)

class EquilateralTriangleByThreeSidesRule(RuleWithHints):
    property_type = EquilateralTriangleProperty

    def apply(self, prop):
        sides = prop.triangle.sides

        cs0 = self.context.congruent_segments_property(sides[0], sides[1], allow_zeroes=True)
        cs1 = self.context.congruent_segments_property(sides[0], sides[2], allow_zeroes=True)
        if cs0 and cs1:
            yield (prop, 'Congruent sides', [cs0, cs1])
        elif cs0:
            cs2 = self.context.congruent_segments_property(sides[1], sides[2], allow_zeroes=True)
            if cs2:
                yield (prop, 'Congruent sides', [cs0, cs2])
        elif cs1:
            cs2 = self.context.congruent_segments_property(sides[1], sides[2], allow_zeroes=True)
            if cs2:
                yield (prop, 'Congruent sides', [cs1, cs2])

class IsoscelesTriangleByConrguentLegsRule(RuleWithHints):
    property_type = IsoscelesTriangleProperty

    def apply(self, prop):
        ne = self.context.not_equal_property(*prop.base.points)
        if ne is None:
            return
        cs = self.context.congruent_segments_property(
            prop.apex.segment(prop.base.points[0]),
            prop.apex.segment(prop.base.points[1]),
            True
        )
        if cs is None:
            return
        yield (prop, 'Congruent legs', [cs, ne])

class IsoscelesTriangleByConrguentBaseAnglesRule(RuleWithHints):
    property_type = IsoscelesTriangleProperty

    def apply(self, prop):
        nc = self.context.not_collinear_property(prop.apex, *prop.base.points)
        if nc is None:
            return
        ca = self.context.angle_ratio_property(
            prop.base.points[0].angle(prop.apex, prop.base.points[1]),
            prop.base.points[1].angle(prop.apex, prop.base.points[0])
        )
        if ca is None:
            return
        yield (prop, 'Congruent base angles', [ca, nc])
