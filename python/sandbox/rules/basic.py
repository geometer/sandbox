import itertools

from ..property import *
from ..scene import Scene
from ..util import LazyComment, Comment, divide, common_endpoint, other_point

from .abstract import Rule, accepts_auto, processed_cache, source_type

@processed_cache(set())
class TwoAnglesWithCommonAndCollinearSidesRule(Rule):
    def sources(self):
        kinds = [a for a in self.context.list(AngleKindProperty) if a.angle.vertex and a.kind != AngleKindProperty.Kind.right]
        for k0, k1 in itertools.combinations(kinds, 2):
            if k0.angle.vertex != k1.angle.vertex:
                continue
            if k0.angle.vectors[0] in k1.angle.vectors or k0.angle.vectors[1] in k1.angle.vectors:
                yield (k0, k1)

    def apply(self, pair):
        key = frozenset(pair)
        if key in self.processed:
            return

        k0, k1 = pair
        common = next(pt for pt in k0.angle.endpoints if pt in k1.angle.endpoints)
        other0 = other_point(k0.angle.endpoints, common)
        other1 = other_point(k1.angle.endpoints, common)
        collinearity = self.context.collinearity(k0.angle.vertex, other0, other1)
        if collinearity is None:
            return

        self.processed.add(key)
        if not collinearity:
            return
        collinearity_prop = self.context.collinearity_property(k0.angle.vertex, other0, other1)

        if k0.kind == k1.kind:
            value = 0
            if k0.kind == AngleKindProperty.Kind.acute:
                pattern = '$%{point:vertex}$, $%{point:other0}$, and $%{point:other1}$ are collinear, and both $%{angle:angle0}$ and $%{angle:angle1}$ are acute'
            else:
                pattern = '$%{point:vertex}$, $%{point:other0}$, and $%{point:other1}$ are collinear, and both $%{angle:angle0}$ and $%{angle:angle1}$ are obtuse'
        else:
            value = 180
            pattern = '$%{point:vertex}$, $%{point:other0}$, and $%{point:other1}$ are collinear, $%{anglemeasure:angle0} \\neq %{anglemeasure:angle1}$'

        yield (
            AngleValueProperty(k0.angle.vertex.angle(other0, other1), value),
            Comment(
                pattern,
                {'angle0': k0.angle, 'angle1': k1.angle, 'vertex': k0.angle.vertex, 'other0': other0, 'other1': other1}
            ),
            [collinearity_prop, k0, k1]
        )

@processed_cache(set())
class TwoFootsOfSamePerpendicularRule(Rule):
    def sources(self):
        return self.context.angle_value_properties_for_degree(90, lambda a: a.vertex)

    def apply(self, prop):
        for vec0, vec1 in [prop.angle.vectors, reversed(prop.angle.vectors)]:
            key = (prop.angle, vec1.end)
            if key in self.processed:
                continue
            foot = self.context.foot_of_perpendicular(vec1.end, vec0.as_segment)
            if foot is None:
                continue
            self.processed.add(key)
            if foot in vec0.points:
                continue
            foot_prop = self.context.foot_of_perpendicular_property(foot, vec1.end, vec0.as_segment)
            yield (
                PointsCoincidenceProperty(prop.angle.vertex, foot, True),
                Comment(
                    '$%{point:foot}$ is the foot of the perpendicular from $%{point:pt}$ to $%{line:line}$, and $%{angle:angle}$ is right',
                    {'foot': foot, 'pt': vec1.end, 'line': vec0, 'angle': prop.angle}
                ),
                [foot_prop, prop]
            )

@processed_cache(set())
class FourPointsOnLineRule(Rule):
    def sources(self):
        props = self.context.angle_value_properties_for_degree(180, lambda a: a.vertex)
        for p0, p1 in itertools.combinations(props, 2):
            if p0.angle.vertex in p1.angle.endpoints and p1.angle.vertex in p0.angle.endpoints:
                yield (p0, p1)

    def apply(self, src):
        if src in self.processed:
            return

        prop0, prop1 = src
        self.processed.add(src)
        self.processed.add((prop1, prop0))

        end0 = other_point(prop0.angle.endpoints, prop1.angle.vertex)
        end1 = other_point(prop1.angle.endpoints, prop0.angle.vertex)

        comment = Comment(
            'four points $%{point:e0}$, $%{point:v0}$, $%{point:v1}$, and $%{point:e1}$ lie on a straight line in this order',
            {'e0': end0, 'e1': end1, 'v0': prop0.angle.vertex, 'v1': prop1.angle.vertex}
        )

        for p in (
            AngleValueProperty(prop0.angle.vertex.angle(end0, end1), 180),
            AngleValueProperty(prop1.angle.vertex.angle(end0, end1), 180),
            AngleValueProperty(end0.angle(prop0.angle.vertex, end1), 0),
            AngleValueProperty(end0.angle(prop1.angle.vertex, end1), 0),
            AngleValueProperty(end1.angle(prop0.angle.vertex, end0), 0),
            AngleValueProperty(end1.angle(prop1.angle.vertex, end0), 0)
        ):
            yield (p, comment, [prop0, prop1])

@processed_cache(set())
class FourPointsOnLineRule2(Rule):
    def sources(self):
        props = self.context.angle_value_properties_for_degree(180, lambda a: a.vertex)
        for p0, p1 in itertools.combinations(props, 2):
            ep0 = p0.angle.endpoints
            ep1 = p1.angle.endpoints
            if p0.angle.vertex in ep1 and (ep0[0] in ep1 or ep0[1] in ep1):
                yield (p1, p0)
            elif p1.angle.vertex in ep0 and (ep1[0] in ep0 or ep1[1] in ep0):
                yield (p0, p1)

    def apply(self, src):
        if src in self.processed:
            return
        self.processed.add(src)

        prop0, prop1 = src

        end0 = other_point(prop0.angle.endpoints, prop1.angle.vertex)
        end1 = other_point(prop1.angle.endpoints, end0)

        comment = Comment(
            'four points $%{point:e0}$, $%{point:v0}$, $%{point:v1}$, and $%{point:e1}$ lie on a straight line in this order',
            {'e0': end0, 'e1': end1, 'v0': prop0.angle.vertex, 'v1': prop1.angle.vertex}
        )

        for p in (
            AngleValueProperty(prop0.angle.vertex.angle(end0, end1), 180),
            AngleValueProperty(prop1.angle.vertex.angle(prop0.angle.vertex, end1), 180),
            AngleValueProperty(end0.angle(prop0.angle.vertex, end1), 0),
            AngleValueProperty(prop0.angle.vertex.angle(prop1.angle.vertex, end1), 0),
            AngleValueProperty(end1.angle(prop0.angle.vertex, end0), 0),
            AngleValueProperty(end1.angle(prop0.angle.vertex, prop1.angle.vertex), 0)
        ):
            yield (p, comment, [prop0, prop1])

@source_type(AngleKindProperty)
@processed_cache(set())
class PerpendicularInAcuteAngleRule(Rule):
    def accepts(self, prop):
        return prop.angle.vertex and prop.kind == AngleKindProperty.Kind.acute

    def apply(self, prop):
        for v0, v1 in (prop.angle.vectors, reversed(prop.angle.vectors)):
            for pt in self.context.collinear_points(v0.as_segment):
                key = (prop, pt)
                if key in self.processed:
                    continue

                foot = self.context.foot_of_perpendicular(pt, v1.as_segment)
                if foot is None or foot == v1.start:
                    continue
                if foot == v1.end:
                    premises = [self.context.foot_of_perpendicular_property(foot, pt, v1.as_segment)]
                    degree = 0
                else:
                    av = self.context.angle_value_property(v1.start.angle(foot, v1.end))
                    if av is None:
                        continue
                    premises = [self.context.foot_of_perpendicular_property(foot, pt, v1.as_segment), av]
                    degree = av.degree

                self.processed.add(key)

                co = self.context.collinearity_property(pt, *v0.points)
                if degree == 0:
                    pattern = '$%{angle:angle}$ is acute, foot of the perpendicular from $%{point:pt}$ to line $%{line:side}$ lies on ray $%{ray:side}$'
                else:
                    pattern = '$%{angle:angle}$ is acute, foot of the perpendicular from $%{point:pt}$ to line $%{line:side}$ lies outside of ray $%{ray:side}$'
                yield (
                    AngleValueProperty(v0.start.angle(pt, v0.end), degree),
                    Comment(pattern, {'angle': prop.angle, 'pt': pt, 'side': v1}),
                    [prop, co] + premises
                )

@source_type(AngleKindProperty)
@processed_cache(set())
class PerpendicularInAcuteAngleRule2(Rule):
    def accepts(self, prop):
        return prop.angle.vertex and prop.kind == AngleKindProperty.Kind.acute

    def apply(self, prop):
        for v0, v1 in (prop.angle.vectors, reversed(prop.angle.vectors)):
            for pt in [v0.end, *self.context.collinear_points(v0.as_segment)]:
                key = (prop, pt)
                if key in self.processed:
                    continue

                foot = self.context.foot_of_perpendicular(pt, v1.as_segment)
                if foot is None:
                    continue
                if foot == v1.end:
                    self.processed.add(key)
                    continue

                if pt == v0.end:
                    premises = [self.context.foot_of_perpendicular_property(foot, pt, v1.as_segment)]
                    degree = 0
                else:
                    av = self.context.angle_value_property(v0.start.angle(pt, v0.end))
                    if av is None:
                        continue
                    premises = [self.context.foot_of_perpendicular_property(foot, pt, v1.as_segment), av]
                    degree = av.degree

                self.processed.add(key)

                if degree == 0:
                    pattern = '$%{angle:angle}$ is acute, $%{point:pt}$ lies on $%{ray:side0}$, $%{point:foot}$ is the foot of the perpendicular from $%{point:pt}$ to $%{line:side1}$'
                else:
                    pattern = '$%{angle:angle}$ is acute, $%{point:pt}$ lies on line $%{line:side0}$ outside of ray $%{ray:side0}$, $%{point:foot}$ is the foot of the perpendicular from $%{point:pt}$ to $%{line:side1}$'
                yield (
                    AngleValueProperty(v1.start.angle(foot, v1.end), degree),
                    Comment(pattern, {'angle': prop.angle, 'pt': pt, 'foot': foot, 'side0': v0, 'side1': v1}),
                    [prop] + premises
                )

@source_type(PointInsideAngleProperty)
@processed_cache(set())
@accepts_auto
class PointInsideAngleAndSecantRule(Rule):
    def apply(self, prop):
        col = self.context.collinearity_property(prop.point, *prop.angle.endpoints)
        if col is None:
            return
        self.processed.add(prop)

        if not col.collinear:
            return
        yield (
            AngleValueProperty(prop.point.angle(*prop.angle.endpoints), 180),
            Comment(
                '$%{point:pt0}$ and $%{point:pt1}$ are on different sides of $%{angle:angle}$, $%{point:inside}$ lies inside',
                {'pt0': prop.angle.endpoints[0], 'pt1': prop.angle.endpoints[1], 'angle': prop.angle, 'inside': prop.point}
            ),
            [prop, col]
        )

@source_type(PointInsideAngleProperty)
@processed_cache(set())
class PointInsideAngleAndPointOnSideRule(Rule):
    def apply(self, prop):
        for vec in prop.angle.vectors:
            for pt in self.context.collinear_points(vec.as_segment):
                key = (prop, pt)
                if key in self.processed:
                    continue
                self.processed.add(key)
                yield (
                    PointsCoincidenceProperty(prop.point, pt, False),
                    Comment(
                        '$%{point:inside}$ lies inside $%{angle:angle}$, $%{point:pt}$ is on $%{line:side}$',
                        {'inside': prop.point, 'angle': prop.angle, 'pt': pt, 'side': vec}
                    ),
                    [prop, self.context.collinearity_property(*vec.points, pt)]
                )

@source_type(AngleKindProperty)
@processed_cache(set())
class AngleTypeAndPerpendicularRule(Rule):
    def accepts(self, prop):
        return prop.angle.vertex and prop.kind != AngleKindProperty.Kind.right

    def apply(self, prop):
        angle = prop.angle
        if prop.kind == AngleKindProperty.Kind.acute:
            pattern = '$%{point:foot}$ is the foot of perpendicular from point $%{point:pt}$ on side of acute $%{angle:angle}$ to the second side'
        else:
            pattern = '$%{point:foot}$ is the foot of perpendicular from point $%{point:pt}$ on side of obtuse $%{angle:angle}$ to extension of the second side'
        for vec0, vec1 in (angle.vectors, reversed(angle.vectors)):
            key = (prop, vec0.end)
            if key in self.processed:
                continue
            foot = self.context.foot_of_perpendicular(vec0.end, vec1.as_segment)
            if foot is None:
                continue
            self.processed.add(key)
            foot_prop = self.context.foot_of_perpendicular_property(foot, vec0.end, vec1.as_segment)
            comment = Comment(pattern, {'foot': foot, 'pt': vec0.end, 'angle': angle})
            new_props = [
                PointsCollinearityProperty(vec0.end, foot, angle.vertex, False),
                PointsCoincidenceProperty(foot, angle.vertex, False),
            ]
            if foot != vec1.end:
                if prop.kind == AngleKindProperty.Kind.acute:
                    new_props.append(AngleValueProperty(angle.vertex.angle(foot, vec1.end), 0))
                else:
                    new_props.append(AngleValueProperty(angle.vertex.angle(foot, vec1.end), 180))
            for p in new_props:
                yield (p, comment, [prop, foot_prop])

