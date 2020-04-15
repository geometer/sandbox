import itertools

from sandbox.property import *
from sandbox.scene import Triangle
from sandbox.util import LazyComment

from .abstract import Rule, SingleSourceRule

class SideProductsInSimilarTrianglesRule(SingleSourceRule):
    property_type = SimilarTrianglesProperty

    def apply(self, prop):
        sides0 = prop.triangle0.sides
        sides1 = prop.triangle1.sides
        for i, j in itertools.combinations(range(0, 3), 2):
            segments = (sides0[i], sides0[j], sides1[i], sides1[j])
            found_four_ratio_equalities = True
            for inds in [(0, 1, 2, 3), (0, 2, 1, 3), (1, 0, 3, 2), (1, 3, 0, 2)]:
                if not self.context.length_ratios_are_equal(*[segments[i] for i in inds]):
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

class SimilarTrianglesByTwoAnglesRule(Rule):
    def sources(self):
        groups = {}
        for a0, a1 in self.context.congruent_angles():
            if not a0.vertex or not a1.vertex or a0.point_set == a1.point_set:
                continue
            key = frozenset([a0.point_set, a1.point_set])
            lst = groups.get(key)
            if lst:
                lst.append((a0, a1))
            else:
                groups[key] = [(a0, a1)]

        pair_to_prop = {}
        def prop_for(pair):
            prop = pair_to_prop.get(pair)
            if prop is None:
                prop = self.context.angle_ratio_property(pair[0], pair[1])
                pair_to_prop[pair] = prop
            return prop

        for group in groups.values():
            for pair0, pair1 in itertools.combinations(group, 2):
                common = next((angle for angle in pair0 if angle in pair1), None)
                if common:
                    continue
                yield (prop_for(pair0), prop_for(pair1))

    def apply(self, src):
        ca0, ca1 = src

        ncl = self.context.not_collinear_property(*ca0.angle0.point_set)
        first_non_degenerate = True
        if ncl is None:
            ncl = self.context.not_collinear_property(*ca1.angle1.point_set)
            first_non_degenerate = False
        if ncl is None or ca0.reason.obsolete and ca1.reason.obsolete and ncl.reason.obsolete:
            return

        #this code ensures that vertices are listed in corresponding orders
        if ca0.angle0.point_set == ca1.angle0.point_set:
            tr0 = [ca0.angle0.vertex, ca1.angle0.vertex]
            tr1 = [ca0.angle1.vertex, ca1.angle1.vertex]
        else:
            tr0 = [ca0.angle0.vertex, ca1.angle1.vertex]
            tr1 = [ca0.angle1.vertex, ca1.angle0.vertex]
        tr0.append(next(p for p in ca0.angle0.point_set if p not in tr0))
        tr1.append(next(p for p in ca0.angle1.point_set if p not in tr1))
        if not self.context.triangles_are_similar(tuple(tr0), tuple(tr1)):
            yield (
                SimilarTrianglesProperty(tr0, tr1),
                LazyComment('Two pairs of congruent angles, and △ %s %s %s is non-degenerate', *(tr0 if first_non_degenerate else tr1)),
                [ca0, ca1, ncl]
            )

class SimilarTrianglesByAngleAndTwoSidesRule(Rule):
    def sources(self):
        return [(a0, a1) for a0, a1 in self.context.congruent_angles() if a0.vertex and a1.vertex and a0.point_set != a1.point_set]

    def apply(self, src):
        ang0, ang1 = src
        ca = None
        for vec0, vec1 in [(ang0.vector0, ang0.vector1), (ang0.vector1, ang0.vector0)]:
            if self.context.triangles_are_similar( \
                (vec0.start, vec0.end, vec1.end), \
                (ang1.vertex, ang1.vector0.end, ang1.vector1.end) \
            ):
                continue
            segments = (
                vec0.as_segment, vec1.as_segment,
                ang1.vector0.as_segment, ang1.vector1.as_segment
            )
            for inds in [(0, 1, 2, 3), (0, 2, 1, 3), (1, 0, 3, 2), (1, 3, 0, 2)]:
                elr = self.context.equal_length_ratios_property(*[segments[i] for i in inds])
                if elr:
                    break
            else:
                continue
            if ca is None:
                ca = self.context.angle_ratio_property(ang0, ang1)
            if ca.reason.obsolete and elr.reason.obsolete:
                continue
            yield (
                SimilarTrianglesProperty(
                    (ang0.vertex, vec0.end, vec1.end),
                    (ang1.vertex, ang1.vector0.end, ang1.vector1.end)
                ),
                'Two pairs of sides with the same ratio, and angle between the sides',
                [elr, ca]
            )

class CorrespondingAnglesInSimilarTriangles(SingleSourceRule):
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
