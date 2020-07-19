import itertools

from .. import Scene
from ..property import *
from ..util import LazyComment, Comment, common_endpoint, other_point

from .abstract import Rule, accepts_auto, processed_cache, source_type, source_types

@processed_cache(set())
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
                key = frozenset((pair0, pair1))
                if key in self.processed:
                    continue
                common = next((angle for angle in pair0 if angle in pair1), None)
                if common:
                    continue
                yield (prop_for(pair0), prop_for(pair1), key)

    def apply(self, src):
        ca0, ca1, key = src

        ncl = self.context.collinearity_property(*ca0.angle0.point_set)
        if ncl is None:
            ncl = self.context.collinearity_property(*ca1.angle1.point_set)
        if ncl is None:
            return
        self.processed.add(key)
        if ncl.collinear:
            return

        #this code ensures that vertices are listed in corresponding orders
        if ca0.angle0.point_set == ca1.angle0.point_set:
            verts0 = [ca0.angle0.vertex, ca1.angle0.vertex]
            verts1 = [ca0.angle1.vertex, ca1.angle1.vertex]
        else:
            verts0 = [ca0.angle0.vertex, ca1.angle1.vertex]
            verts1 = [ca0.angle1.vertex, ca1.angle0.vertex]
        verts0.append(next(p for p in ca0.angle0.point_set if p not in verts0))
        verts1.append(next(p for p in ca0.angle1.point_set if p not in verts1))
        tr0 = Scene.Triangle(*verts0)
        tr1 = Scene.Triangle(*verts1)

        for i in range(0, 3):
            side0 = tr0.sides[i]
            side1 = tr1.sides[i]
            if side0 == side1:
                yield (
                    CongruentTrianglesProperty(tr0, tr1),
                    Comment(
                        'congruent angles $%{anglemeasure:angle0_0}=%{anglemeasure:angle1_0}$ and $%{anglemeasure:angle0_1}=%{anglemeasure:angle1_1}$, and common side $%{segment:side}$',
                        {
                            'angle0_0': tr0.angles[0],
                            'angle0_1': tr0.angles[1],
                            'angle1_0': tr1.angles[0],
                            'angle1_1': tr1.angles[1],
                            'side': side0
                        }
                    ),
                    [ca0, ca1, ncl]
                )
                return
        for i in range(0, 3):
            side0 = tr0.sides[i]
            side1 = tr1.sides[i]
            rat, val = self.context.length_ratio_property_and_value(side0, side1, True)
            if rat is None:
                continue
            if val == 1:
                yield (
                    CongruentTrianglesProperty(tr0, tr1),
                    Comment(
                        'congruent angles $%{anglemeasure:angle0_0}=%{anglemeasure:angle1_0}$ and $%{anglemeasure:angle0_1}=%{anglemeasure:angle1_1}$, and congruent sides $|%{segment:side0}|=|%{segment:side1}|$',
                        {
                            'angle0_0': tr0.angles[0],
                            'angle0_1': tr0.angles[1],
                            'angle1_0': tr1.angles[0],
                            'angle1_1': tr1.angles[1],
                            'side0': side0,
                            'side1': side1
                        }
                    ),
                    [ca0, ca1, rat, ncl]
                )
                return
            break

        yield (
            SimilarNondegenerateTrianglesProperty(tr0, tr1),
            Comment(
                'congruent angles $%{anglemeasure:angle0_0}=%{anglemeasure:angle1_0}$ and $%{anglemeasure:angle0_1}=%{anglemeasure:angle1_1}$',
                {
                    'angle0_0': tr0.angles[0],
                    'angle0_1': tr0.angles[1],
                    'angle1_0': tr1.angles[0],
                    'angle1_1': tr1.angles[1]
                }
            ),
            [ca0, ca1, ncl]
        )