@source_type(PointInsideAngleProperty)
@processed_cache(set())
@accepts_auto
class PointInsideAngleConfigurationRule(Rule):
    def apply(self, prop):
        self.processed.add(prop)

        for endpoint in prop.angle.endpoints:
            yield (
                PointsCollinearityProperty(prop.point, prop.angle.vertex, endpoint, False),
                Comment(
                    '$%{point:vertex}$ is the vertex of $%{angle:angle}$, $%{point:on_side}$ lies on a side, and $%{point:inside}$ lies inside',
                    {'vertex': prop.angle.vertex, 'angle': prop.angle, 'on_side': endpoint, 'inside': prop.point}
                ),
                [prop]
            )

        yield (
            SameOrOppositeSideProperty(prop.angle.vertex.segment(prop.point), *prop.angle.endpoints, False),
            Comment(
                'ray $%{ray:ray}$ inside $%{angle:angle}$ separates points $%{point:pt0}$ and $%{point:pt1}$',
                {'ray': prop.angle.vertex.vector(prop.point), 'angle': prop.angle, 'pt0': prop.angle.endpoints[0], 'pt1': prop.angle.endpoints[1]}
            ),
            [prop]
        )
        pattern = '$%{ray:side}$ is a side of $%{angle:angle}$, $%{point:other}$ lies on the other side, and $%{point:inside}$ lies inside the angle'
        yield (
            SameOrOppositeSideProperty(prop.angle.vectors[0].as_segment, prop.point, prop.angle.vectors[1].end, True),
            Comment(
                pattern,
                {'side': prop.angle.vectors[0], 'angle': prop.angle, 'other': prop.angle.vectors[1].end, 'inside': prop.point}
            ),
            [prop]
        )
        yield (
            SameOrOppositeSideProperty(prop.angle.vectors[1].as_segment, prop.point, prop.angle.vectors[0].end, True),
            Comment(
                pattern,
                {'side': prop.angle.vectors[1], 'angle': prop.angle, 'other': prop.angle.vectors[0].end, 'inside': prop.point}
            ),
            [prop]
        )

@source_type(PointInsideAngleProperty)
@processed_cache(set())
@accepts_auto
class SegmentWithEndpointsOnAngleSidesRule(Rule):
    def apply(self, prop):
        A = prop.angle.vertex
        B = prop.angle.vectors[0].end
        C = prop.angle.vectors[1].end
        D = prop.point
        AD = A.segment(D)
        BC = B.segment(C)
        X = self.context.intersection(AD, BC)
        if X is None:
            return
        self.processed.add(prop)
        if X in (A, B, C, D):
            return

        X_prop = self.context.intersection_property(X, AD, BC)
        comment = Comment(
            '$%{point:X}$ is the intersection of ray $%{ray:ray}$ and segment $%{segment:segment}$',
            {'X': X, 'ray': A.vector(D), 'segment': B.segment(C)}
        )
        yield (AngleValueProperty(A.angle(D, X), 0), comment, [X_prop, prop])
        yield (AngleValueProperty(B.angle(C, X), 0), comment, [X_prop, prop])
        yield (AngleValueProperty(C.angle(B, X), 0), comment, [X_prop, prop])
        yield (AngleValueProperty(X.angle(B, C), 180), comment, [X_prop, prop])

@source_type(SameOrOppositeSideProperty)
@processed_cache(set())
@accepts_auto
class LineAndTwoPointsToNoncollinearityRule(Rule):
    def apply(self, prop):
        self.processed.add(prop)
        for pt in prop.points:
            yield (
                PointsCollinearityProperty(pt, *prop.segment.points, False),
                Comment(
                    '$%{point:pt}$ does not lie on $%{line:line}$',
                    {'pt': pt, 'line': prop.segment}
                ),
                [prop]
            )

@source_type(SameOrOppositeSideProperty)
@processed_cache(set())
class KnownSumOfAnglesWithCommonSideRule(Rule):
    def accepts(self, prop):
        return not prop.same

    def apply(self, prop):
        for pt0, pt1 in (prop.segment.points, reversed(prop.segment.points)):
            key = (prop, pt0)
            if key in self.processed:
                continue
            summand0 = pt0.angle(prop.points[0], pt1)
            summand1 = pt0.angle(pt1, prop.points[1])
            sum_prop = self.context.sum_of_angles_property(summand0, summand1)
            if sum_prop is None:
                continue
            big_angle = pt0.angle(*prop.points)
            self.processed.add(key)
            if sum_prop.degree <= 180:
                degree = sum_prop.degree
                pattern = '$%{angle:big}$ consists of $%{angle:summand0}$ and $%{angle:summand1}$'
            else:
                degree = 360 - sum_prop.degree
                pattern = 'complement of $%{angle:big}$ consists of $%{angle:summand0}$ and $%{angle:summand1}$'
            yield (
                AngleValueProperty(big_angle, degree),
                Comment(pattern, {'big': big_angle, 'summand0': summand0, 'summand1': summand1}),
                [sum_prop, prop]
            )

@source_type(ProportionalLengthsProperty)
@processed_cache({})
class ProportionalLengthsToLengthsRatioRule(Rule):
    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0x3:
            return

        original = mask
        for segment, bit in ((prop.segment0, 1), (prop.segment1, 2)):
            if mask & bit:
                continue
            ne = self.context.coincidence_property(*segment.points)
            if ne is None:
                continue
            mask |= bit
            if ne.coincident:
                continue
            yield (
                LengthRatioProperty(prop.segment0, prop.segment1, prop.value),
                prop.reason.comment,
                [prop, ne]
            )

        if mask != original:
            self.processed[prop] = mask

@processed_cache(set())
class LengthRatiosWithCommonDenominatorRule(Rule):
    def sources(self):
        return self.context.equal_length_ratios_with_common_denominator()

    def apply(self, src):
        key = frozenset(src)
        if key in self.processed:
            return
        self.processed.add(key)

        ratio0, ratio1 = src
        ratio_prop = self.context.equal_length_ratios_property(*ratio0, *ratio1)
        yield (
            ProportionalLengthsProperty(ratio0[0], ratio1[0], 1),
            Comment(
                '$|%{segment:num0}| / |%{segment:denom}| = |%{segment:num1}| / |%{segment:denom}|$',
                {'num0': ratio0[0], 'num1': ratio1[0], 'denom': ratio0[1]}
            ),
            [ratio_prop]
        )

@processed_cache(set())
class LengthRatioTransitivityRule(Rule):
    """
    For three segments seg0, seg1, and seg2, from
        |seg0| = A |seg1|, and
        |seg1| = B |seg2|
    we conclude that |seg0| = A B |seg2|
    """
    def sources(self):
        return itertools.combinations(self.context.length_ratio_properties(allow_zeroes=True), 2)

    def apply(self, src):
        key = frozenset(src)
        if key in self.processed:
            return
        self.processed.add(key)

        lr0, lr1 = src

        def comment(seg0, seg1, seg2, coef1, coef2):
            if coef1 == 1:
                if coef2 == 1:
                    pattern = '$|%{segment:seg0}| = |%{segment:seg1}| = |%{segment:seg2}|$'
                else:
                    pattern = '$|%{segment:seg0}| = |%{segment:seg1}| = %{multiplier:coef2}|%{segment:seg2}|$'
            else:
                if coef2 == 1:
                    pattern = '$|%{segment:seg0}| = %{multiplier:coef1}|%{segment:seg1}| = |%{segment:seg2}|$'
                else:
                    pattern = '$|%{segment:seg0}| = %{multiplier:coef1}|%{segment:seg1}| = %{multiplier:coef2}|%{segment:seg2}|$'
            return Comment(pattern, {'seg0': seg0, 'seg1': seg1, 'seg2': seg2, 'coef1': coef1, 'coef2': coef2})

        if lr0.segment0 == lr1.segment0:
            coef = divide(lr1.value, lr0.value)
            yield (
                ProportionalLengthsProperty(lr0.segment1, lr1.segment1, coef),
                comment(lr0.segment1, lr0.segment0, lr1.segment1, divide(1, lr0.value), coef),
                [lr0, lr1]
            )
        elif lr0.segment0 == lr1.segment1:
            coef = lr1.value * lr0.value
            yield (
                ProportionalLengthsProperty(lr1.segment0, lr0.segment1, coef),
                comment(lr1.segment0, lr0.segment0, lr0.segment1, lr1.value, coef),
                [lr1, lr0]
            )
        elif lr0.segment1 == lr1.segment0:
            coef = lr1.value * lr0.value
            yield (
                ProportionalLengthsProperty(lr0.segment0, lr1.segment1, coef),
                comment(lr0.segment0, lr0.segment1, lr1.segment1, lr0.value, coef),
                [lr0, lr1]
            )
        elif lr0.segment1 == lr1.segment1:
            coef = divide(lr0.value, lr1.value)
            yield (
                ProportionalLengthsProperty(lr0.segment0, lr1.segment0, coef),
                comment(lr0.segment0, lr0.segment1, lr1.segment0, lr0.value, coef),
                [lr0, lr1]
            )

@processed_cache(set())
class CoincidenceTransitivityRule(Rule):
    def sources(self):
        #TODO: use self.context.non_coincident_points()
        return itertools.combinations(self.context.list(PointsCoincidenceProperty), 2)

    def apply(self, src):
        key = frozenset(src)
        if key in self.processed:
            return
        self.processed.add(key)

        co0, co1 = src
        if not co0.coincident and not co1.coincident:
            return
        common = next((pt for pt in co0.points if pt in co1.points), None)
        if common is None:
            return
        pt0 = next(pt for pt in co0.points if pt != common)
        pt1 = next(pt for pt in co1.points if pt != common)

        def eqsign(coincidence_prop):
            return '=' if coincidence_prop.coincident else '\\neq'
        pattern = '$%{point:pt0} ' + eqsign(co0) + ' %{point:common} ' + eqsign(co1) + ' %{point:pt1}$'
        yield (
            PointsCoincidenceProperty(pt0, pt1, co0.coincident and co1.coincident),
            Comment(pattern, {'pt0': pt0, 'pt1': pt1, 'common': common}),
            [co0, co1]
        )

@processed_cache({})
class AngleInTriangleWithTwoKnownAnglesRule(Rule):
    def sources(self):
        return [p for p in self.context.angle_value_properties() if p.angle.vertex and p.degree not in (0, 180)];

    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0x3:
            return

        angle0 = prop.angle
        triangle = Scene.Triangle(angle0.vertex, *angle0.endpoints)
        others = triangle.angles[1:]
        original = mask
        for (angle1, angle2), bit in ((others, 1), (reversed(others), 2)):
            if mask & bit:
                continue
            av = self.context.angle_value_property(angle1)
            if av is None:
                continue
            mask |= bit
            yield (
                AngleValueProperty(angle2, 180 - prop.degree - av.degree),
                Comment(
                    'third angle in $%{triangle:triangle}$ with $%{anglemeasure:angle0} = %{degree:degree0}$ and $%{anglemeasure:angle1} = %{degree:degree1}$',
                    {
                        'triangle': triangle,
                        'angle0': angle0,
                        'angle1': angle1,
                        'degree0': prop.degree,
                        'degree1': av.degree
                    }
                ),
                [prop, av]
            )
        if mask != original:
            self.processed[prop] = mask

@processed_cache(set())
class SumOfTwoAnglesInTriangleRule(Rule):
    def sources(self):
        return [p for p in self.context.angle_value_properties() if p.angle.vertex and p.degree not in (0, 180)];

    def apply(self, prop):
        if prop in self.processed:
            return
        self.processed.add(prop)

        angle0 = prop.angle
        triangle = Scene.Triangle(angle0.vertex, *angle0.endpoints)
        angle1 = triangle.angles[1]
        angle2 = triangle.angles[2]

        if prop.degree == 90:
            pattern = 'sum of acute angles of right-angled $%{triangle:triangle}$'
        else:
            pattern = 'sum of two angles of $%{triangle:triangle}$, the third $%{anglemeasure:angle} = %{degree:degree}$'
        yield (
            SumOfAnglesProperty(angle1, angle2, degree=180 - prop.degree),
            Comment(pattern, {'triangle': triangle, 'angle': angle0, 'degree': prop.degree}),
            [prop]
        )

@processed_cache(set())
class SumOfThreeAnglesInTriangleRule(Rule):
    def sources(self):
        for pt in self.context.points:
            for pair in itertools.combinations(self.context.non_coincident_points(pt), 2):
                yield (pt, *pair)

    def apply(self, src):
        key = frozenset(src)
        if key in self.processed:
            return

        pt0, pt1, pt2 = src
        ne2 = self.context.coincidence_property(pt1, pt2)
        if ne2 is None:
            return
        self.processed.add(key)
        if ne2.coincident:
            return
        ne0 = self.context.coincidence_property(pt0, pt1)
        ne1 = self.context.coincidence_property(pt0, pt2)
        triangle = Scene.Triangle(pt0, pt1, pt2)
        yield (
            SumOfAnglesProperty(*triangle.angles, degree=180),
            Comment('three angles of $%{triangle:triangle}$', {'triangle': triangle}),
            [ne0, ne1, ne2]
        )

