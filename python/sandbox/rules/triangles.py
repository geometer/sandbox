import itertools

from sandbox.property import *
from sandbox.util import LazyComment

from .abstract import Rule, SingleSourceRule

class SimilarTrianglesByTwoAnglesRule(Rule):
    def sources(self):
        groups = {}
        for a0, a1 in self.context.congruent_angles_with_vertex():
            if a0.point_set == a1.point_set:
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

class CongruentTrianglesByAngleAndTwoSidesRule(Rule):
    def sources(self):
        return self.context.congruent_angles_with_vertex()

    def apply(self, src):
        ang0, ang1 = src
        if ang0.point_set == ang1.point_set:
            return
        ca = None

        def congruent_segments(seg0, seg1):
            if seg0 == seg1:
                return True
            return self.context.congruent_segments_property(seg0, seg1, True)

        for vec0, vec1 in [(ang0.vector0, ang0.vector1), (ang0.vector1, ang0.vector0)]:
            rsn0 = congruent_segments(vec0.as_segment, ang1.vector0.as_segment)
            if rsn0 is None:
                continue
            rsn1 = congruent_segments(vec1.as_segment, ang1.vector1.as_segment)
            if rsn1 is None:
                continue
            if ca is None:
                ca = self.context.angle_ratio_property(ang0, ang1)
            if ca.reason.obsolete and (rsn0 == True or rsn0.reason.obsolete) and (rsn1 == True or rsn1.reason.obsolete):
                continue
            if rsn0 == True:
                comment = LazyComment('Common side %s, pair of congruent sides, and angle between the sides', vec0)
                premises = [rsn1, ca]
            elif rsn1 == True:
                comment = LazyComment('Common side %s, pair of congruent sides, and angle between the sides', vec1)
                premises = [rsn0, ca]
            else:
                comment = 'Two pairs of congruent sides, and angle between the sides'
                premises = [rsn0, rsn1, ca]
            yield (
                CongruentTrianglesProperty(
                    (ang0.vertex, vec0.points[1], vec1.points[1]),
                    (ang1.vertex, ang1.vector0.end, ang1.vector1.end)
                ), comment, premises
            )

class SimilarTrianglesByAngleAndTwoSidesRule(Rule):
    def sources(self):
        return [(a0, a1) for a0, a1 in self.context.congruent_angles_with_vertex() if a0.point_set != a1.point_set]

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

class SimilarTrianglesWithCongruentSideRule(SingleSourceRule):
    property_type = SimilarTrianglesProperty

    def apply(self, prop):
        sides0 = prop.triangle0.sides
        sides1 = prop.triangle1.sides
        for i in range(0, 3):
            cs = self.context.congruent_segments_property(sides0[i], sides1[i], True)
            if cs is None:
                continue
            if prop.reason.obsolete and cs.reason.obsolete:
                break
            yield (
                CongruentTrianglesProperty(prop.triangle0, prop.triangle1),
                'Similar triangles with congruent corresponding sides',
                [prop, cs]
            )
            break

class SimilarTrianglesByThreeSidesRule(Rule):
    def sources(self):
        return itertools.combinations(self.context.length_ratios(allow_zeroes=True), 2)

    def apply(self, src):
        triple0, triple1 = src
        num0, den0, value0 = triple0
        num1, den1, value1 = triple1
        if value0 == 1:
            return
        if value0 * value1 == 1:
            num1, den1, value1 = den1, num1, value0
        elif value0 != value1:
            return

        def common_point(segment0, segment1):
            if segment0.points[0] in segment1.points:
                if segment0.points[1] in segment1.points:
                    return None
                return segment0.points[0]
            if segment0.points[1] in segment1.points:
                return segment0.points[1]
            return None
        def other_point(segment, point):
            return segment.points[0] if point == segment.points[1] else segment.points[1]

        common0 = common_point(num0, num1)
        if common0 is None:
            return
        common1 = common_point(den0, den1)
        if common1 is None:
            return
        third0 = other_point(num0, common0).vector(other_point(num1, common0))
        third1 = other_point(den0, common1).vector(other_point(den1, common1))
        ncl = self.context.not_collinear_property(common0, *third0.points)
        if ncl is None:
            return
        ps2, value2 = self.context.length_ratio_property_and_value(third0.as_segment, third1.as_segment, True)
        if ps2 is None or value2 != value0:
            return
        ps0, _ = self.context.length_ratio_property_and_value(num0, den0, allow_zeroes=True)
        ps1, _ = self.context.length_ratio_property_and_value(num1, den1, allow_zeroes=True)
        if ncl is None or ps0.reason.obsolete and ps1.reason.obsolete and ps2.reason.obsolete and ncl.reason.obsolete:
            return
        yield (
            SimilarTrianglesProperty(
                (common0, *third0.points), (common1, *third1.points)
            ),
            'Three pairs of sides with the same ratio',
            [ps0, ps1, ps2, ncl]
        )
