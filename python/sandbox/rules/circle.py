import itertools

from sandbox.property import *
from sandbox.util import LazyComment

from .abstract import Rule, SingleSourceRule

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

class TwoChordsIntersectionRule(Rule):
    def sources(self):
        return self.context.n_concyclic_points(4)

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

class InscribedAnglesWithCommonCircularArcRule(Rule):
    def sources(self):
        return self.context.n_concyclic_points(4)

    def apply(self, points):
        # TODO: implement duplicate protection
        for inds0, inds1 in [((0, 1), (2, 3)), ((0, 2), (1, 3)), ((0, 3), (1, 2))]:
            pair0 = [points[i] for i in inds0]
            pair1 = [points[i] for i in inds1]
            for p0, p1 in ((pair0, pair1), (pair1, pair0)):
                sos = self.context.two_points_and_line_configuration_property(
                    p0[0].segment(p0[1]), *p1
                )
                if sos is None:
                    continue
                ang0 = p0[0].angle(*p1)
                ang1 = p0[1].angle(*p1)
                if sos.same:
                    yield (
                        AngleRatioProperty(ang0, ang1, 1),
                        LazyComment('%s and %s are inscribed and subtend the same arc', ang0, ang1),
                        # TODO: add concyclic points reasons
                        [sos]
                    )
                else:
                    # TODO: sum = 180 degree
                    pass
                ang0 = p1[0].angle(*p0)
                ang1 = p1[1].angle(*p0)
                if sos.same:
                    yield (
                        AngleRatioProperty(ang0, ang1, 1),
                        LazyComment('%s and %s are inscribed and subtend the same arc', ang0, ang1),
                        # TODO: add concyclic points reasons
                        [sos]
                    )
                else:
                    # TODO: sum = 180 degree
                    pass