@processed_cache(set())
class SumOfThreeAnglesOnLineRule(Rule):
    def sources(self):
        avs = self.context.angle_value_properties_for_degree(0, lambda angle: angle.vertex)
        for av0, av1 in itertools.combinations(avs, 2):
            if av0.angle.point_set == av1.angle.point_set:
                yield (av0, av1)

    def apply(self, src):
        key = frozenset(src)
        if key in self.processed:
            return
        self.processed.add(key)

        av0, av1 = src
        third = next(pt for pt in av0.angle.point_set if pt not in (av0.angle.vertex, av1.angle.vertex))
        angle = third.angle(av0.angle.vertex, av1.angle.vertex)
        yield (
            AngleValueProperty(angle, 180),
            Comment(
                '$%{point:pt0}$ and $%{point:pt1}$ are on the same side of $%{point:pt2}$, $%{point:pt2}$ and $%{point:pt1}$ are on the same side of $%{point:pt0}$',
                {'pt1': third, 'pt0': av0.angle.vertex, 'pt2': av1.angle.vertex}
            ),
            [av0, av1]
        )

@processed_cache(set())
class SumOfThreeAnglesOnLineRule2(Rule):
    def sources(self):
        return self.context.angle_value_properties_for_degree(
            180, lambda angle: angle.vertex and angle not in self.processed
        )

    def apply(self, prop):
        self.processed.add(prop.angle)

        for vec0, vec1 in (prop.angle.vectors, reversed(prop.angle.vectors)):
            yield (
                AngleValueProperty(vec0.end.angle(vec0.start, vec1.end), 0),
                Comment(
                    '$%{point:pt0}$ lies between $%{point:pt1}$ and $%{point:pt2}$',
                    {'pt0': vec0.start, 'pt1': vec0.end, 'pt2': vec1.end}
                ),
                [prop]
            )

@source_type(ProportionalLengthsProperty)
@processed_cache(set())
class LengthRatioRule(Rule):
    def apply(self, prop):
        for seg0, seg1 in [(prop.segment0, prop.segment1), (prop.segment1, prop.segment0)]:
            key = (seg0, seg1)
            if key in self.processed:
                continue
            coinc = self.context.coincidence_property(*seg0.points)
            if coinc is None:
                continue
            self.processed.add(key)

            if coinc.coincident:
                pattern = 'otherwise, $%{point:pt0} = %{point:pt1}$'
            else:
                pattern = '$%{point:pt0} = %{point:pt1}$'
            yield (
                PointsCoincidenceProperty(*seg1.points, coinc.coincident),
                Comment(pattern, {'pt0': seg0.points[0], 'pt1': seg0.points[1]}),
                [prop, coinc]
            )

@source_type(ProportionalLengthsProperty)
@processed_cache(set())
@accepts_auto
class IsoscelesNonzeroBaseImpliesNonzeroLegsRule(Rule):
    def apply(self, prop):
        seg0 = prop.segment0
        seg1 = prop.segment1
        common = common_endpoint(seg0, seg1)
        if common is None:
            self.processed.add(prop)
            return

        pt0 = other_point(seg0.points, common)
        pt1 = other_point(seg1.points, common)
        coinc = self.context.coincidence_property(pt0, pt1)
        if coinc is None:
            return
        self.processed.add(prop)
        if coinc.coincident:
            return

        pattern = 'otherwise, $%{point:pt0} = %{point:pt1} = %{point:pt2}$'
        yield (
            PointsCoincidenceProperty(*seg0.points, False),
            Comment(pattern, {'pt0': coinc.points[0], 'pt1': common, 'pt2': coinc.points[1]}),
            [prop, coinc]
        )
        yield (
            PointsCoincidenceProperty(*seg1.points, False),
            Comment(pattern, {'pt0': coinc.points[1], 'pt1': common, 'pt2': coinc.points[0]}),
            [prop, coinc]
        )

@source_type(ParallelVectorsProperty)
@processed_cache(set())
@accepts_auto
class ParallelVectorsRule(Rule):
    def apply(self, para):
        vec0 = para.vectors[0]
        vec1 = para.vectors[1]
        ne0 = self.context.coincidence_property(*vec0.points)
        if ne0 is None:
            return
        if ne0.coincident:
            self.processed.add(para)
            return
        ne1 = self.context.coincidence_property(*vec1.points)
        if ne1 is None:
            return
        self.processed.add(para)
        if ne1.coincident:
            return
        for prop in AngleValueProperty.generate(vec0, vec1, 0):
            yield (
                prop,
                Comment(
                    'non-zero parallel vectors $%{vector:vec0}$ and $%{vector:vec1}$',
                    {'vec0': vec0, 'vec1': vec1}
                ),
                [para, ne0, ne1]
            )

@source_type(PerpendicularSegmentsProperty)
@processed_cache(set())
@accepts_auto
class PerpendicularSegmentsRule(Rule):
    def apply(self, pv):
        seg0 = pv.segments[0]
        seg1 = pv.segments[1]
        ne0 = self.context.coincidence_property(*seg0.points)
        ne1 = self.context.coincidence_property(*seg1.points)
        if ne0 is None or ne1 is None:
            return
        self.processed.add(pv)
        if ne0.coincident or ne1.coincident:
            return
        vec0 = seg0.points[0].vector(seg0.points[1])
        vec1 = seg1.points[0].vector(seg1.points[1])
        for prop in AngleValueProperty.generate(vec0, vec1, 90):
            yield (
                prop,
                Comment(
                    'non-zero perpendicular segments $%{segment:seg0}$ and $%{segment:seg1}$',
                    {'seg0': seg0, 'seg1': seg1}
                ),
                [pv, ne0, ne1]
            )

@source_type(PerpendicularSegmentsProperty)
@processed_cache(set())
@accepts_auto
class PerpendicularSegmentsRule2(Rule):
    def apply(self, pv):
        seg0 = pv.segments[0]
        seg1 = pv.segments[1]
        common = common_endpoint(seg0, seg1)
        if common is None:
            return
        other0 = other_point(seg0.points, common)
        other1 = other_point(seg1.points, common)
        ncl = self.context.collinearity_property(common, other0, other1)
        if ncl is None:
            return
        self.processed.add(pv)
        if ncl.collinear:
            return
        yield (
            AngleValueProperty(common.angle(other0, other1), 90),
            Comment(
                'non-zero perpendicular segments $%{segment:seg0}$ and $%{segment:seg1}$',
                {'seg0': seg0, 'seg1': seg1}
            ),
            [pv, ncl]
        )

@processed_cache(set())
class Degree90ToPerpendicularSegmentsRule(Rule):
    def sources(self):
        return self.context.angle_value_properties_for_degree(
            90, lambda angle: angle not in self.processed
        )

    def apply(self, prop):
        self.processed.add(prop.angle)

        new_prop = PerpendicularSegmentsProperty(prop.angle.vectors[0].as_segment, prop.angle.vectors[1].as_segment)
        new_prop.add_base(prop)
        yield (
            new_prop,
            prop.reason.comment,
            prop.reason.premises
        )

@processed_cache(set())
class Degree90ToPerpendicularSegmentsRule2(Rule):
    def sources(self):
        return self.context.angle_value_properties_for_degree(90)

    def apply(self, prop):
        seg0 = prop.angle.vectors[0].as_segment
        seg1 = prop.angle.vectors[1].as_segment
        for pt in self.context.collinear_points(seg0):
            key = (prop, 0, pt)
            if key in self.processed:
                continue
            self.processed.add(key)

            for pt1 in seg0.points:
                yield (
                    PerpendicularSegmentsProperty(pt.segment(pt1), seg1),
                    Comment(
                        '$%{segment:seg0} \\perp %{segment:seg1}$, $%{point:pt}$ lies on $%{line:seg0}$',
                        {'seg0': seg0, 'seg1': seg1, 'pt': pt}
                    ),
                    [prop, self.context.point_on_line_property(seg0, pt)]
                )
        for pt in self.context.collinear_points(seg1):
            key = (prop, 1, pt)
            if key in self.processed:
                continue
            self.processed.add(key)

            for pt1 in seg1.points:
                yield (
                    PerpendicularSegmentsProperty(pt.segment(pt1), seg0),
                    Comment(
                        '$%{segment:seg1} \\perp %{segment:seg0}$, $%{point:pt}$ lies on $%{line:seg1}$',
                        {'seg0': seg0, 'seg1': seg1, 'pt': pt}
                    ),
                    [prop, self.context.point_on_line_property(seg1, pt)]
                )

@processed_cache(set())
class CommonPerpendicularRule(Rule):
    def sources(self):
        return self.context.angle_value_properties_for_degree(0)

    def apply(self, prop):
        segments = (prop.angle.vectors[0].as_segment, prop.angle.vectors[1].as_segment)
        for seg0, seg1 in (segments, reversed(segments)):
            for perp in self.context.list(PerpendicularSegmentsProperty, [seg0]):
                key = (prop, seg0, perp)
                if key in self.processed:
                    continue
                self.processed.add(key)

                other = perp.segments[1] if seg0 == perp.segments[0] else perp.segments[0]
                if prop.angle.vertex:
                    pattern = '$%{line:line0}$ is the same line as $%{line:line1}$'
                else:
                    pattern = 'any line perpendicular to $%{line:line0}$ is also perpendicular to $%{line:line1}$'
                comment = Comment(pattern, {'line0': seg0, 'line1': seg1})
                yield (
                    PerpendicularSegmentsProperty(seg1, other),
                    comment,
                    [perp, prop]
                )

@processed_cache(set())
class TwoPointsBelongsToTwoPerpendicularsRule(Rule):
    def sources(self):
        return itertools.combinations(self.context.list(PerpendicularSegmentsProperty), 2)

    def apply(self, src):
        key = frozenset(src)
        if key in self.processed:
            return
        perp0, perp1 = src
        common = next((seg for seg in perp0.segments if seg in perp1.segments), None)
        if common is None:
            self.processed.add(key)
            return
        seg0 = next(seg for seg in perp0.segments if seg != common)
        seg1 = next(seg for seg in perp1.segments if seg != common)
        points = set(seg0.points + seg1.points)
        if len(points) != 3:
            self.processed.add(key)
            return
        ncl = self.context.collinearity_property(*points)
        if ncl is None:
            return
        self.processed.add(key)
        if ncl.collinear:
            return
        yield (
            PointsCoincidenceProperty(*common.points, True),
            Comment(
                '$%{point:pt0}$ and $%{point:pt1}$ both lie on perpendiculars to non-parallel $%{line:line0}$ and $%{line:line1}$',
                {'pt0': common.points[0], 'pt1': common.points[1], 'line0': seg0, 'line1': seg1}
            ),
            [perp0, perp1, ncl]
        )

@processed_cache(set())
class PerpendicularTransitivityRule(Rule):
    def sources(self):
        return itertools.combinations(self.context.list(PerpendicularSegmentsProperty), 2)

    def apply(self, src):
        key = frozenset(src)
        if key in self.processed:
            return

        perp0, perp1 = src
        common = next((seg for seg in perp0.segments if seg in perp1.segments), None)
        if common is None:
            self.processed.add(key)
            return
        seg0 = next(seg for seg in perp0.segments if seg != common)
        seg1 = next(seg for seg in perp1.segments if seg != common)
        common_point = next((pt for pt in seg0.points if pt in seg1.points), None)
        if common_point is None:
            self.processed.add(key)
            return
        ne = self.context.coincidence_property(*common.points)
        if ne is None:
            return
        self.processed.add(key)
        if ne.coincident:
            return
        pt0 = next(pt for pt in seg0.points if pt != common_point)
        pt1 = next(pt for pt in seg1.points if pt != common_point)
        comment = Comment(
            '$%{segment:seg0}$ and $%{segment:seg1}$ are perpendiculars to line $%{line:line}$',
            {'seg0': seg0, 'seg1': seg1, 'line': common}
        )
        yield (
            PerpendicularSegmentsProperty(common, pt0.segment(pt1)),
            comment,
            [perp0, perp1, ne]
        )
        yield (
            PointsCollinearityProperty(common_point, pt0, pt1, True),
            comment,
            [perp0, perp1, ne]
        )

@source_type(PerpendicularSegmentsProperty)
@processed_cache({})
class PerpendicularToEquidistantRule(Rule):
    def apply(self, prop):
        if common_endpoint(*prop.segments) is not None:
            return

        mask = self.processed.get(prop, 0)
        if mask == 0xF:
            return
        original = mask

        pattern = '$%{point:point}$ lies on the perpendicular bisector to $%{segment:base}$'
        for seg0, seg1, bit in ((*prop.segments, 0x1), (prop.segments[1], prop.segments[0], 0x4)):
            segments = (
                [seg0.points[0].segment(pt) for pt in seg1.points],
                [seg0.points[1].segment(pt) for pt in seg1.points]
            )
            if (mask & bit) == 0:
                ratio, value = self.context.length_ratio_property_and_value(*segments[0], True)
                if ratio is not None:
                    mask |= bit
                    if value != 1:
                        mask |= bit << 1
                    else:
                        yield (
                            ProportionalLengthsProperty(*segments[1], 1),
                            Comment(pattern, {'point': seg0.points[1], 'base': seg1}),
                            [prop, ratio]
                        )
            if (mask & (bit << 1)) == 0:
                ratio, value = self.context.length_ratio_property_and_value(*segments[1], True)
                if ratio is not None:
                    mask |= bit << 1
                    if value != 1:
                        mask |= bit
                    else:
                        yield (
                            ProportionalLengthsProperty(*segments[0], 1),
                            Comment(pattern, {'point': seg0.points[0], 'base': seg1}),
                            [prop, ratio]
                        )

        if mask != original:
            self.processed[prop] = mask

