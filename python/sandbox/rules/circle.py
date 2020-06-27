import itertools

from ..figure import Circle
from ..property import *
from ..util import LazyComment, Comment

from .abstract import Rule, SingleSourceRule

class CyclicQuadrilateralRule(Rule):
    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def sources(self):
        right_angles = [prop for prop in self.context.list(PerpendicularSegmentsProperty) if len(set((*prop.segments[0].points, *prop.segments[1].points))) == 3]
        return itertools.combinations(right_angles, 2)

    def apply(self, src):
        key = frozenset(src)
        if key in self.processed:
            return

        perp0, perp1 = src
        vertex0 = next(pt for pt in perp0.segments[0].points if pt in perp0.segments[1].points)
        vertex1 = next(pt for pt in perp1.segments[0].points if pt in perp1.segments[1].points)
        if vertex0 == vertex1:
            self.processed.add(key)
            return

        pts0 = [
            next(pt for pt in perp0.segments[0].points if pt != vertex0),
            next(pt for pt in perp0.segments[1].points if pt != vertex0)
        ]
        pts1 = [
            next(pt for pt in perp1.segments[0].points if pt != vertex1),
            next(pt for pt in perp1.segments[1].points if pt != vertex1)
        ]
        if set(pts0) != set(pts1):
            self.processed.add(key)
            return

        points = [vertex0, vertex1, *pts0]
        for pt0, pt1 in itertools.combinations(points, 2):
            ne = self.context.coincidence_property(pt0, pt1)
            if ne is not None:
                # TODO: select best candidate instead
                break
        if ne is None:
            return
        self.processed.add(key)
        if ne.coincident:
            return

        yield (
            ConcyclicPointsProperty(*points),
            Comment(
                'quadrilateral $%{polygon:quad}$ with two right angles $%{angle:right0}$ and $%{angle:right1}$ is cyclic',
                {
                    'quad': Scene.Polygon(vertex0, pts0[0], vertex1, pts0[1]),
                    'right0': vertex0.angle(*pts0),
                    'right1': vertex1.angle(*pts1)
                }
            ),
            [perp0, perp1, ne]
        )

class CyclicQuadrilateralRule2(SingleSourceRule):
    property_type = SameOrOppositeSideProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def accepts(self, prop):
        return not prop.same and prop not in self.processed

    def apply(self, prop):
        angle0 = prop.points[0].angle(*prop.segment.points)
        angle1 = prop.points[1].angle(*prop.segment.points)
        sum_degree = self.context.sum_of_two_angles(angle0, angle1)
        if sum_degree is None:
            return
        self.processed.add(prop)
        if sum_degree != 180:
            return
        sum_prop = self.context.sum_of_two_angles_property(angle0, angle1)

        points = (prop.points[0], prop.segment.points[0], prop.points[1], prop.segment.points[1])
        yield (
            ConcyclicPointsProperty(*points),
            Comment(
                'quadrilateral $%{polygon:quad}$ with sum of opposite angles $%{anglemeasure:angle0} + %{anglemeasure:angle1} = %{degree:180}$ is cyclic',
                {
                    'quad': Scene.Polygon(*points),
                    'angle0': angle0,
                    'angle1': angle1,
                    '180': 180
                }
            ),
            [sum_prop, prop]
        )

class ThreeNonCoincidentPointsOnACicrleAreNonCollinearRule(SingleSourceRule):
    property_type = ConcyclicPointsProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = {}

    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0xF:
            return

        pair_to_ne = {}
        def ne(pair):
            cached = pair_to_ne.get(pair)
            if cached is not None:
                return cached
            prop = self.context.coincidence_property(*pair)
            if not prop:
                prop = False
            pair_to_ne[pair] = prop
            return prop

        original = mask
        for index, pt in enumerate(prop.points):
            bit = 1 << index
            if mask & bit:
                continue
            circle = [p for p in prop.points if p != pt]
            premises = [prop]
            for pair in itertools.combinations(circle, 2):
                neq = ne(pair)
                if neq == False or neq.coincident:
                    break
                premises.append(neq)
            if len(premises) < 4:
                if neq != False:
                    mask |= bit
                continue
            mask |= bit
            yield (
                PointsCollinearityProperty(*circle, False),
                LazyComment('three non-coincident points on a circle'),
                premises
            )
        if mask != original:
            self.processed[prop] = mask