@processed_cache({})
class CongruentTrianglesByAngleAndTwoSidesRule(Rule):
    def sources(self):
        return self.context.congruent_angles_with_vertex()

    def apply(self, src):
        mask = self.processed.get(src, 0)
        if mask == 0x3:
            return
        ang0, ang1 = src
        if ang0.point_set == ang1.point_set:
            return
        ca = None

        def congruent_segments(seg0, seg1):
            if seg0 == seg1:
                return True
            return self.context.length_ratio_property_and_value(seg0, seg1, True)

        original = mask
        for vec0, vec1, bit in [(*ang0.vectors, 1), (ang0.vectors[1], ang0.vectors[0], 2)]:
            if bit & mask:
                continue
            rsn0 = congruent_segments(vec0.as_segment, ang1.vectors[0].as_segment)
            if rsn0 is None:
                continue
            if isinstance(rsn0, tuple):
                if rsn0[1] != 1:
                    mask |= bit
                    continue
                rsn0 = rsn0[0]
            rsn1 = congruent_segments(vec1.as_segment, ang1.vectors[1].as_segment)
            if rsn1 is None:
                continue
            mask |= bit
            if isinstance(rsn1, tuple):
                if rsn1[1] != 1:
                    continue
                rsn1 = rsn1[0]
            if ca is None:
                ca = self.context.angle_ratio_property(ang0, ang1)

            pattern = 'common side $%{segment:common}$, $%{segment:side0} = %{segment:side1}$, and $%{anglemeasure:angle0} = %{anglemeasure:angle1}$'
            if rsn0 == True:
                comment = Comment(pattern, {
                    'common': vec0,
                    'side0': vec1,
                    'side1': ang1.vectors[1],
                    'angle0': ang0,
                    'angle1': ang1
                })
                premises = [rsn1, ca]
            elif rsn1 == True:
                comment = Comment(pattern, {
                    'common': vec1,
                    'side0': vec0,
                    'side1': ang1.vectors[0],
                    'angle0': ang0,
                    'angle1': ang1
                })
                premises = [rsn0, ca]
            else:
                comment = Comment(
                    'two pair of congruent sides $%{segment:side0} = %{segment:side1}$ and $%{segment:side2} = %{segment:side3}$, and congruent angles between the sides $%{anglemeasure:angle0} = %{anglemeasure:angle1}$',
                    {
                        'side0': vec0,
                        'side1': ang1.vectors[0],
                        'side2': vec1,
                        'side3': ang1.vectors[1],
                        'angle0': ang0,
                        'angle1': ang1
                    }
                )
                premises = [rsn0, rsn1, ca]
            yield (
                CongruentTrianglesProperty(
                    (ang0.vertex, vec0.points[1], vec1.points[1]),
                    (ang1.vertex, ang1.vectors[0].end, ang1.vectors[1].end)
                ), comment, premises
            )

        if original != mask:
            self.processed[src] = mask

@processed_cache(set())
class SimilarTrianglesByAngleAndTwoSidesRule(Rule):
    def sources(self):
        num_to_ratio = {}
        for seg0, seg1, ratio in self.context.length_ratios(allow_zeroes=True):
            common = common_endpoint(seg0, seg1)
            if common is None:
                continue
            triangle = Scene.Triangle(
                common, other_point(seg0.points, common), other_point(seg1.points, common)
            )
            lst = num_to_ratio.get(ratio)
            if lst:
                lst.append(triangle)
            else:
                num_to_ratio[ratio] = [triangle]
        for num, lst in num_to_ratio.items():
            if num == 1:
                for t0, t1 in itertools.combinations(lst, 2):
                    if set(t0.points) == set(t1.points):
                        continue
                    yield (t0, t1)
                    yield (t0, Scene.Triangle(t1.points[0], t1.points[2], t1.points[1]))
            else:
                for t0, t1 in itertools.combinations(lst, 2):
                    if set(t0.points) == set(t1.points):
                        continue
                    yield (t0, t1)

    def apply(self, src):
        t0, t1 = src

        if (t0.points, t1.points) in self.processed:
            return

        ar = self.context.angle_ratio_property(t0.angles[0], t1.angles[0])
        if ar is None:
            return
        self.processed.add((t0.points, t1.points))
        self.processed.add((t1.points, t0.points))

        if ar.value != 1:
            return
        rat0, value = self.context.length_ratio_property_and_value(t0.sides[1], t0.sides[2], allow_zeroes=True)
        rat1, value1 = self.context.length_ratio_property_and_value(t1.sides[1], t1.sides[2], allow_zeroes=True)
        yield (
            SimilarTrianglesProperty(t0, t1),
            LazyComment('%s, %s, and %s', rat0, rat1, ar),
            [rat0, rat1, ar]
        )