@processed_cache({})
class EquidistantToPerpendicularRule(Rule):
    def sources(self):
        return itertools.combinations([p for p in self.context.congruent_segments_properties(allow_zeroes=True) if common_endpoint(p.segment0, p.segment1) is not None], 2)

    def apply(self, src):
        key = frozenset(src)
        mask = self.processed.get(key, 0)
        if mask == 0x3:
            return

        cs0, cs1 = src

        common0 = common_endpoint(cs0.segment0, cs0.segment1)
        common1 = common_endpoint(cs1.segment0, cs1.segment1)
        pts0 = [pt for pt in cs0.segment0.points + cs0.segment1.points if pt != common0]
        pts1 = [pt for pt in cs1.segment0.points + cs1.segment1.points if pt != common1]
        if set(pts0) != set(pts1):
            self.processed[key] = 0x3
            return

        original = mask
        try:
            segment0 = common0.segment(common1)
            segment1 = pts0[0].segment(pts0[1])
            if (mask & 0x1) == 0:
                mask |= 0x1
                yield (
                    PerpendicularSegmentsProperty(segment0, segment1),
                    Comment(
                        'both $%{point:pt0}$ and $%{point:pt1}$ are equidistant from $%{point:endpoint0}$ and $%{point:endpoint1}$',
                        {'pt0': common0, 'pt1': common1, 'endpoint0': pts0[0], 'endpoint1': pts0[1]}
                    ),
                    [cs0, cs1]
                )

            ne0 = self.context.coincidence_property(*segment0.points)
            if ne0 is None:
                return
            if ne0.coincident:
                mask |= 0x2
                return
            ne1 = self.context.coincidence_property(*segment1.points)
            if ne1 is None:
                return
            mask |= 0x2
            if ne1.coincident:
                return
            yield (
                SameOrOppositeSideProperty(segment0, *pts0, False),
                Comment(
                    'perpendicular bisector $%{line:bisector}$ separates endpoints of $%{segment:segment}$',
                    {'bisector': segment0, 'segment': segment1}
                ),
                [cs0, cs1, ne0, ne1]
            )
        finally:
            if mask != original:
                self.processed[key] = mask

@source_type(SameOrOppositeSideProperty)
@processed_cache({})
class EqualAnglesToCollinearityRule(Rule):
    def accepts(self, prop):
        return prop.same

    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0x3:
            return

        original = mask
        for (p0, p1), bit in ((prop.segment.points, 1), (reversed(prop.segment.points), 2)):
            if mask & bit:
                continue
            angles = [p0.angle(p1, pt) for pt in prop.points]
            ratio = self.context.angle_ratio(*angles)
            if ratio is None:
                continue
            mask |= bit
            if ratio != 1:
                continue
            ca = self.context.angle_ratio_property(*angles)
            comment = Comment(
                '$%{anglemeasure:angle0} = %{anglemeasure:angle1}$, and points $%{point:pt0}$ and $%{point:pt1}$ are on the same side of $%{line:line}$',
                {'angle0': angles[0], 'angle1': angles[1], 'pt0': prop.points[0], 'pt1': prop.points[1], 'line': prop.segment}
            )
            yield (
                AngleValueProperty(p0.angle(*prop.points), 0),
                comment,
                [ca, prop]
            )
            yield (
                PointsCollinearityProperty(p0, *prop.points, True),
                comment,
                [ca, prop]
            )

        if mask != original:
            self.processed[prop] = mask

@source_type(SameOrOppositeSideProperty)
@processed_cache(set())
class PointsSeparatedByLineAreNotCoincidentRule(Rule):
    """
    If two points are separated by a line, the points are not coincident
    """
    def accepts(self, prop):
        return not prop.same and prop not in self.processed

    def apply(self, prop):
        self.processed.add(prop)

        yield (
            PointsCoincidenceProperty(prop.points[0], prop.points[1], False),
            Comment('the points are separated by $%{line:line}$', {'line': prop.segment}),
            [prop]
        )

@source_type(SameOrOppositeSideProperty)
@processed_cache(set())
class SameSidePointInsideSegmentRule(Rule):
    """
    If endpoints of a segment are on the same side of a line,
    then any point inside the segment in on the same side too
    """
    def accepts(self, prop):
        return prop.same

    def apply(self, prop):
        segment = prop.points[0].segment(prop.points[1])
        for inside in self.context.points_inside_segment(segment):
            key = (prop, inside)
            if key in self.processed:
                continue
            self.processed.add(key)
            comment = Comment(
                'segment $%{segment:segment}$ contains $%{point:inside}$ and does not cross line $%{line:line}$',
                {'segment': segment, 'line': prop.segment, 'inside': inside}
            )
            inside_prop = self.context.angle_value_property(inside.angle(*prop.points))
            for new_prop in (
                SameOrOppositeSideProperty(prop.segment, prop.points[0], inside, True),
                SameOrOppositeSideProperty(prop.segment, prop.points[1], inside, True),
                PointsCollinearityProperty(inside, *prop.segment.points, False),
            ):
                yield (new_prop, comment, [prop, inside_prop])

@source_type(SameOrOppositeSideProperty)
@processed_cache(set())
class PointInsideSegmentRelativeToLineRule(Rule):
    def apply(self, prop):
        for index, (pt_on, pt_not_on) in enumerate(itertools.product(prop.segment.points, prop.points)):
            segment = pt_on.segment(pt_not_on)
            for inside in self.context.points_inside_segment(segment):
                if inside in prop.points:
                    continue
                key = (prop, index, inside)
                if key in self.processed:
                    continue
                self.processed.add(key)
                pt2 = prop.points[1] if pt_not_on == prop.points[0] else prop.points[0]
                if prop.same:
                    pattern = '$%{point:pt_not_on}$ and $%{point:pt2}$ are on the same side of $%{line:line}$ and $%{point:inside}$ lies inside $%{segment:segment}$'
                else:
                    pattern = '$%{point:pt_not_on}$ and $%{point:pt2}$ are on opposite sides of $%{line:line}$ and $%{point:inside}$ lies inside $%{segment:segment}$'
                inside_prop = self.context.angle_value_property(inside.angle(*segment.points))
                yield (
                    SameOrOppositeSideProperty(prop.segment, inside, pt2, prop.same),
                    Comment(pattern, {
                        'pt_not_on': pt_not_on,
                        'pt2': pt2,
                        'line': prop.segment,
                        'inside': inside,
                        'segment': segment
                    }),
                    [prop, inside_prop]
                )

@source_type(SameOrOppositeSideProperty)
@processed_cache(set())
@accepts_auto
class TwoPerpendicularsRule(Rule):
    """
    Two perpendiculars to the same line are parallel
    """
    def apply(self, prop):
        foot0 = self.context.foot_of_perpendicular(prop.points[0], prop.segment)
        if foot0 is None:
            return
        foot1 = self.context.foot_of_perpendicular(prop.points[1], prop.segment)
        if foot1 is None:
            return
        self.processed.add(prop)
        premises = [
            prop,
            self.context.foot_of_perpendicular_property(foot0, prop.points[0], prop.segment),
            self.context.foot_of_perpendicular_property(foot1, prop.points[1], prop.segment)
        ]
        vec0 = foot0.vector(prop.points[0])
        vec1 = foot1.vector(prop.points[1]) if prop.same else prop.points[1].vector(foot1)
        yield (
            ParallelVectorsProperty(vec0, vec1),
            Comment('two perpendiculars to $%{line:line}$', {'line': prop.segment}),
            premises
        )

@processed_cache(set())
class TwoPerpendicularsRule2(Rule):
    """
    Two perpendiculars to the same line are parallel
    """
    def sources(self):
        return itertools.combinations(self.context.list(PerpendicularSegmentsProperty), 2)

    def apply(self, src):
        key = frozenset(src)
        if key in self.processed:
            return

        perp0, perp1 = src
        common = next((seg for seg in perp0.segments if seg in perp1.segments), None)
        if common is None:
            self.processed.add(key)
            return
        ne = self.context.coincidence_property(*common.points)
        if ne is None:
            return
        self.processed.add(key)
        if ne.coincident:
            return
        other0 = next(seg for seg in perp0.segments if seg != common)
        other1 = next(seg for seg in perp1.segments if seg != common)
        yield (
            ParallelSegmentsProperty(other0, other1),
            Comment(
                '$%{segment:seg0} \\perp %{segment:seg1} \\perp %{segment:seg2}$',
                {'seg0': other0, 'seg1': common, 'seg2': other1}
            ),
            [perp0, perp1, ne]
        )

@processed_cache({})
class ZeroAngleVectorsToPointAndLineConfigurationRule(Rule):
    def sources(self):
        return self.context.angle_value_properties_for_degree(0, lambda a: len(a.point_set) == 4)

    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0xF:
            return
        original = mask

        ang = prop.angle
        all_points = ang.vectors[0].points + ang.vectors[1].points
        for index, pt in enumerate(all_points):
            bit = 1 << index
            if mask & bit:
                continue
            triple = tuple(p for p in all_points if p != pt)
            ncl = self.context.collinearity_property(*triple)
            if ncl is None:
                continue
            if ncl.collinear:
                mask = 0xF
                break
            mask |= bit
            comment = Comment(
                '$%{vector:vec0}$ and $%{vector:vec1}$ are parallel but not collinear',
                {'vec0': ang.vectors[0], 'vec1': ang.vectors[1]}
            )
            premises = [prop, ncl]
            for new_prop in (
                SameOrOppositeSideProperty(ang.vectors[0].as_segment, *ang.vectors[1].points, True),
                SameOrOppositeSideProperty(ang.vectors[1].as_segment, *ang.vectors[0].points, True),
                SameOrOppositeSideProperty(
                    ang.vectors[0].start.segment(ang.vectors[1].start),
                    ang.vectors[0].end, ang.vectors[1].end, True
                ),
                SameOrOppositeSideProperty(
                    ang.vectors[0].end.segment(ang.vectors[1].end),
                    ang.vectors[0].start, ang.vectors[1].start, True
                ),
                SameOrOppositeSideProperty(
                    ang.vectors[0].start.segment(ang.vectors[1].end),
                    ang.vectors[0].end, ang.vectors[1].start, False
                ),
                SameOrOppositeSideProperty(
                    ang.vectors[1].start.segment(ang.vectors[0].end),
                    ang.vectors[1].end, ang.vectors[0].start, False
                ),
            ):
                yield (new_prop, comment, premises)

        if mask != original:
            self.processed[prop] = mask

@source_type(ParallelSegmentsProperty)
@processed_cache({})
class ParallelSameSideRule(Rule):
    def accepts(self, prop):
        return common_endpoint(prop.segments[0], prop.segments[1]) is None

    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0xF:
            return
        original = mask

        index = 0
        for seg0, seg1 in (prop.segments, reversed(prop.segments)):
            comment = Comment(
                '$%{point:pt0}$ and $%{point:pt1}$ lie on a line parallel to $%{line:line}$',
                {'pt0': seg1.points[0], 'pt1': seg1.points[1], 'line': seg0}
            )
            for pt in seg1.points:
                bit = 1 << index
                index += 1
                if mask & bit:
                    continue
                ncl = self.context.collinearity_property(*seg0.points, pt)
                if ncl is None:
                    continue
                mask |= bit
                if ncl.collinear:
                    mask = 0xF
                    break
                yield (
                    SameOrOppositeSideProperty(seg0, *seg1.points, True),
                    comment, [prop, ncl]
                )

        if mask != original:
            self.processed[prop] = mask

@processed_cache({})
class RotatedAngleSimplifiedRule(Rule):
    def sources(self):
        for prop in self.context.angle_value_properties_for_degree(180, lambda a: a.vertex):
            segment = prop.angle.endpoints[0].segment(prop.angle.endpoints[1])
            for oppo in self.context.list(SameOrOppositeSideProperty, [segment]):
                if oppo.same:
                    yield (prop, oppo)

    def apply(self, src):
        mask = self.processed.get(src, 0)
        if mask == 0x3:
            return
        prop, oppo = src
        ang = prop.angle
        angles0 = (
            ang.vertex.angle(ang.endpoints[0], oppo.points[0]),
            ang.vertex.angle(ang.endpoints[1], oppo.points[1])
        )
        angles1 = (
            ang.vertex.angle(ang.endpoints[0], oppo.points[1]),
            ang.vertex.angle(ang.endpoints[1], oppo.points[0])
        )

        original = mask
        for angs0, angs1, bit in [(angles0, angles1, 1), (angles1, angles0, 2)]:
            if mask & bit:
                continue
            ar = self.context.angle_ratio_property(*angs0)
            if ar is None:
                continue
            if ar.value != 1:
                mask = 0x3
                break
            mask |= bit
            yield (
                AngleRatioProperty(*angs1, 1),
                LazyComment('TODO: write comment'),
                [ar, prop, oppo]
            )

        if mask != original:
            self.processed[src] = mask