class PointsOnCircleRule(SingleSourceRule):
    property_type = ConcyclicPointsProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = {}

    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0xF:
            return

        original = mask
        for triple, bit in zip(itertools.combinations(prop.points, 3), (1, 2, 4, 8)):
            if mask & bit:
                continue
            ncl = self.context.collinearity_property(*triple)
            if ncl is None:
                continue
            mask |= bit
            if ncl.collinear:
                continue
            pt = next(pt for pt in prop.points if pt not in triple)
            yield (
                PointAndCircleProperty(pt, *triple, PointAndCircleProperty.Kind.on),
                LazyComment('%s, %s, %s, and %s are concyclic', pt, *triple),
                [prop, ncl]
            )
        if mask != original:
            self.processed[prop] = mask

class ConcyclicToSameCircleRule(SingleSourceRule):
    property_type = ConcyclicPointsProperty

    def __init__(self, context):
        super().__init__(context)
        self.processed = {}

    def apply(self, prop):
        mask = self.processed.get(prop, 0)
        if mask == 0x3F:
            return

        original = mask
        for pair, bit in zip(itertools.combinations(prop.points, 2), (1, 2, 4, 8, 16, 32)):
            if mask & bit:
                continue
            others = [pt for pt in prop.points if pt not in pair]
            triple0 = (*pair, others[0])
            ncl0 = self.context.collinearity_property(*triple0)
            if ncl0 is None:
                continue
            if ncl0.collinear:
                mask |= bit
                continue
            triple1 = (*pair, others[1])
            ncl1 = self.context.collinearity_property(*triple1)
            if ncl1 is None:
                continue
            mask |= bit
            if ncl1.collinear:
                continue
            yield (
                CircleCoincidenceProperty(triple0, triple1, True),
                LazyComment('%s, %s, %s, and %s are concyclic', *pair, *others),
                [prop, ncl0, ncl1]
            )
        if mask != original:
            self.processed[prop] = mask

class ThreeCollinearPointsOnCircleRule(Rule):
    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def sources(self):
        return [triple[0] for triple in self.context.n_concyclic_points(3)]

    def apply(self, points):
        key = frozenset(points)
        if key in self.processed:
            return
        col = self.context.collinearity_property(*points)
        if col is None:
            return
        if not col.collinear:
            self.processed.add(key)
            return
        pairs = list(itertools.combinations(points, 2))
        neq = [self.context.coincidence_property(*pair) for pair in pairs]
        for ne0, ne1, pair in ((neq[0], neq[1], pairs[2]), (neq[0], neq[2], pairs[1]), (neq[1], neq[2], pairs[0])):
            if ne0 and ne1 and not ne0.coincident and not ne1.coincident:
                self.processed.add(key)
                yield (
                    PointsCoincidenceProperty(*points[:2], True),
                    # TODO: circle name
                    LazyComment('%s, %s, and %s are collinear points that lie on circle XXX', *points),
                    # concyclic points
                    [col, ne0, ne1]
                )

