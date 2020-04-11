import itertools

from sandbox.property import *
from sandbox.scene import Triangle
from sandbox.util import LazyComment

from .abstract import Rule, SingleSourceRule

class SideProductsInSimilarTrianglesRule(SingleSourceRule):
    property_type = SimilarTrianglesProperty

    def apply(self, prop):
        for i, j in itertools.combinations(range(0, 3), 2):
            yield (
                EqualLengthProductsProperty(
                    prop.triangle0.side_for_index(i), prop.triangle0.side_for_index(j),
                    prop.triangle1.side_for_index(i), prop.triangle1.side_for_index(j)
                ),
                'Relation of sides in similar triangles',
                [prop]
            )

class SimilarTrianglesByTwoAnglesRule(Rule):
    def sources(self):
        groups = {}
        for prop in self.context.congruent_angle_properties():
            if not prop.angle0.vertex or not prop.angle1.vertex:
                continue
            key = frozenset([frozenset(prop.angle0.points), frozenset(prop.angle1.points)])
            lst = groups.get(key)
            if lst:
                lst.append(prop)
            else:
                groups[key] = [prop]

        for group in groups.values():
            for ca0, ca1 in itertools.combinations(group, 2):
                if ca1.angle0 in ca0.angle_set or ca1.angle1 in ca0.angle_set:
                    continue
                yield (ca0, ca1)

    def apply(self, src):
        ca0, ca1 = src

        ncl = self.context.not_collinear_property(*ca0.angle0.points)
        first_non_degenerate = True
        if ncl is None:
            ncl = self.context.not_collinear_property(*ca1.angle1.points)
            first_non_degenerate = False
        if ncl is None or ca0.reason.obsolete and ca1.reason.obsolete and ncl.reason.obsolete:
            return

        #this code ensures that vertices are listed in corresponding orders
        if ca0.angle0.points == ca1.angle0.points:
            tr0 = [ca0.angle0.vertex, ca1.angle0.vertex]
            tr1 = [ca0.angle1.vertex, ca1.angle1.vertex]
        else:
            tr0 = [ca0.angle0.vertex, ca1.angle1.vertex]
            tr1 = [ca0.angle1.vertex, ca1.angle0.vertex]
        tr0.append(next(p for p in ca0.angle0.points if p not in tr0))
        tr1.append(next(p for p in ca0.angle1.points if p not in tr1))

        yield (
            SimilarTrianglesProperty(tr0, tr1),
            LazyComment('Two pairs of congruent angles, and △ %s %s %s is non-degenerate', *(tr0 if first_non_degenerate else tr1)),
            [ca0, ca1, ncl]
        )

class SimilarTrianglesByAngleAndTwoSidesRule(Rule):
    def sources(self):
        return [ar for ar in self.context.congruent_angle_properties() if ar.angle0.vertex and ar.angle1.vertex]

    def apply(self, ca):
        ang0 = ca.angle0
        ang1 = ca.angle1
        for vec0, vec1 in [(ang0.vector0, ang0.vector1), (ang0.vector1, ang0.vector0)]:
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
        for i in range(0, 3):
            ne0.append(self.context.not_equal_property(*prop.triangle0.side_for_index(i).points))
            ne1.append(self.context.not_equal_property(*prop.triangle1.side_for_index(i).points))

        for i in range(0, 3):
            angle0 = prop.triangle0.angle_for_index(i)
            angle1 = prop.triangle1.angle_for_index(i)
            if angle0 == angle1:
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
                AnglesRatioProperty(angle0, angle1, 1),
                'Corresponding non-degenerate angles in similar triangles',
                [prop] + ne
            )