@source_type(SameOrOppositeSideProperty)
@processed_cache({})
class TwoAcuteOrRightAnglesWithCommonSideRule(Rule):
    def accepts(self, prop):
        return not prop.same

    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0x3:
            return
        original = mask

        for v0, v1, bit in [(*prop.segment.points, 0x1), (*reversed(prop.segment.points), 0x2)]:
            if mask & bit:
                continue

            kind0 = self.context.angle_kind_property(v0.angle(prop.points[0], v1))
            if kind0 is None:
                continue
            if kind0.kind == AngleKindProperty.Kind.obtuse:
                mask |= bit
                continue
            kind1 = self.context.angle_kind_property(v0.angle(prop.points[1], v1))
            if kind1 is None:
                continue
            mask |= bit
            if kind1.kind == AngleKindProperty.Kind.obtuse:
                continue
            if kind1.kind == AngleKindProperty.Kind.right and kind0.kind == kind1.kind:
                continue

            if kind0.kind == AngleKindProperty.Kind.acute:
                if kind1.kind == AngleKindProperty.Kind.acute:
                    pattern = 'acute angles $%{angle:angle0}$ and $%{angle:angle1}$ with common side $%{ray:side}$'
                else:
                    pattern = 'acute $%{angle:angle0}$ and right $%{angle:angle1}$ with common side $%{ray:side}$'
            else:
                pattern = 'acute $%{angle:angle1}$ and right $%{angle:angle0}$ with common side $%{ray:side}$'
            yield (
                PointInsideAngleProperty(v1, v0.angle(*prop.points)),
                Comment(
                    pattern,
                    {'angle0': kind0.angle, 'angle1': kind1.angle, 'side': v0.vector(v1)}
                ),
                [kind0, kind1, prop]
            )

        if mask != original:
            self.processed[prop] = mask

@processed_cache({})
class CongruentAnglesWithCommonPartRule(Rule):
    def sources(self):
        pias = self.context.list(PointInsideAngleProperty)
        return [(p0, p1) for (p0, p1) in itertools.combinations(pias, 2) if p0.angle.vertex == p1.angle.vertex and p0.point in p1.angle.endpoints and p1.point in p0.angle.endpoints]

    def apply(self, src):
        key = frozenset(src)
        mask = self.processed.get(key, 0)
        if mask == 0x3:
            return
        original = mask

        prop0, prop1 = src
        sum0, sum1 = prop0.angle, prop1.angle
        vertex = sum0.vertex
        common = vertex.angle(prop0.point, prop1.point)
        pt0 = next(pt for pt in sum0.endpoints if pt != prop1.point)
        pt1 = next(pt for pt in sum1.endpoints if pt != prop0.point)
        summand0 = vertex.angle(pt0, prop0.point)
        summand1 = vertex.angle(pt1, prop1.point)

        if (mask & 0x1) == 0:
            known = self.context.angle_ratio_property(sum0, sum1)
            if known:
                if known.value == 1:
                    mask |= 0x1
                    yield (
                        AngleRatioProperty(summand0, summand1, 1),
                        Comment(
                            '$%{anglemeasure:summand0} = %{anglemeasure:sum0} - %{anglemeasure:common} = %{anglemeasure:sum1} - %{anglemeasure:common} = %{anglemeasure:summand1}$',
                            {'sum0': sum0, 'sum1': sum1, 'common': common, 'summand0': summand0, 'summand1': summand1}
                        ),
                        [known, prop0, prop1]
                    )
                else:
                    mask = 0x3

        if (mask & 0x2) == 0:
            known = self.context.angle_ratio_property(summand0, summand1)
            if known:
                if known.value == 1:
                    mask |= 0x2
                    yield (
                        AngleRatioProperty(sum0, sum1, 1),
                        Comment(
                            '$%{angle:sum0}$ and $%{angle:sum1}$ consist of common part $%{angle:common}$ and congruent $%{angle:summand0}$ and $%{angle:summand1}$',
                            {'sum0': sum0, 'sum1': sum1, 'common': common, 'summand0': summand0, 'summand1': summand1}
                        ),
                        [known, prop0, prop1]
                    )
                else:
                    mask = 0x3

        if mask != original:
            self.processed[key] = mask

@source_type(PointInsideAngleProperty)
@processed_cache(set())
class PointInsidePartOfAngleRule(Rule):
    def apply(self, prop):
        for pt in prop.angle.endpoints:
            part = prop.angle.vertex.angle(pt, prop.point)
            for prop1 in self.context.list(PointInsideAngleProperty, [part]):
                key = (prop, prop1)
                if key in self.processed:
                    continue
                self.processed.add(key)
                comment = Comment(
                    '$%{point:point}$ lies inside $%{angle:part}$ that is part of $%{angle:full}$',
                    {'point': prop1.point, 'part': part, 'full': prop.angle}
                )
                yield (
                    PointInsideAngleProperty(prop1.point, prop.angle),
                    comment,
                    [prop1, prop]
                )
                pt1 = next(p for p in prop.angle.endpoints if p != pt)
                yield (
                    PointInsideAngleProperty(prop.point, prop.angle.vertex.angle(pt1, prop1.point)),
                    comment,
                    [prop1, prop]
                )

@source_type(PointInsideAngleProperty)
@processed_cache(set())
@accepts_auto
class PartOfAcuteAngleIsAcuteRule(Rule):
    def apply(self, prop):
        kind = self.context.angle_kind_property(prop.angle)
        if kind is None:
            return
        self.processed.add(prop)
        if kind.kind == AngleKindProperty.Kind.acute:
            pattern = '$%{angle:part}$ is a part of acute $%{angle:whole}$'
        elif kind.kind == AngleKindProperty.Kind.right:
            pattern = '$%{angle:part}$ is a part of right $%{angle:whole}$'
        else:
            return
        for vec in prop.angle.vectors:
            angle = prop.angle.vertex.angle(vec.end, prop.point)
            yield (
                AngleKindProperty(angle, AngleKindProperty.Kind.acute),
                Comment(pattern, {'part': angle, 'whole': prop.angle}),
                [prop, kind]
            )

@processed_cache(set())
@accepts_auto
class AngleTypeByDegreeRule(Rule):
    def sources(self):
        return self.context.nondegenerate_angle_value_properties()

    def apply(self, prop):
        self.processed.add(prop)
        if prop.degree in (0, 180):
            return
        pattern = '$%{degree:min} < %{anglemeasure:angle} = %{degree:degree} < %{degree:max}$'
        if prop.degree < 90:
            yield (
                AngleKindProperty(prop.angle, AngleKindProperty.Kind.acute),
                Comment(pattern, {'angle': prop.angle, 'degree': prop.degree, 'min': 0, 'max': 90}),
                [prop]
            )
        elif prop.degree > 90:
            yield (
                AngleKindProperty(prop.angle, AngleKindProperty.Kind.obtuse),
                Comment(pattern, {'angle': prop.angle, 'degree': prop.degree, 'min': 90, 'max': 180}),
                [prop]
            )
        else:
            yield (
                AngleKindProperty(prop.angle, AngleKindProperty.Kind.right),
                prop.reason.comment,
                prop.reason.premises
            )

@processed_cache(set())
class PointsCollinearityByAngleDegreeRule(Rule):
    def sources(self):
        return self.context.angle_value_properties()

    def accepts(self, prop):
        return prop.angle.vertex and prop not in self.processed

    def apply(self, prop):
        self.processed.add(prop)
        yield (
            PointsCollinearityProperty(*prop.angle.point_set, prop.degree in (0, 180)),
            Comment(
                '$%{anglemeasure:angle} = %{degree:degree}$',
                {'angle': prop.angle, 'degree': prop.degree}
            ),
            [prop]
        )

@source_type(AngleKindProperty)
@processed_cache(set())
class RightAngleDegreeRule(Rule):
    def accepts(self, prop):
        return prop.kind == AngleKindProperty.Kind.right and prop not in self.processed

    def apply(self, prop):
        self.processed.add(prop)

        yield (
            AngleValueProperty(prop.angle, 90),
            prop.reason.comment,
            prop.reason.premises
        )

@source_type(AngleKindProperty)
@processed_cache(set())
class AngleTypesInObtuseangledTriangleRule(Rule):
    def accepts(self, prop):
        return prop.angle.vertex and prop.kind != AngleKindProperty.Kind.acute and prop not in self.processed

    def apply(self, prop):
        self.processed.add(prop)

        if prop.kind == AngleKindProperty.Kind.obtuse:
            pattern = 'an angle of $%{triangle:triangle}$, another $%{angle:other}$ is obtuse'
        else:
            pattern = 'an angle of $%{triangle:triangle}$, another $%{angle:other}$ is right'
        triangle = Scene.Triangle(prop.angle.vertex, *prop.angle.endpoints)
        comment = Comment(pattern, {'triangle': triangle, 'other': prop.angle})
        for angle in triangle.angles[1:]:
            yield (
                AngleKindProperty(angle, AngleKindProperty.Kind.acute),
                comment,
                [prop]
            )

@processed_cache(set())
@accepts_auto
class VerticalAnglesRule(Rule):
    def sources(self):
        return itertools.combinations(self.context.angle_value_properties_for_degree(180, lambda a: a.vertex), 2)

    @classmethod
    def priority(clazz):
        return 1

    def apply(self, src):
        av0, av1 = src
        self.processed.add(src)
        self.processed.add((av1, av0))

        ng0 = av0.angle
        ng1 = av1.angle
        if ng0.vertex != ng1.vertex:
            return
        if len(ng0.point_set.union(ng1.point_set)) != 5:
            return

        pattern = '$%{angle:angle0}$ and $%{angle:angle1}$ are vertical angles'
        new_prop = AngleRatioProperty(
            ng0.vertex.angle(ng0.vectors[0].end, ng1.vectors[0].end),
            ng0.vertex.angle(ng0.vectors[1].end, ng1.vectors[1].end),
            1
        )
        yield (
            new_prop,
            Comment(pattern, {'angle0': new_prop.angle0, 'angle1': new_prop.angle1}),
            [av0, av1]
        )
        new_prop = AngleRatioProperty(
            ng0.vertex.angle(ng0.vectors[0].end, ng1.vectors[1].end),
            ng0.vertex.angle(ng0.vectors[1].end, ng1.vectors[0].end),
            1
        )
        yield (
            new_prop,
            Comment(pattern, {'angle0': new_prop.angle0, 'angle1': new_prop.angle1}),
            [av0, av1]
        )

@processed_cache({})
class ReversedVerticalAnglesRule(Rule):
    def sources(self):
        return self.context.angle_value_properties_for_degree(180, lambda a: a.vertex)

    def apply(self, prop):
        angle = prop.angle
        line = angle.vectors[0].end.segment(angle.vectors[1].end)
        for oppo in self.context.list(SameOrOppositeSideProperty, [line]):
            if oppo.same:
                continue
            key = (prop, oppo)
            mask = self.processed.get(key, 0)
            if mask == 0x3:
                continue
            original = mask
            for pt0, pt1, bit in ((*oppo.points, 0x1), (*reversed(oppo.points), 0x2)):
                if mask & bit:
                    continue
                ang0 = angle.vertex.angle(angle.vectors[0].end, pt0)
                ang1 = angle.vertex.angle(angle.vectors[1].end, pt1)
                ar = self.context.angle_ratio_property(ang0, ang1)
                if ar is None:
                    continue
                mask |= bit
                if ar.value != 1:
                    continue
                yield (
                    AngleValueProperty(angle.vertex.angle(pt0, pt1), 180),
                    Comment(
                        '$%{anglemeasure:angle0} = %{anglemeasure:angle1}$ and $%{point:pt}$ lies on segment $%{segment:segment}$',
                        {'angle0': ang0, 'angle1': ang1, 'pt': angle.vertex, 'segment': angle.endpoints[0].segment(angle.endpoints[1])}
                    ),
                    [ar, prop, oppo]
                )
            if mask != original:
                self.processed[key] = mask

@source_type(SameOrOppositeSideProperty)
@processed_cache({})
class CorrespondingAndAlternateAnglesRule(Rule):
    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0x3:
            return
        original = mask

        lp0 = prop.segment.points[0]
        lp1 = prop.segment.points[1]
        for pt0, pt1, bit in [(*prop.points, 1), (*reversed(prop.points), 2)]:
            if mask & bit:
                continue
            angle0 = lp0.angle(pt0, lp1)
            angle1 = lp1.angle(pt1, lp0)
            if prop.same:
                sum_degree = self.context.sum_of_angles(angle0, angle1)
                if sum_degree is None:
                    continue
                mask |= bit
                if sum_degree != 180:
                    continue
                sum_reason = self.context.sum_of_angles_property(angle0, angle1)
                for p in AngleValueProperty.generate(lp0.vector(pt0), lp1.vector(pt1), 0):
                    yield (
                        p,
                        Comment(
                            'sum of consecutive angles: $%{anglemeasure:angle0} + %{anglemeasure:angle1} = %{degree:180}$',
                            {'angle0': angle0, 'angle1': angle1, '180': 180}
                        ),
                        [prop, sum_reason]
                    )
            else:
                ratio_reason = self.context.angle_ratio_property(angle0, angle1)
                if ratio_reason is None:
                    continue
                mask |= bit
                if ratio_reason.value != 1:
                    continue
                for p in AngleValueProperty.generate(lp0.vector(pt0), pt1.vector(lp1), 0):
                    yield (
                        p,
                        Comment(
                            'alternate angles $%{angle:angle0}$ and $%{angle:angle1}$ are congruent',
                            {'angle0': angle0, 'angle1': angle1}
                        ),
                        [prop, ratio_reason]
                    )

        if mask != original:
            self.processed[prop] = mask