class TwoChordsIntersectionRule(Rule):
    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def sources(self):
        for circle in self.context.circles:
            for four in itertools.combinations(circle.points_on, 4):
                yield four

    def apply(self, points):
        prop = None
        for pt0, pt1 in itertools.combinations(points, 2):
            pt2, pt3 = [pt for pt in points if pt not in (pt0, pt1)]
            chord0 = pt0.segment(pt1)
            chord1 = pt2.segment(pt3)
            key = frozenset([chord0, chord1])
            if key in self.processed:
                return
            crossing, premises = self.context.intersection_of_lines(chord0, chord1)
            if crossing is None:
                continue
            if crossing in points:
                self.processed.add(key)
                continue
            av = self.context.angle_value_property(crossing.angle(pt0, pt1))
            if av is None:
                continue
            self.processed.add(key)

            circle = Circle(*points)
            if av.degree == 0:
                pattern = '$%{segment:chord1}$ and $%{segment:chord0}$ are chords of $%{circle:circle}$, $%{point:crossing}$ is the intersection of lines $%{line:chord1}$ and $%{line:chord0}$, and lies outside of the chord $%{segment:chord0}$'
            elif av.degree == 180:
                pattern = '$%{point:crossing}$ is the intersection of chords $%{segment:chord1}$ and $%{segment:chord0}$ of $%{circle:circle}$, and lies inside $%{segment:chord0}$'
            else:
                assert False, 'Contradiction'
            if prop is None:
                prop = self.context.concyclicity_property(*points)
            yield (
                AngleValueProperty(crossing.angle(pt2, pt3), av.degree),
                Comment(
                    pattern,
                    {'crossing': crossing, 'chord0': chord0, 'chord1': chord1, 'circle': circle}
                ),
                [prop, av] + premises
            )

class PointsOnChordRule(Rule):
    def sources(self):
        return self.context.n_concyclic_points(2)

    def apply(self, triple):
        points, circle, premises = triple
        for pt in self.context.collinear_points(points[0].segment(points[1])):
            av = self.context.angle_value_property(pt.angle(*points))
            pc = self.context.point_and_circle_property(pt, circle.main_key)
            if av:
                if av.degree == 0:
                    location = PointAndCircleProperty.Kind.outside
                    pattern = '$%{point:pt}$ lies on the line $%{line:chord}$'
                elif av.degree == 180:
                    location = PointAndCircleProperty.Kind.inside
                    pattern = '$%{point:pt}$ lies on the chord $%{segment:chord}$'
                else:
                    assert False, 'Contradiction'
                yield (
                    PointAndCircleProperty(pt, *circle.main_key, location),
                    Comment(pattern, {'pt': pt, 'chord': points[0].segment(points[1])})
                    [av] + premises
                )
            if pc:
                if pc.location == PointAndCircleProperty.Kind.inside:
                    degree = 180
                elif pc.location == PointAndCircleProperty.Kind.inside:
                    degree = 0
                else:
                    continue
                yield (
                    AngleValueProperty(pt.angle(*points), degree),
                    LazyComment('temp comment'),
                    [pc] + premises
                )

class InscribedAnglesWithCommonCircularArcRule(Rule):
    def __init__(self, context):
        super().__init__(context)
        self.processed = {}

    def sources(self):
        for circle in self.context.circles:
            for four in itertools.combinations(circle.points_on, 4):
                yield four

    def apply(self, points):
        prop = None

        for pt0, pt1 in itertools.combinations(points, 2):
            pt2, pt3 = [pt for pt in points if pt not in (pt0, pt1)]
            sos = self.context.two_points_relatively_to_line_property(
                pt0.segment(pt1), pt2, pt3
            )
            if sos is None:
                continue
            if prop is None:
                prop = self.context.concyclicity_property(*points)
            p0 = (pt0, pt1)
            p1 = (pt2, pt3)
            for pp0, pp1 in ((p0, p1), (p1, p0)):
                ang0 = pp0[0].angle(*pp1)
                ang1 = pp0[1].angle(*pp1)
                circle = Circle(*ang0.point_set)
                if sos.same:
                    pattern = '$%{angle:angle0}$ and $%{angle:angle1}$ are inscribed in $%{circle:circle}$ and subtend the same arc'
                    new_prop = AngleRatioProperty(ang0, ang1, 1)
                else:
                    pattern = '$%{angle:angle0}$ and $%{angle:angle1}$ are inscribed in $%{circle:circle}$ and subtend complementary arcs'
                    new_prop = SumOfTwoAnglesProperty(ang0, ang1, 180)
                yield (
                    new_prop,
                    Comment(pattern, {'angle0': ang0, 'angle1': ang1, 'circle': circle}),
                    [prop, sos]
                )