@processed_cache(set())
@accepts_auto
class SimilarTrianglesByAngleAndTwoSidesRule2(Rule):
    def sources(self):
        return [(a0, a1) for a0, a1 in self.context.congruent_angles_with_vertex() if a0.point_set != a1.point_set]

    def apply(self, src):
        ang0, ang1 = src
        ca = None
        for vec0, vec1 in [ang0.vectors, reversed(ang0.vectors)]:
            segments = (
                vec0.as_segment, vec1.as_segment,
                ang1.vectors[0].as_segment, ang1.vectors[1].as_segment
            )
            elrs = []
            for inds in [(0, 1, 2, 3), (0, 2, 1, 3), (1, 0, 3, 2), (2, 0, 3, 1)]:
                elrs.append(self.context.equal_length_ratios_property(*[segments[i] for i in inds]))
            elrs = list(filter(None, elrs))
            if not elrs:
                continue
            self.processed.add(src)
            if ca is None:
                ca = self.context.angle_ratio_property(ang0, ang1)
            for elr in elrs:
                yield (
                    SimilarTrianglesProperty(
                        (ang0.vertex, vec0.end, vec1.end),
                        (ang1.vertex, ang1.vectors[0].end, ang1.vectors[1].end)
                    ),
                    LazyComment('%s and %s', elr, ca),
                    [elr, ca]
                )

@source_types(SimilarNondegenerateTrianglesProperty, SimilarTrianglesProperty)
@processed_cache(set())
@accepts_auto
class SimilarTrianglesWithCongruentSideRule(Rule):
    def apply(self, prop):
        sides0 = prop.triangle0.sides
        sides1 = prop.triangle1.sides
        for i in range(0, 3):
            if sides0[i] != sides1[i]:
                continue
            ne = self.context.not_equal_property(*sides0[i].points)
            if ne is None:
                return
            self.processed.add(prop)
            yield (
                CongruentTrianglesProperty(prop.triangle0, prop.triangle1),
                Comment(
                    'similar triangles with common non-zero side $%{segment:side}$',
                    {'side': sides0[i]}
                ),
                [prop, ne]
            )
            return
        for i in range(0, 3):
            cs, value = self.context.length_ratio_property_and_value(sides0[i], sides1[i], True)
            if cs is None:
                continue
            if value != 1:
                self.processed.add(prop)
                return
            ne = self.context.not_equal_property(*sides0[i].points)
            if ne is None:
                ne = self.context.not_equal_property(*sides1[i].points)
            if ne is None:
                continue
            self.processed.add(prop)
            yield (
                CongruentTrianglesProperty(prop.triangle0, prop.triangle1),
                Comment(
                    'similar triangles with congruent sides $%{segment:side0}$ and $%{segment:side1}$',
                    {'side0': sides0[i], 'side1': sides1[i]}
                ),
                [prop, cs, ne]
            )
            return