@processed_cache(set())
class SupplementaryAnglesRule(Rule):
    def sources(self):
        return self.context.angle_value_properties_for_degree(180, lambda a: a.vertex)

    def apply(self, prop):
        ang = prop.angle
        for pt in self.context.non_coincident_points(ang.vertex):
            if pt in ang.endpoints:
                continue
            key = (ang, pt)
            if key in self.processed:
                continue
            self.processed.add(key)

            neq = self.context.coincidence_property(ang.vertex, pt)
            angle0 = ang.vertex.angle(ang.endpoints[0], pt)
            angle1 = ang.vertex.angle(ang.endpoints[1], pt)
            yield (
                SumOfAnglesProperty(angle0, angle1, degree=180),
                Comment(
                    'supplementary angles: common side $%{ray:common}$, and $%{ray:vec0} \\uparrow\\!\\!\\!\\downarrow %{ray:vec1}$',
                    {'common': ang.vertex.vector(pt), 'vec0': ang.vectors[0], 'vec1': ang.vectors[1]}
                ),
                [prop, neq]
            )

@processed_cache(set())
class ZeroDegreeTransitivityRule(Rule):
    def sources(self):
        angles = self.context.angle_value_properties_for_degree(0)
        return itertools.combinations(angles, 2)

    def apply(self, src):
        prop0, prop1 = src
        common = next((v for v in prop0.angle.vectors if v in prop1.angle.vectors), None)
        if common is None:
            return
        key = frozenset((prop0.angle, prop1.angle))
        if key in self.processed:
            return
        self.processed.add(key)
        v0 = next(v for v in prop0.angle.vectors if v != common)
        v1 = next(v for v in prop1.angle.vectors if v != common)
        yield (
            AngleValueProperty(v0.angle(v1), 0),
            Comment(
                '$%{vector:vec0} \\uparrow\\!\\!\\!\\uparrow %{vector:common} \\uparrow\\!\\!\\!\\uparrow %{vector:vec1}$',
                {'vec0': v0, 'vec1': v1, 'common': common}
            ),
            [prop0, prop1]
        )
        yield (
            AngleValueProperty(v0.reversed.angle(v1.reversed), 0),
            Comment(
                '$%{vector:vec0} \\uparrow\\!\\!\\!\\uparrow %{vector:common} \\uparrow\\!\\!\\!\\uparrow %{vector:vec1}$',
                {'vec0': v0.reversed, 'vec1': v1.reversed, 'common': common.reversed}
            ),
            [prop0, prop1]
        )
        yield (
            AngleValueProperty(v0.angle(v1.reversed), 180),
            Comment(
                '$%{vector:vec0} \\uparrow\\!\\!\\!\\uparrow %{vector:common} \\uparrow\\!\\!\\!\\downarrow %{vector:vec1}$',
                {'vec0': v0, 'vec1': v1.reversed, 'common': common}
            ),
            [prop0, prop1]
        )
        yield (
            AngleValueProperty(v0.reversed.angle(v1), 180),
            Comment(
                '$%{vector:vec0} \\uparrow\\!\\!\\!\\downarrow %{vector:common} \\uparrow\\!\\!\\!\\uparrow %{vector:vec1}$',
                {'vec0': v0.reversed, 'vec1': v1, 'common': common}
            ),
            [prop0, prop1]
        )

@processed_cache(set())
class CorrespondingAnglesRule(Rule):
    def sources(self):
        return self.context.angle_value_properties_for_degree(0, lambda a: len(a.point_set) == 4)

    def apply(self, prop):
        ang = prop.angle
        starts = tuple(vec.start for vec in ang.vectors)
        segment = starts[0].segment(starts[1])
        for pt in self.context.collinear_points(segment):
            if pt in ang.point_set:
                continue
            key = (prop, pt)
            if key in self.processed:
                continue
            av = self.context.angle_value_property(pt.angle(*starts))
            if av is None:
                continue
            self.processed.add(key)
            if av.degree == 180:
                continue
            vec0 = starts[0].vector(pt)
            angle0 = ang.vectors[0].angle(vec0)
            vec1 = starts[1].vector(pt)
            angle1 = ang.vectors[1].angle(vec1)
            yield (
                AngleRatioProperty(angle0, angle1, 1),
                Comment(
                    'corresponding angles: transversal $%{line:common}$, and $%{ray:vec0} \\uparrow\\!\\!\\!\\uparrow %{ray:vec1}$',
                    {'common': segment, 'vec0': ang.vectors[0], 'vec1': ang.vectors[1]}
                ),
                [prop, av]
            )

@processed_cache(set())
@accepts_auto
class ConsecutiveInteriorAnglesRule(Rule):
    def sources(self):
        return self.context.angle_value_properties_for_degree(0, lambda a: len(a.point_set) == 4)

    def apply(self, prop):
        vecs = prop.angle.vectors
        ne = self.context.coincidence_property(vecs[0].start, vecs[1].start)
        if ne is None:
            return
        self.processed.add(prop)
        if ne.coincident:
            return
        angle0 = vecs[0].start.angle(vecs[0].end, vecs[1].start)
        angle1 = vecs[1].start.angle(vecs[1].end, vecs[0].start)
        yield (
            SumOfAnglesProperty(angle0, angle1, degree=180),
            Comment(
                'consecutive interior angles: transversal $%{line:common}$, and $%{ray:vec0} \\uparrow\\!\\!\\!\\uparrow %{ray:vec1}$',
                {'common': vecs[0].start.segment(vecs[1].start), 'vec0': vecs[0], 'vec1': vecs[1]}
            ),
            [prop, ne]
        )

@processed_cache(set())
@accepts_auto
class AlternateInteriorAnglesRule(Rule):
    def sources(self):
        return self.context.angle_value_properties_for_degree(180, lambda a: len(a.point_set) == 4)

    def apply(self, prop):
        vecs = prop.angle.vectors
        neq = self.context.coincidence_property(vecs[0].start, vecs[1].start)
        if neq is None:
            return
        self.processed.add(prop)
        if neq.coincident:
            return
        angle0 = vecs[0].start.angle(vecs[0].end, vecs[1].start)
        angle1 = vecs[1].start.angle(vecs[1].end, vecs[0].start)
        yield (
            AngleRatioProperty(angle0, angle1, 1),
            Comment(
                'alternate interior angles: transversal $%{line:common}$, and $%{ray:vec0} \\uparrow\\!\\!\\!\\downarrow %{ray:vec1}$',
                {'common': vecs[0].start.segment(vecs[1].start), 'vec0': vecs[0], 'vec1': vecs[1]}
            ),
            [prop, neq]
        )

@processed_cache(set())
class TwoPointsInsideSegmentRule(Rule):
    def sources(self):
        segment_to_props = {}
        for av in self.context.angle_value_properties_for_degree(180, lambda a: a.vertex):
            segment = av.angle.endpoints[0].segment(av.angle.endpoints[1])
            props = segment_to_props.get(segment)
            if props:
                props.add(av)
            else:
                segment_to_props[segment] = {av}

        for segment, props in segment_to_props.items():
            for av0, av1 in itertools.combinations(props, 2):
                key = frozenset([av0.angle, av1.angle])
                if key not in self.processed:
                    self.processed.add(key)
                    yield (segment, av0, av1)

    def apply(self, src):
        segment, av0, av1 = src

        pt0 = av0.angle.vertex
        pt1 = av1.angle.vertex
        for pt in segment.points:
            yield (
                AngleValueProperty(pt.angle(pt0, pt1), 0),
                Comment(
                    'both $%{point:pt0}$ and $%{point:pt1}$ lie inside segment $%{segment:segment}$',
                    {'pt0': pt0, 'pt1': pt1, 'segment': segment}
                ),
                [av0, av1]
            )

@processed_cache(set())
class TwoPointsOnRayRule(Rule):
    def sources(self):
        return self.context.angle_value_properties_for_degree(0, lambda a: a.vertex)

    def apply(self, prop):
        zero = prop.angle
        pt0, pt1 = zero.endpoints
        for pt in self.context.not_collinear_points(zero.vectors[0].as_segment):
            key = (zero, pt)
            if key in self.processed:
                continue
            angle0 = pt0.angle(zero.vertex, pt)
            value0 = self.context.angle_value_property(angle0)
            if value0 is None:
                continue
            angle1 = pt1.angle(zero.vertex, pt)
            value1 = self.context.angle_value_property(angle1)
            if value1 is None:
                continue
            self.processed.add(key)
            pattern = '$%{point:pt}$ lies on $%{ray:ray}$ and $%{anglemeasure:lesser} < %{anglemeasure:greater}$'
            if value0.degree < value1.degree:
                comment = Comment(
                    pattern,
                    {'pt': pt0, 'ray': zero.vertex.vector(pt1), 'lesser': angle0, 'greater': angle1}
                )
                yield (
                    AngleValueProperty(pt0.angle(pt1, zero.vertex), 0),
                    comment,
                    [prop, value0, value1]
                )
                yield (
                    AngleValueProperty(pt1.angle(pt0, zero.vertex), 180),
                    comment,
                    [prop, value0, value1]
                )
                yield (
                    PointsCoincidenceProperty(pt0, pt1, False),
                    Comment(
                        '$%{anglemeasure:angle0} \\neq %{anglemeasure:angle1}$',
                        {'angle0': angle0, 'angle1': angle1}
                    ),
                    [value0, value1]
                )
            elif value1.degree < value0.degree:
                comment = Comment(
                    pattern,
                    {'pt': pt1, 'ray': zero.vertex.vector(pt0), 'lesser': angle1, 'greater': angle0}
                )
                yield (
                    AngleValueProperty(pt1.angle(pt0, zero.vertex), 0),
                    comment,
                    [prop, value0, value1]
                )
                yield (
                    AngleValueProperty(pt0.angle(pt1, zero.vertex), 180),
                    comment,
                    [prop, value0, value1]
                )
                yield (
                    PointsCoincidenceProperty(pt0, pt1, False),
                    Comment(
                        '$%{anglemeasure:angle0} \\neq %{anglemeasure:angle1}$',
                        {'angle0': angle0, 'angle1': angle1}
                    ),
                    [value0, value1]
                )
            else:
                yield (
                    PointsCoincidenceProperty(pt0, pt1, True),
                    Comment(
                        '$%{point:pt}$ lies on $%{ray:ray}$ and $%{anglemeasure:angle0} = %{anglemeasure:angle1}$',
                        {'pt': pt0, 'ray': zero.vertex.vector(pt1), 'angle0': angle0, 'angle1': angle1}
                    ),
                    [prop, value0, value1]
                )

@processed_cache(set())
class SameAngleRule(Rule):
    def sources(self):
        return itertools.combinations([av for av in self.context.list(AngleValueProperty) if av.angle.vertex and av.degree == 0], 2)

    def apply(self, src):
        if src in self.processed:
            return
        self.processed.add(src)

        av0, av1 = src
        ng0 = av0.angle
        ng1 = av1.angle
        if ng0.vertex != ng1.vertex:
            return
        if len(ng0.point_set.union(ng1.point_set)) != 5:
            return

        angle0 = ng0.vertex.angle(ng0.vectors[0].end, ng1.vectors[0].end)
        angle1 = ng0.vertex.angle(ng0.vectors[1].end, ng1.vectors[1].end)
        yield (
            AngleRatioProperty(angle0, angle1, 1, same=True),
            Comment(
                '$%{point:pt0}$ lies on $%{ray:vec1}$ and $%{point:pt2}$ lies on $%{ray:vec3}$',
                {
                    'pt0': ng0.vectors[0].end,
                    'vec1': ng0.vectors[1],
                    'pt2': ng1.vectors[0].end,
                    'vec3': ng1.vectors[1]
                }
            ),
            [av0, av1]
        )

@processed_cache(set())
class SameAngleRule2(Rule):
    def sources(self):
        return self.context.angle_value_properties_for_degree(180, lambda a: a.vertex)

    def apply(self, prop):
        angle = prop.angle
        side = angle.endpoints[0].segment(angle.endpoints[1])
        for pt in self.context.not_collinear_points(side):
            key = (angle, pt)
            if key in self.processed:
                continue
            self.processed.add(key)

            for pt0, pt1 in (angle.endpoints, reversed(angle.endpoints)):
                angle0 = pt0.angle(pt, pt1)
                angle1 = pt0.angle(pt, angle.vertex)
                yield (
                    AngleRatioProperty(angle0, angle1, 1, same=True),
                    Comment(
                        '$%{point:pt}$ lies on side $%{segment:side}$ of $%{angle:angle}$',
                        {'pt': angle.vertex, 'side': side, 'angle': angle0}
                    ),
                    [prop]
                )

