import itertools

from sandbox.property import *
from sandbox.util import LazyComment

from .abstract import Rule, SingleSourceRule

class CyclicQuadrilateralRule(Rule):
    def __init__(self, context):
        super().__init__(context)
        self.processed = set()

    def sources(self):
        right_angles = [prop for prop in self.context.angle_value_properties_for_degree(90) if prop.angle.vertex]
        return itertools.combinations(right_angles, 2)

    def apply(self, src):
        key = frozenset(src)
        if key in self.processed:
            return

        av0, av1 = src
        endpoints = av0.angle.endpoints
        if set(endpoints) != set(av1.angle.endpoints):
            self.processed.add(key)
            return

        oppo0 = self.context.two_points_relatively_to_line_property(endpoints[0].segment(endpoints[1]), av0.angle.vertex, av1.angle.vertex)
        oppo1 = self.context.two_points_relatively_to_line_property(av0.angle.vertex.segment(av1.angle.vertex), *endpoints)
        if oppo0 is None and oppo1 is None:
            return
        self.processed.add(key)
        for oppo in filter(None, (oppo0, oppo1)):
            if oppo.same:
                return
            yield (
                ConcyclicPointsProperty(av0.angle.vertex, av1.angle.vertex, *endpoints),
                LazyComment('convex quadrilateral %s with two right angles %s and %s is cyclic', Scene.Polygon(av0.angle.vertex, endpoints[0], av1.angle.vertex, endpoints[1]), av0.angle, av1.angle),
                [av0, av1, oppo]
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
        self.processed = set()

    def accepts(self, prop):
        return prop not in self.processed

    def apply(self, prop):
        for triple in itertools.combinations(prop.points, 3):
            ncl = self.context.collinearity_property(*triple)
            if ncl:
                # TODO: better way to report contadiction
                assert not ncl.collinear
                break
        else:
            return

        self.processed.add(prop)
        for pt in [pt for pt in prop.points if pt not in triple]:
            yield (
                PointAndCircleProperty(pt, *triple, PointAndCircleProperty.Kind.on),
                LazyComment('%s, %s, %s, and %s are concyclic', pt, *triple),
                [prop, ncl]
            )

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
    def sources(self):
        return [triple[0] for triple in self.context.n_concyclic_points(4)]

    def apply(self, points):
        # TODO: implement duplicate protection
        for inds0, inds1 in [((0, 1), (2, 3)), ((0, 2), (1, 3)), ((0, 3), (1, 2))]:
            pair0 = [points[i] for i in inds0]
            pair1 = [points[i] for i in inds1]
            segment0 = pair0[0].segment(pair0[1])
            segment1 = pair1[0].segment(pair1[1])
            crossing, premises = self.context.intersection_of_lines(segment0, segment1)
            if crossing is None:
                continue
            if crossing in pair0 or crossing in pair1:
                continue
            angle0 = crossing.angle(*pair0)
            angle1 = crossing.angle(*pair1)
            av0 = self.context.angle_value_property(angle0)
            av1 = self.context.angle_value_property(angle1)
            for av, angle in ((av0, angle1), (av1, angle0)):
                if av is None:
                    continue
                if av.degree == 0:
                    # TODO: circle name
                    comment = LazyComment('%s lies outside of circle XXX', crossing),
                elif av.degree == 180:
                    # TODO: circle name
                    comment = LazyComment('%s lies inside circle XXX', crossing),
                else:
                    assert False, 'Contradiction'
                yield (
                    AngleValueProperty(angle, av.degree),
                    comment,
                    # TODO: concyclic property
                    premises
                )

class PointsOnChordRule(Rule):
    def sources(self):
        return self.context.n_concyclic_points(2)

    def apply(self, triple):
        points, circle, premises = triple
        for pt, _ in self.context.collinear_points_with_properties(*points):
            av = self.context.angle_value_property(pt.angle(*points))
            pc = self.context.point_and_circle_property(pt, circle.main_key)
            if av:
                if av.degree == 0:
                    location = PointAndCircleProperty.Kind.outside
                    comment = LazyComment('%s lies on line %s', pt, points[0].segment(points[1]).as_line)
                elif av.degree == 180:
                    location = PointAndCircleProperty.Kind.inside
                    comment = LazyComment('%s lies on chord %s', pt, points[0].segment(points[1]))
                else:
                    assert False, 'Contradiction'
                yield (
                    PointAndCircleProperty(pt, *circle.main_key, location),
                    comment,
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
    def sources(self):
        return [triple[0] for triple in self.context.n_concyclic_points(4)]

    def apply(self, points):
        # TODO: implement duplicate protection
        for inds0, inds1 in [((0, 1), (2, 3)), ((0, 2), (1, 3)), ((0, 3), (1, 2))]:
            pair0 = [points[i] for i in inds0]
            pair1 = [points[i] for i in inds1]
            for p0, p1 in ((pair0, pair1), (pair1, pair0)):
                sos = self.context.two_points_relatively_to_line_property(
                    p0[0].segment(p0[1]), *p1
                )
                if sos is None:
                    continue
                for pp0, pp1 in ((p0, p1), (p1, p0)):
                    ang0 = pp0[0].angle(*pp1)
                    ang1 = pp0[1].angle(*pp1)
                    if sos.same:
                        yield (
                            AngleRatioProperty(ang0, ang1, 1),
                            LazyComment('%s and %s are inscribed and subtend the same arc', ang0, ang1),
                            # TODO: add concyclic points reasons
                            [sos]
                        )
                    else:
                        yield (
                            SumOfTwoAnglesProperty(ang0, ang1, 180),
                            LazyComment('%s and %s are inscribed and subtend complementary arcs', ang0, ang1),
                            # TODO: add concyclic points reasons
                            [sos]
                        )