@processed_cache(set())
class CongruentTrianglesByThreeSidesRule(Rule):
    def sources(self):
        congruent_segments = [p for p in self.context.length_ratio_properties(allow_zeroes=True) if p.value == 1]
        return itertools.combinations(congruent_segments, 2)

    def apply(self, src):
        key = frozenset(src)
        if key in self.processed:
            return
        self.processed.add(key)

        cs0, cs1 = src

        for seg0, seg1 in [(cs0.segment0, cs0.segment1), (cs0.segment1, cs0.segment0)]:
            points0 = set((*seg0.points, *cs1.segment0.points))
            if len(points0) != 3 or points0 == set((*seg1.points, *cs1.segment1.points)):
                continue
            common0 = common_endpoint(seg0, cs1.segment0)
            if seg1 == cs1.segment1:
                continue
            common1 = common_endpoint(seg1, cs1.segment1)
            if common1 is None:
                continue
            third0 = other_point(seg0.points, common0).vector(other_point(cs1.segment0.points, common0))
            third1 = other_point(seg1.points, common1).vector(other_point(cs1.segment1.points, common1))
            prop = CongruentTrianglesProperty(
                (common0, *third0.points), (common1, *third1.points)
            )
            if third0.as_segment == third1.as_segment:
                yield (
                    prop,
                    Comment(
                        'common side $%{segment:side0}$, $%{segment:side1_0} = %{segment:side1_1}$, $%{segment:side2_0} = %{segment:side2_1}$',
                        {'side0': third0, 'side1_0': seg0, 'side1_1': seg1, 'side2_0': cs1.segment0, 'side2_1': cs1.segment1}
                    ),
                    [cs0, cs1]
                )
            else:
                cs2 = self.context.congruent_segments_property(third0.as_segment, third1.as_segment, True)
                if cs2:
                    yield (
                        prop,
                        Comment(
                            'three pairs of congruent sides: $%{segment:side0_0} = %{segment:side0_1}$, $%{segment:side1_0} = %{segment:side1_1}$, $%{segment:side2_0} = %{segment:side2_1}$',
                            {
                                'side0_0': seg0,
                                'side0_1': seg1,
                                'side1_0': cs1.segment0,
                                'side1_1': cs1.segment1,
                                'side2_0': third0,
                                'side2_1': third1
                            }
                        ),
                        [cs0, cs1, cs2]
                    )

@processed_cache(set())
class SimilarTrianglesByThreeSidesRule(Rule):
    def sources(self):
        return itertools.combinations(self.context.length_ratios(allow_zeroes=True), 2)

    def apply(self, src):
        key = frozenset(src)
        if key in self.processed:
            return

        triple0, triple1 = src
        num0, den0, value0 = triple0
        num1, den1, value1 = triple1
        if value0 == 1:
            self.processed.add(key)
            return
        if value0 != value1:
            if value0 * value1 == 1:
                num1, den1, value1 = den1, num1, value0
            else:
                self.processed.add(key)
                return

        if num0 == num1 or den0 == den1:
            self.processed.add(key)
            return
        common0 = common_endpoint(num0, num1)
        if common0 is None:
            self.processed.add(key)
            return
        common1 = common_endpoint(den0, den1)
        if common1 is None:
            self.processed.add(key)
            return
        third0 = other_point(num0.points, common0).vector(other_point(num1.points, common0))
        third1 = other_point(den0.points, common1).vector(other_point(den1.points, common1))
        ncl = self.context.collinearity_property(common0, *third0.points)
        if ncl is None:
            return
        if ncl.collinear:
            self.processed.add(key)
            return
        ps2, value2 = self.context.length_ratio_property_and_value(third0.as_segment, third1.as_segment, True)
        if ps2 is None:
            return
        self.processed.add(key)
        if value2 != value0:
            return
        ps0, _ = self.context.length_ratio_property_and_value(num0, den0, allow_zeroes=True)
        ps1, _ = self.context.length_ratio_property_and_value(num1, den1, allow_zeroes=True)
        yield (
            SimilarTrianglesProperty(
                (common0, *third0.points), (common1, *third1.points)
            ),
            LazyComment('Three pairs of sides with the same ratio'),
            [ps0, ps1, ps2, ncl]
        )

@processed_cache(set())
@accepts_auto
class EquilateralTriangleByThreeSidesRule(Rule):
    def sources(self):
        return [p for p in self.context.length_ratio_properties(allow_zeroes=True) if p.value == 1]

    def apply(self, prop):
        self.processed.add(prop)
        common = next((p for p in prop.segment0.points if p in prop.segment1.points), None)
        if common is None:
            return
        pt0 = next(p for p in prop.segment0.points if p != common)
        pt1 = next(p for p in prop.segment1.points if p != common)
        cs2 = self.context.congruent_segments_property(common.segment(pt0), pt0.segment(pt1), True)
        if cs2:
            yield (
                EquilateralTriangleProperty((common, pt0, pt1)),
                Comment(
                    'congruent sides $%{segment:s0} = %{segment:s1}$ and $%{segment:s2} = %{segment:s3}$',
                    {'s0': prop.segment0, 's1': prop.segment1, 's2': cs2.segment0, 's3': cs2.segment1}
                ),
                [prop, cs2]
            )