@processed_cache(set())
class SameAngleDegreeRule2(Rule):
    def sources(self):
        return self.context.angle_value_properties_for_degree(180, lambda a: a.vertex)

    def apply(self, prop):
        angle = prop.angle
        side = angle.endpoints[0].segment(angle.endpoints[1])
        pattern = '$%{point:pt}$ lies on side $%{segment:side}$ of $%{angle:angle}$, $%{anglemeasure:known} = %{degree:degree}$'
        for pt in self.context.not_collinear_points(side):
            for pt0, pt1 in (angle.endpoints, reversed(angle.endpoints)):
                angle0 = pt0.angle(pt, pt1)
                angle1 = pt0.angle(pt, angle.vertex)
                key = (angle, pt, pt0, 0)
                if not key in self.processed:
                    value = self.context.angle_value_property(angle0)
                    if value:
                        self.processed.add(key)
                        yield (
                            AngleValueProperty(angle1, value.degree),
                            Comment(
                                pattern,
                                {'pt': angle.vertex, 'side': side, 'angle': angle0, 'known': angle0, 'degree': value.degree}
                            ),
                            [prop, value]
                        )
                key = (angle, pt, pt0, 1)
                if not key in self.processed:
                    value = self.context.angle_value_property(angle1)
                    if value:
                        self.processed.add(key)
                        yield (
                            AngleValueProperty(angle0, value.degree),
                            Comment(
                                pattern,
                                {'pt': angle.vertex, 'side': side, 'angle': angle0, 'known': angle1, 'degree': value.degree}
                            ),
                            [prop, value]
                        )

@processed_cache(set())
class SameAngleRule3(Rule):
    def sources(self):
        return self.context.angle_value_properties_for_degree(0, lambda a: a.vertex)

    def apply(self, prop):
        angle = prop.angle
        for pt in self.context.not_collinear_points(angle.vectors[0].as_segment):
            key = (angle, pt)
            if key in self.processed:
                continue
            self.processed.add(key)

            angles = [angle.vertex.angle(pt, endpoint) for endpoint in angle.endpoints]
            yield (
                AngleRatioProperty(*angles, 1, same=True),
                Comment(
                    '$%{point:pt}$ lies on side $%{ray:side}$ of $%{angle:angle}$',
                    {'pt': angle.endpoints[1], 'side': angle.vectors[0], 'angle': angles[0]}
                ),
                [prop]
            )

@processed_cache(set())
class SameAngleDegreeRule3(Rule):
    def sources(self):
        return self.context.angle_value_properties_for_degree(0, lambda a: a.vertex)

    def apply(self, prop):
        angle = prop.angle
        pattern = '$%{point:pt}$ lies on side $%{ray:side}$ of $%{angle:known}$, $%{anglemeasure:known} = %{degree:degree}$'
        for pt in self.context.not_collinear_points(angle.vectors[0].as_segment):
            angles = [angle.vertex.angle(pt, endpoint) for endpoint in angle.endpoints]

            key = (angle, pt, 0)
            if key not in self.processed:
                value = self.context.angle_value_property(angles[0])
                if value:
                    self.processed.add(key)
                    yield (
                        AngleValueProperty(angles[1], value.degree),
                        Comment(
                            pattern,
                            {'pt': angle.endpoints[1], 'side': angle.vectors[0], 'known': angles[0], 'degree': value.degree}
                        ),
                        [prop, value]
                    )
            key = (angle, pt, 1)
            if key not in self.processed:
                value = self.context.angle_value_property(angles[1])
                if value:
                    self.processed.add(key)
                    yield (
                        AngleValueProperty(angles[0], value.degree),
                        Comment(
                            pattern,
                            {'pt': angle.endpoints[0], 'side': angle.vectors[1], 'known': angles[1], 'degree': value.degree}
                        ),
                        [prop, value]
                    )

@processed_cache(set())
class ZeroAngleToSameSideRule(Rule):
    def sources(self):
        return self.context.angle_value_properties_for_degree(0, lambda a: a.vertex)

    def apply(self, prop):
        angle = prop.angle
        for pair in itertools.combinations(angle.point_set, 2):
            segment = pair[0].segment(pair[1])
            for pt in self.context.not_collinear_points(segment):
                key = (prop, segment, pt)
                if key in self.processed:
                    continue
                self.processed.add(key)
                ncl = self.context.collinearity_property(*pair, pt)
                yield (
                    SameOrOppositeSideProperty(angle.vertex.segment(pt), *angle.endpoints, True),
                    LazyComment('%s, %s', prop, ncl), #TODO: better comment
                    [prop, ncl]
                )

@processed_cache(set())
class Angle180ToSameOppositeSideRule(Rule):
    def sources(self):
        return self.context.angle_value_properties_for_degree(180, lambda a: a.vertex)

    def apply(self, prop):
        angle = prop.angle
        for pair in itertools.combinations(angle.point_set, 2):
            segment = pair[0].segment(pair[1])
            for pt in self.context.not_collinear_points(segment):
                key = (prop, segment, pt)
                if key in self.processed:
                    continue
                self.processed.add(key)
                ncl = self.context.collinearity_property(*pair, pt)
                yield (
                    SameOrOppositeSideProperty(angle.vertex.segment(pt), *angle.endpoints, False),
                    LazyComment('%s, %s', prop, ncl), #TODO: better comment
                    [prop, ncl]
                )
                yield (
                    SameOrOppositeSideProperty(angle.endpoints[0].segment(pt), *angle.vectors[1].points, True),
                    LazyComment('%s, %s', prop, ncl), #TODO: better comment
                    [prop, ncl]
                )
                yield (
                    SameOrOppositeSideProperty(angle.endpoints[1].segment(pt), *angle.vectors[0].points, True),
                    LazyComment('%s, %s', prop, ncl), #TODO: better comment
                    [prop, ncl]
                )

@source_type(SameOrOppositeSideProperty)
@processed_cache(set())
@accepts_auto
class PlanePositionsToLinePositionsRule(Rule):
    def apply(self, prop):
        pt0 = prop.points[0]
        pt1 = prop.points[1]
        segment = pt0.segment(pt1)
        crossing = self.context.intersection(prop.segment, segment)
        if not crossing:
            return
        crossing_prop = self.context.intersection_property(crossing, prop.segment, segment)
        self.processed.add(prop)
        if prop.same:
            pattern = '$%{point:crossing}$ is the intersection of lines $%{line:line0}$ and $%{line:line1}$'
            new_prop = AngleValueProperty(crossing.angle(pt0, pt1), 0)
        else:
            pattern = '$%{point:crossing}$ is the intersection of segment $%{segment:line0}$ and line $%{line:line1}$'
            new_prop = AngleValueProperty(crossing.angle(pt0, pt1), 180)
        yield (
            new_prop,
            Comment(pattern, {'crossing': crossing, 'line0': pt0.segment(pt1), 'line1': prop.segment}),
            [crossing_prop, prop]
        )

@source_type(PointInsideAngleProperty)
@processed_cache(set())
@accepts_auto
class TwoAnglesWithCommonSideRule(Rule):
    def apply(self, prop):
        av = self.context.angle_value_property(prop.angle)
        if av is None:
            return
        self.processed.add(prop)
        angle0 = prop.angle.vertex.angle(prop.angle.vectors[0].end, prop.point)
        angle1 = prop.angle.vertex.angle(prop.angle.vectors[1].end, prop.point)
        yield (
            SumOfAnglesProperty(angle0, angle1, degree=av.degree),
            Comment(
                '$%{anglemeasure:angle0} + %{anglemeasure:angle1} = %{anglemeasure:sum} = %{degree:degree}$',
                {'angle0': angle0, 'angle1': angle1, 'sum': prop.angle, 'degree': av.degree}
            ),
            [prop, av]
        )

@source_type(PointInsideAngleProperty)
@processed_cache({})
class TwoAnglesWithCommonSideDegreeRule(Rule):
    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0x7:
            return

        angle0 = prop.angle.vertex.angle(prop.angle.vectors[0].end, prop.point)
        angle1 = prop.angle.vertex.angle(prop.angle.vectors[1].end, prop.point)
        av0 = self.context.angle_value_property(angle0)
        av1 = self.context.angle_value_property(angle1)
        if av0 is None and av1 is None:
            return
        av_sum = self.context.angle_value_property(prop.angle)

        original = mask

        if (mask & 0x1) == 0 and av0 and av1:
            mask |= 0x1
            yield (
                AngleValueProperty(prop.angle, av0.degree + av1.degree),
                Comment(
                    '$%{anglemeasure:sum} = %{anglemeasure:angle0} + %{anglemeasure:angle1} = %{degree:degree0} + %{degree:degree1}$',
                    {'sum': prop.angle, 'angle0': angle0, 'angle1': angle1, 'degree0': av0.degree, 'degree1': av1.degree}
                ),
                [prop, av0, av1]
            )
        if (mask & 0x2) == 0 and av0 and av_sum:
            mask |= 0x2
            yield (
                AngleValueProperty(angle1, av_sum.degree - av0.degree),
                Comment(
                    '$%{anglemeasure:angle1} = %{anglemeasure:sum} - %{anglemeasure:angle0} = %{degree:degree_sum} - %{degree:degree0}$',
                    {'sum': prop.angle, 'angle0': angle0, 'angle1': angle1, 'degree0': av0.degree, 'degree_sum': av_sum.degree}
                ),
                [prop, av_sum, av0]
            )
        if (mask & 0x4) == 0 and av1 and av_sum:
            mask |= 0x4
            yield (
                AngleValueProperty(angle0, av_sum.degree - av1.degree),
                Comment(
                    '$%{anglemeasure:angle0} = %{anglemeasure:sum} - %{anglemeasure:angle1} = %{degree:degree_sum} - %{degree:degree1}$',
                    {'sum': prop.angle, 'angle0': angle0, 'angle1': angle1, 'degree1': av1.degree, 'degree_sum': av_sum.degree}
                ),
                [prop, av_sum, av1]
            )

        if mask != original:
            self.processed[prop] = mask

@source_type(SameOrOppositeSideProperty)
@processed_cache({})
class KnownAnglesWithCommonSideRule(Rule):
    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0x3:
            return
        original = mask

        for (sp0, sp1), bit in ((prop.segment.points, 0x1), (reversed(prop.segment.points), 0x2)):
            if mask & bit:
                continue
            pt0, pt1 = prop.points
            av0 = self.context.angle_value_property(sp0.angle(sp1, pt0))
            if av0 is None:
                continue
            av1 = self.context.angle_value_property(sp0.angle(sp1, pt1))
            if av1 is None:
                continue
            mask |= bit

            if av0.degree < av1.degree:
                pt0, pt1 = pt1, pt0
                av0, av1 = av1, av0
            params = {
                'angle0': av0.angle,
                'angle1': av1.angle,
                'degree0': av0.degree,
                'degree1': av1.degree,
                '180': 180,
                'pt0': pt0,
                'pt1': pt1,
                'line': prop.segment
            }
            if prop.same:
                if av0.degree == av1.degree:
                    comment = Comment(
                        '$%{anglemeasure:angle0} = %{degree:degree0} = %{anglemeasure:angle1}$, and points $%{point:pt0}$ and $%{point:pt1}$ are on the same side of $%{line:line}$',
                        params
                    )
                    yield (
                        PointsCollinearityProperty(sp0, pt0, pt1, True),
                        comment,
                        [av0, av1, prop]
                    )
                    yield (
                        AngleValueProperty(sp0.angle(pt0, pt1), 0),
                        comment,
                        [av0, av1, prop]
                    )
                    continue
                yield (
                    PointInsideAngleProperty(pt1, av0.angle),
                    Comment(
                        '$%{anglemeasure:angle0} = %{degree:degree0} > %{degree:degree1} = %{anglemeasure:angle1}$, and points $%{point:pt0}$ and $%{point:pt1}$ are on the same side of $%{line:line}$',
                        params
                    ),
                    [av1, av0, prop]
                )
                yield (
                    AngleValueProperty(sp0.angle(*prop.points), av0.degree - av1.degree),
                    Comment(
                        '$%{anglemeasure:angle0} = %{degree:degree0}$, $%{anglemeasure:angle1} = %{degree:degree1}$, and points $%{point:pt0}$ and $%{point:pt1}$ are on the same side of $%{line:line}$',
                        params
                    ),
                    [av0, av1, prop]
                )
            else:
                if av0.degree + av1.degree == 180:
                    comment = Comment(
                        '$%{anglemeasure:angle0} + %{anglemeasure:angle1} = %{degree:180}$, and points $%{point:pt0}$ and $%{point:pt1}$ are on opposite sides of $%{line:line}$',
                        params
                    )
                    yield (
                        PointsCollinearityProperty(sp0, *prop.points, True),
                        comment,
                        [av0, av1, prop]
                    )
                    yield (
                        AngleValueProperty(sp0.angle(*prop.points), 180),
                        comment,
                        [av0, av1, prop]
                    )
                    continue
                comment = Comment(
                    '$%{anglemeasure:angle0} = %{degree:degree0}$, $%{anglemeasure:angle1} = %{degree:degree1}$, and points $%{point:pt0}$ and $%{point:pt1}$ are on opposite sides of $%{line:line}$',
                    params
                )
                degree_sum = av0.degree + av1.degree
                if degree_sum < 180:
                    yield (
                        PointInsideAngleProperty(sp1, sp0.angle(pt0, pt1)),
                        Comment(
                            '$%{anglemeasure:angle0} + %{anglemeasure:angle1} = %{degree:degree0} + %{degree:degree1} < %{degree:180}$, and points $%{point:pt0}$ and $%{point:pt1}$ are on the same side of $%{line:line}$',
                            params
                        ),
                        [av1, av0, prop]
                    )
                if degree_sum > 180:
                    degree_sum = 360 - degree_sum
                yield (
                    AngleValueProperty(sp0.angle(*prop.points), degree_sum),
                    comment,
                    [av0, av1, prop]
                )

        if mask != original:
            self.processed[prop] = mask

@source_type(SameOrOppositeSideProperty)
@processed_cache({})
class OppositeSidesToInsideTriangleRule(Rule):
    def accepts(self, prop):
        return not prop.same

    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0xF:
            return

        original = mask
        index = 0
        for (centre, pt1) in (prop.segment.points, reversed(prop.segment.points)):
            for (pt0, pt2) in (prop.points, reversed(prop.points)):
                index += 1
                bit = 1 << index
                if mask & bit:
                    continue
                prop1 = self.context.two_points_relative_to_line_property(centre.segment(pt0), pt1, pt2)
                if prop1 is None:
                    continue
                mask |= bit
                if prop1.same:
                    continue
                triangle = Scene.Triangle(pt0, pt1, pt2)
                comment = Comment(
                    'line $%{line:line0}$ separates $%{point:pt0}$ and $%{point:pt1}$, line $%{line:line1}$ separates $%{point:pt2}$ and $%{point:pt3}$',
                    {
                        'line0': prop.segment,
                        'pt0': prop.points[0],
                        'pt1': prop.points[1],
                        'line1': prop1.segment,
                        'pt2': prop1.points[0],
                        'pt3': prop1.points[1]
                    }
                )
                yield (
                    PointInsideTriangleProperty(centre, triangle),
                    comment,
                    [prop, prop1]
                )
        if mask != original:
            self.processed[prop] = mask

@processed_cache(set())
class TwoPointsRelativeToLineTransitivityRule(Rule):
    def sources(self):
        for p0 in self.context.list(SameOrOppositeSideProperty):
            for p1 in self.context.list(SameOrOppositeSideProperty, [p0.segment]):
                if p0 != p1:
                    yield (p0, p1)

    def apply(self, src):
        key = frozenset(src)
        if key in self.processed:
            return
        self.processed.add(key)

        sos0, sos1 = src
        if sos0.points[0] in sos1.points:
            common = sos0.points[0]
            other0 = sos0.points[1]
        elif sos0.points[1] in sos1.points:
            common = sos0.points[1]
            other0 = sos0.points[0]
        else:
            return
        other1 = sos1.points[0] if sos1.points[1] == common else sos1.points[1]
        if sos0.same and sos1.same:
            pattern = '$%{point:other0}$, $%{point:common}$, and $%{point:other1}$ lie on the same side of $%{line:line}$'
            pts = (other0, other1)
            premises = [sos0, sos1]
        elif sos0.same:
            pattern = '$%{point:other0}$ and $%{point:common}$ lie on the same side of $%{line:line}$, $%{point:other1}$ is on the opposite side'
            pts = (other0, other1)
            premises = [sos0, sos1]
        elif sos1.same:
            pattern = '$%{point:other1}$ and $%{point:common}$ lie on the same side of $%{line:line}$, $%{point:other0}$ is on the opposite side'
            pts = (other1, other0)
            premises = [sos1, sos0]
        else:
            pattern = '$%{point:other0}$ and $%{point:common}$ lie on opposite sides of $%{line:line}$, and $%{point:common}$ and $%{point:other1}$ too'
            pts = (other0, other1)
            premises = [sos0, sos1]

        yield (
            SameOrOppositeSideProperty(sos0.segment, *pts, sos0.same == sos1.same),
            Comment(
                pattern,
                {'other0': other0, 'other1': other1, 'common': common, 'line': sos0.segment}
            ),
            premises
        )

@source_type(SameOrOppositeSideProperty)
@processed_cache(set())
class TwoPointsRelativeToLineTransitivityRule2(Rule):
    def apply(self, prop):
        for other in self.context.collinear_points(prop.segment):
            colli = None
            for pt in prop.segment.points:
                key = (prop, other, pt)
                if key in self.processed:
                    continue
                ne = self.context.coincidence_property(other, pt)
                if ne is None:
                    continue
                self.processed.add(key)
                if ne.coincident:
                    continue
                if colli is None:
                    colli = self.context.collinearity_property(other, *prop.segment.points)
                yield (
                    SameOrOppositeSideProperty(other.segment(pt), *prop.points, prop.same),
                    Comment(
                        '$%{line:line0}$ is the same line as $%{line:line1}$',
                        {'line0': other.segment(pt), 'line1': prop.segment}
                    ),
                    [colli, ne, prop]
                )

@processed_cache(set())
class CongruentAnglesDegeneracyRule(Rule):
    def sources(self):
        return self.context.congruent_angles_with_vertex()

    def apply(self, src):
        ca = None
        for key in (src, (src[1], src[0])):
            if key in self.processed:
                continue
            ang0, ang1 = key
            collinearity = self.context.collinearity(*ang0.point_set)
            if collinearity is None:
                continue
            self.processed.add(key)

            col = self.context.collinearity_property(*ang0.point_set)
            if ca is None:
                ca = self.context.angle_ratio_property(ang0, ang1)
            if col.collinear:
                pattern = '$%{angle:angle1}$ and $%{angle:angle0}$ are congruent, $%{angle:angle0}$ is degenerate'
            else:
                pattern = '$%{angle:angle1}$ and $%{angle:angle0}$ are congruent, $%{angle:angle0}$ is non-degenerate'
            comment = Comment(pattern, {'angle0': ang0, 'angle1': ang1})
            yield (
                PointsCollinearityProperty(*ang1.point_set, col.collinear),
                comment,
                [ca, col]
            )

@processed_cache(set())
class CongruentAnglesKindRule(Rule):
    def sources(self):
        return self.context.congruent_angles_with_vertex()

    def apply(self, src):
        ca = None
        for key in (src, (src[1], src[0])):
            if key in self.processed:
                continue
            ang0, ang1 = key
            kind = self.context.angle_kind_property(ang0)
            if kind is None:
                continue
            self.processed.add(key)
            if ca is None:
                ca = self.context.angle_ratio_property(ang0, ang1)
            if kind.kind == AngleKindProperty.Kind.acute:
                pattern = '$%{angle:angle1}$ and $%{angle:angle0}$ are congruent, $%{angle:angle0}$ is acute'
            elif kind.kind == AngleKindProperty.Kind.obtuse:
                pattern = '$%{angle:angle1}$ and $%{angle:angle0}$ are congruent, $%{angle:angle0}$ is obtuse'
            else:
                pattern = '$%{angle:angle1}$ and $%{angle:angle0}$ are congruent, $%{angle:angle0}$ is right'
            comment = Comment(pattern, {'angle0': ang0, 'angle1': ang1})
            yield (
                AngleKindProperty(ang1, kind.kind),
                comment,
                [ca, kind]
            )

@source_type(SameOrOppositeSideProperty)
@processed_cache({})
class PointAndAngleRule(Rule):
    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0x0F:
            return
        original = mask
        for vertex, bit0 in zip(prop.segment.points, (0x1, 0x4)):
            pt0 = other_point(prop.segment.points, vertex)
            for pt1, bit in zip(prop.points, (bit0, bit0 << 1)):
                if mask & bit:
                    continue
                fourth = other_point(prop.points, pt1)
                prop1 = self.context.two_points_relative_to_line_property(
                    vertex.segment(pt1), pt0, fourth
                )
                if prop1 is None:
                    continue
                mask |= bit
                # TODO: update self.processed[prop1]
                if not prop.same and not prop1.same:
                    continue

                params = {
                    'pt0': pt0,
                    'pt1': pt1,
                    'fourth': fourth,
                    'side0': vertex.vector(pt0),
                    'side1': vertex.vector(pt1)
                }
                if prop.same and prop1.same:
                    yield (
                        PointInsideAngleProperty(fourth, vertex.angle(pt0, pt1)),
                        Comment(
                            '$%{point:fourth}$ lies on the same side of $%{ray:side0}$ as $%{point:pt1}$ and on the same side of $%{ray:side1}$ as $%{point:pt0}$',
                            params
                        ),
                        [prop, prop1]
                    )
                elif prop.same:
                    yield (
                        PointInsideAngleProperty(pt1, vertex.angle(pt0, fourth)),
                        Comment(
                            '$%{point:pt1}$ lies on the same side of $%{ray:side0}$ as $%{point:fourth}$ and $%{ray:side1}$ separates $%{point:pt0}$ and $%{point:fourth}$',
                            params
                        ),
                        [prop, prop1]
                    )
                else:
                    yield (
                        PointInsideAngleProperty(pt0, vertex.angle(fourth, pt1)),
                        Comment(
                            '$%{point:pt0}$ lies on the same side of $%{ray:side1}$ as $%{point:fourth}$ and $%{ray:side0}$ separates $%{point:pt1}$ and $%{point:fourth}$',
                            params
                        ),
                        [prop1, prop]
                    )

        if mask != original:
            self.processed[prop] = mask

@source_type(AngleKindProperty)
@processed_cache(set())
class PerpendicularToSideOfObtuseAngleRule(Rule):
    def accepts(self, prop):
        return prop.angle.vertex and prop.kind == AngleKindProperty.Kind.obtuse

    def apply(self, prop):
        for vec0, vec1 in (prop.angle.vectors, reversed(prop.angle.vectors)):
            for perp in self.context.list(PerpendicularSegmentsProperty, [vec0.as_segment]):
                other = next(seg for seg in perp.segments if seg != vec0.as_segment)
                if vec0.end not in other.points or self.context.line_for_segment(other) is None:
                    continue
                key = (prop.angle, other)
                if key in self.processed:
                    continue
                self.processed.add(key)
                ne = self.context.coincidence_property(*other.points)
                yield (
                    SameOrOppositeSideProperty(other, *vec1.points, True),
                    Comment(
                        '$%{line:perp} \\perp %{segment:side}$ and $%{angle:obtuse}$ is obtuse',
                        {'perp': other, 'side': vec0, 'obtuse': prop.angle}
                    ),
                    [perp, prop, ne]
                )

@source_type(MiddleOfSegmentProperty)
@processed_cache({})
class MiddleOfSegmentRule(Rule):
    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0xF:
            return
        original = mask

        comment = Comment(
            '$%{point:point}$ is the midpoint of $%{segment:segment}$',
            {'point': prop.point, 'segment': prop.segment}
        )

        triangle = Scene.Triangle(prop.point, *prop.segment.points)
        if (mask & 0x1) == 0:
            # properties not depending on degeneracy
            mask |= 0x1
            new_properties = (
                PointsCollinearityProperty(*triangle.points, True),
                ProportionalLengthsProperty(triangle.sides[0], triangle.sides[1], 2),
                ProportionalLengthsProperty(triangle.sides[0], triangle.sides[2], 2),
                ProportionalLengthsProperty(triangle.sides[1], triangle.sides[2], 1),
            )
            for p in new_properties:
                yield (p, comment, [prop])

        for index, seg in enumerate(triangle.sides):
            bit = 2 << index
            if mask & bit:
                continue
            ne = self.context.coincidence_property(*seg.points)
            if ne is None:
                continue
            mask |= bit
            if ne.coincident:
                mask |= 0xE
                break

            new_properties = [
                AngleValueProperty(triangle.angles[0], 180),
                AngleValueProperty(triangle.angles[1], 0),
                AngleValueProperty(triangle.angles[2], 0),
            ]
            for side in triangle.sides:
                if side != seg:
                    new_properties.append(PointsCoincidenceProperty(*side.points, False))
            for p in new_properties:
                yield (p, comment, [prop, ne])

        if mask != original:
            self.processed[prop] = mask

@processed_cache(set())
class PointOnSegmentWithEndpointsOnSidesOfAngleRule(Rule):
    def sources(self):
        return self.context.angle_value_properties_for_degree(180, lambda a: a.vertex)

    def apply(self, prop):
        segment = prop.angle.endpoints[0].segment(prop.angle.endpoints[1])
        for vertex in self.context.not_collinear_points(segment):
            key = (prop, vertex)
            if key in self.processed:
                continue
            self.processed.add(key)

            ncl = self.context.collinearity_property(vertex, *segment.points)
            angle = vertex.angle(*prop.angle.endpoints)
            yield (
                PointInsideAngleProperty(prop.angle.vertex, angle),
                Comment(
                    '$%{point:vertex}$ lies on a segment with endpoints on sides of $%{angle:angle}$',
                    {'vertex': prop.angle.vertex, 'angle': angle}
                ),
                [prop, ncl]
            )
            yield (
                SameOrOppositeSideProperty(prop.angle.vertex.segment(vertex), *prop.angle.endpoints, False),
                Comment(
                    '$%{point:pt_on}$ lies on segment $%{segment:segment}$, and $%{point:pt_not_on}$ is not on the line $%{line:segment}$',
                    {'pt_on': prop.angle.vertex, 'pt_not_on': vertex, 'segment': segment}
                ),
                [prop, ncl]
            )