@processed_cache(set())
class EquilateralTriangleByConrguentLegsAndAngleRule(Rule):
    def sources(self):
        return self.context.angle_value_properties_for_degree(
            60, lambda angle: angle.vertex and angle not in self.processed
        )

    def apply(self, prop):
        angle = prop.angle
        ratio, value = self.context.length_ratio_property_and_value(angle.vectors[0].as_segment, angle.vectors[1].as_segment, allow_zeroes=True)
        if ratio is None:
            return

        self.processed.add(angle)
        if value != 1:
            return
        yield (
            EquilateralTriangleProperty(angle.point_set),
            Comment(
                'congruent sides $%{segment:side0}$ and $%{segment:side1}$, and $%{anglemeasure:angle} = %{degree:degree}$',
                {'side0': ratio.segment0, 'side1': ratio.segment1, 'angle': angle, 'degree': prop.degree}
            ),
            [ratio, prop]
        )

@processed_cache(set())
class IsoscelesTriangleByConrguentLegsRule(Rule):
    def sources(self):
        return [p for p in self.context.length_ratio_properties(allow_zeroes=True) if p.value == 1 and p not in self.processed]

    def apply(self, prop):
        apex = next((pt for pt in prop.segment0.points if pt in prop.segment1.points), None)
        if apex is None:
            self.processed.add(prop)
            return
        base0 = next(pt for pt in prop.segment0.points if pt != apex)
        base1 = next(pt for pt in prop.segment1.points if pt != apex)

        self.processed.add(prop)
        yield (
            IsoscelesTriangleProperty(apex, base0.segment(base1)),
            Comment(
                'congruent legs $%{segment:side0}$ and $%{segment:side1}$',
                {'side0': prop.segment0, 'side1': prop.segment1}
            ),
            [prop]
        )

@processed_cache(set())
class IsoscelesTriangleByConrguentBaseAnglesRule(Rule):
    def sources(self):
        return self.context.congruent_angles_with_vertex()

    def apply(self, src):
        ang0, ang1 = src
        if ang0.point_set != ang1.point_set:
            return

        key = frozenset(src)
        if key in self.processed:
            return

        base = ang0.vertex.segment(ang1.vertex)
        apex = next(pt for pt in ang0.point_set if pt not in base.point_set)

        av0 = self.context.angle_value_property(ang0)
        if av0 and av0.degree != 0:
            self.processed.add(key)
            av1 = self.context.angle_value_property(ang1)
            if av0.degree == 60:
                yield (
                    EquilateralTriangleProperty(ang0.point_set),
                    Comment(
                        '$%{anglemeasure:angle0} = %{degree:deg0}$ and $%{anglemeasure:angle1} = %{degree:deg1}$',
                        {'angle0': ang0, 'angle1': ang1, 'deg0': av0.degree, 'deg1': av1.degree}
                    ),
                    [av0, av1]
                )
            else:
                yield (
                    IsoscelesTriangleProperty(apex, base),
                    Comment(
                        'congruent base angles $%{anglemeasure:angle0} = %{degree:degree}$ and $%{anglemeasure:angle1} = %{degree:degree}$',
                        {'angle0': ang0, 'angle1': ang1, 'degree': av0.degree}
                    ),
                    [av0, av1]
                )

        nc = self.context.collinearity_property(*ang0.point_set)
        if nc is None:
            return
        self.processed.add(key)

        if nc.collinear:
            return
        ca = self.context.angle_ratio_property(ang0, ang1)
        yield (
            IsoscelesTriangleProperty(apex, base),
            Comment(
                'congruent base angles $%{angle:angle0}$ and $%{angle:angle1}$',
                {'angle0': ang0, 'angle1': ang1}
            ),
    [ca, nc]
        )
