import itertools
import time
import sympy as sp

from .core import Constraint
from .predefined import enumerate_predefined_properties
from .property import *
from .propertyset import PropertySet
from .reason import Reason
from .rules.advanced import *
from .rules.basic import *
from .rules.circle import *
from .rules.linear import *
from .rules.triangle_elements import *
from .rules.triangles import *
from .rules.trigonometric import *
from .scene import Scene
from .stats import Stats
from .util import LazyComment

class Explainer:
    def __init__(self, scene, options={}):
        self.scene = scene
        self.context = PropertySet()
        self.__options = options
        self.__explanation_time = None
        self.__iteration_step_count = -1
        self.__rules = [
            #ThreeNonCoincidentPointsOnACicrleAreNonCollinearRule(self.context),
            PointsOnCircleRule(self.context),
            InscribedAnglesWithCommonCircularArcRule(self.context),
            TwoChordsIntersectionRule(self.context),
            LengthRatioTransitivityRule(self.context),
            ProportionalLengthsToLengthsRatioRule(self.context),
            LengthRatiosWithCommonDenominatorRule(self.context),
            SumOfThreeAnglesInTriangleRule(self.context),
            SumOfTwoAnglesByThreeRule(self.context),
            SumAndRatioOfTwoAnglesRule(self.context),
            #EqualSumsOfAnglesRule(self.context),
            AngleFromSumOfTwoAnglesRule(self.context),
            SumOfAngles180DegreeRule(self.context),
            NonCollinearPointsAreDifferentRule(self.context),
            CoincidenceTransitivityRule(self.context),
            CollinearityCollisionRule(self.context),
            TwoPointsBelongsToTwoLinesRule(self.context),
            TwoPointsBelongsToTwoPerpendicularsRule(self.context),
            LengthRatioRule(self.context),
            ParallelVectorsRule(self.context),
            PerpendicularSegmentsRule(self.context),
            Degree90ToPerpendicularSegmentsRule(self.context),
            PerpendicularTransitivityRule(self.context),
            PerpendicularToEquidistantRule(self.context),
            EquidistantToPerpendicularRule(self.context),
            PointsSeparatedByLineAreNotCoincidentRule(self.context),
            SameSidePointInsideSegmentRule(self.context),
            TwoPerpendicularsRule(self.context),
            TwoPerpendicularsRule2(self.context),
            ParallelSameSideRule(self.context),
            CommonPerpendicularRule(self.context),
            SideProductsInSimilarTrianglesRule(self.context),
            CorrespondingAnglesInCongruentTrianglesRule(self.context),
            CorrespondingAnglesInSimilarTrianglesRule(self.context),
            CorrespondingSidesInCongruentTrianglesRule(self.context),
            CorrespondingSidesInSimilarTrianglesRule(self.context),
            LengthProductEqualityToRatioRule(self.context),
            EquilateralTriangleAnglesRule(self.context),
            EquilateralTriangleSidesRule(self.context),
            BaseAnglesOfIsoscelesRule(self.context),
            LegsOfIsoscelesRule(self.context),
            RotatedAngleRule(self.context),
            AngleTypeByDegreeRule(self.context),
            PointsCollinearityByAngleDegreeRule(self.context),
            RightAngleDegreeRule(self.context),
            AngleTypesInObtuseangledTriangleRule(self.context),
            PartOfAcuteAngleIsAcuteRule(self.context),
            SameAngleRule(self.context),
            SameAngleRule2(self.context),
            SupplementaryAnglesRule(self.context),
            VerticalAnglesRule(self.context),
            CorrespondingAndAlternateAnglesRule(self.context),
            CyclicOrderRule(self.context),
            PlanePositionsToLinePositionsRule(self.context),
            CeviansIntersectionRule(self.context),
            SameSideToInsideAngleRule(self.context),
            TwoAnglesWithCommonSideRule(self.context),

            EquilateralTriangleByThreeSidesRule(self.context),
            IsoscelesTriangleByConrguentLegsRule(self.context),
            IsoscelesTriangleByConrguentBaseAnglesRule(self.context),
            CongruentTrianglesByAngleAndTwoSidesRule(self.context),
            CongruentTrianglesByThreeSidesRule(self.context),
            SimilarTrianglesByTwoAnglesRule(self.context),
            SimilarTrianglesByAngleAndTwoSidesRule(self.context),
            SimilarTrianglesByThreeSidesRule(self.context),
            SimilarTrianglesWithCongruentSideRule(self.context),
        ]
        if options.get('advanced'):
            self.__rules += [
                RightAngledTriangleMedianRule(self.context),
                Triangle30_60_90SidesRule(self.context),
                Triangle30_30_120SidesRule(self.context),
            ]
        if options.get('trigonometric'):
            self.__rules += [
                LawOfSinesRule(self.context),
            ]

    def __reason(self, prop, comment, premises=None):
        reason = Reason(self.__iteration_step_count, comment, premises)
        if prop in reason.all_premises:
            return
        def insert(pro):
            for pre in pro.reason.premises:
                pre.implications.add(pro)
                if self.context.index_of(pre) is None:
                    insert(pre)
            self.context.add(pro)

        existing = self.context[prop]
        #TODO: report contradiction between prop and existing
        if existing is None:
            prop.reason = reason
            prop.reason.obsolete = False
            insert(prop)
        elif len(reason.all_premises) < len(existing.reason.all_premises):
            reason.obsolete = existing.reason.obsolete
            if self.context.index_of(existing) is not None:
                for pre in existing.reason.premises:
                    pre.implications.remove(existing)
            existing.reason = reason
            for pre in existing.reason.premises:
                pre.implications.add(existing)
            existing.fire_premises_change()
            if hasattr(prop, 'rule'):
                existing.rule = prop.rule
            elif hasattr(existing, 'rule'):
                delattr(existing, 'rule')
            #TODO: if the rule reference changed from 'synthetic',
            # add the property to a transitivity set
            if self.context.index_of(existing) is None:
                insert(existing)

    def explain(self):
        start = time.time()
        frozen = self.scene.is_frozen
        if not frozen:
            self.scene.freeze()
        self.__explain_all()
        if not frozen:
            self.scene.unfreeze()
        self.__explanation_time = time.time() - start

    def __explain_all(self):
        def iteration():
            for rule in self.__rules:
                for prop, comment, premises in rule.generate():
                    prop.rule = rule
                    yield (prop, comment, premises)

            for pia in self.context.list(PointInsideAngleProperty):
                A = pia.angle.vertex
                B = pia.angle.vector0.end
                C = pia.angle.vector1.end
                D = pia.point
                AD = A.segment(D)
                BC = B.segment(C)
                X, reasons = self.context.intersection_of_lines(AD, BC)
                if X is None or X in (A, B, C, D):
                    continue
                if pia.reason.obsolete and all(p.reason.obsolete for p in reasons):
                    continue

                comment = LazyComment('%s is the intersection of ray [%s) and segment [%s]', X, A.vector(D).as_ray, B.segment(C))
                yield (AngleValueProperty(A.angle(D, X), 0), [comment], [pia] + reasons)
                yield (AngleValueProperty(B.angle(C, X), 0), [comment], [pia] + reasons)
                yield (AngleValueProperty(C.angle(B, X), 0), [comment], [pia] + reasons)
                yield (AngleValueProperty(X.angle(B, C), 180), [comment], [pia] + reasons)

            for pia in self.context.list(PointInsideAngleProperty):
                if pia.reason.obsolete:
                    continue
                for endpoint in pia.angle.endpoints:
                    yield (
                        PointsCollinearityProperty(pia.point, pia.angle.vertex, endpoint, False),
                        LazyComment(
                            '%s is the vertex of %s, %s lies on a side, and %s lies inside',
                            pia.angle.vertex, pia.angle, endpoint, pia.point
                        ),
                        [pia]
                    )
                yield (
                    SameOrOppositeSideProperty(pia.angle.vector0.as_segment, pia.point, pia.angle.vector1.end, True),
                    '', #TODO: write comment
                    [pia]
                )
                yield (
                    SameOrOppositeSideProperty(pia.angle.vector1.as_segment, pia.point, pia.angle.vector0.end, True),
                    '', #TODO: write comment
                    [pia]
                )

            for ss0, ss1 in itertools.combinations([p for p in self.context.list(SameOrOppositeSideProperty) if p.same], 2):
                for pts in itertools.combinations(ss0.segment.points + ss1.segment.points, 3):
                    ncl = self.context.not_collinear_property(*pts)
                    if ncl:
                        break
                else:
                    continue

                if ss0.points[0] in ss1.points:
                    if ss0.points[1] in ss1.points:
                        continue
                    common = ss0.points[0]
                    other0 = ss0.points[1]
                    other1 = ss1.points[0] if ss1.points[1] == common else ss1.points[1]
                else:
                    common = ss0.points[1]
                    other0 = ss0.points[0]
                    if ss1.points[0] == common:
                        other1 = ss1.points[1]
                    elif ss1.points[1] == common:
                        other1 = ss1.points[0]
                    else:
                        continue

                if other0 not in ss1.segment.points or other1 not in ss0.segment.points:
                    continue

                vertex, reasons = self.context.intersection_of_lines(ss0.segment, ss1.segment)
                if vertex is None or vertex in [common, other0, other1]:
                    continue

                reasons = [ss0, ss1, ncl] + reasons
                if all(p.reason.obsolete for p in reasons):
                    continue

                yield (
                    PointInsideAngleProperty(common, vertex.angle(other0, other1)),
                    '', #TODO: write comment
                    reasons
                )

            angle_values = [prop for prop in self.context.angle_value_properties() \
                if prop.angle.vertex is not None]

            for av in [av for av in angle_values if av.degree == 0]:
                av_is_too_old = av.reason.obsolete
                vertex = av.angle.vertex
                pt0 = av.angle.vector0.end
                pt1 = av.angle.vector1.end
                for vec in (av.angle.vector0, av.angle.vector1):
                    for nc in self.context.list(PointsCollinearityProperty, [vec.as_segment]):
                        if nc.collinear or av_is_too_old and nc.reason.obsolete:
                            continue
                        segment = vertex.segment(
                            next(pt for pt in nc.points if pt not in vec.points)
                        )
                        yield (
                            SameOrOppositeSideProperty(segment, pt0, pt1, True),
                            LazyComment('%s, %s', av, nc), #TODO: better comment
                            [av, nc]
                        )

            for av in [av for av in angle_values if av.degree == 180]:
                av_is_too_old = av.reason.obsolete
                segment = av.angle.vector0.end.segment(av.angle.vector1.end)
                for ncl in self.context.list(PointsCollinearityProperty, [segment]):
                    if ncl.collinear or av_is_too_old and ncl.reason.obsolete:
                        continue
                    vertex = next(pt for pt in ncl.points if pt not in segment.points)
                    angle = vertex.angle(*segment.points)
                    yield (
                        PointInsideAngleProperty(av.angle.vertex, angle),
                        LazyComment('%s lies inside a segment with endpoints on sides of %s', av.angle.vertex, angle),
                        [av, ncl]
                    )
                    yield (
                        SameOrOppositeSideProperty(av.angle.vertex.segment(vertex), *segment.points, False),
                        LazyComment('%s lies inside segment %s, and %s is not on the line %s', av.angle.vertex, segment, vertex, segment),
                        [av, ncl]
                    )

            for sos0, sos1 in itertools.combinations(self.context.list(SameOrOppositeSideProperty), 2):
                if sos0.reason.obsolete and sos1.reason.obsolete:
                    continue
                if sos0.segment != sos1.segment:
                    continue

                if sos0.points[0] in sos1.points:
                    common = sos0.points[0]
                    other0 = sos0.points[1]
                elif sos0.points[1] in sos1.points:
                    common = sos0.points[1]
                    other0 = sos0.points[0]
                else:
                    continue
                other1 = sos1.points[0] if sos1.points[1] == common else sos1.points[1]
                if other0 == other1:
                    break
                yield (
                    SameOrOppositeSideProperty(sos0.segment, other0, other1, sos0.same == sos1.same),
                    'Transitivity', #TODO: better comment
                    [sos0, sos1]
                )

            for aa in [p for p in self.context.list(AngleKindProperty) if p.kind == AngleKindProperty.Kind.acute]:
                base = aa.angle
                if base.vertex is None:
                    continue
                for vec0, vec1 in [(base.vector0, base.vector1), (base.vector1, base.vector0)]:
                    for col in [p for p in self.context.list(PointsCollinearityProperty, [vec0.as_segment]) if p.collinear]:
                        reasons_are_too_old = aa.reason.obsolete and col.reason.obsolete
                        pt = next(pt for pt in col.points if pt not in vec0.points)
                        for angle in [pt.angle(vec1.end, p) for p in vec0.points]:
                            ka = self.context.angle_value_property(angle)
                            if ka is None or reasons_are_too_old and ka.reason.obsolete:
                                continue
                            if ka.degree >= 90:
                                comment = LazyComment(
                                    '%s, %s, %s are collinear, %s is acute, and %s = %sº',
                                    pt, *vec0.points, base, angle, ka.degree
                                )
                                zero = base.vertex.angle(vec0.end, pt)
                                yield (AngleValueProperty(zero, 0), comment, [col, aa, ka])
                            break

            for aa in [p for p in self.context.list(AngleKindProperty) if p.kind == AngleKindProperty.Kind.acute]:
                base = aa.angle
                if base.vertex is None:
                    continue
                for vec0, vec1 in [(base.vector0, base.vector1), (base.vector1, base.vector0)]:
                    for perp in self.context.list(PerpendicularSegmentsProperty, [vec0.as_segment]):
                        other = perp.segments[0] if vec0.as_segment == perp.segments[1] else perp.segments[1]
                        if vec1.end not in other.points:
                            continue
                        foot = next(pt for pt in other.points if pt != vec1.end)
                        col = self.context.collinearity_property(foot, *vec0.points)
                        if col is None or not col.collinear:
                            continue
                        if aa.reason.obsolete and perp.reason.obsolete and col.reason.obsolete:
                            continue
                        yield (
                            AngleValueProperty(base.vertex.angle(vec0.end, foot), 0),
                            LazyComment(
                                '%s it the foot of the perpendicular from %s to %s, %s is acute',
                                foot, vec1.end, vec0, base
                            ),
                            [perp, col, aa]
                        )

            for aa in [p for p in self.context.list(AngleKindProperty) if p.kind == AngleKindProperty.Kind.obtuse]:
                base = aa.angle
                if base.vertex is None:
                    continue
                for vec0, vec1 in [(base.vector0, base.vector1), (base.vector1, base.vector0)]:
                    for perp in self.context.list(PerpendicularSegmentsProperty, [vec0.as_segment]):
                        other = perp.segments[0] if vec0.as_segment == perp.segments[1] else perp.segments[1]
                        if vec1.end not in other.points:
                            continue
                        foot = next(pt for pt in other.points if pt != vec1.end)
                        col = self.context.collinearity_property(foot, *vec0.points)
                        if col is None or not col.collinear:
                            continue
                        if aa.reason.obsolete and perp.reason.obsolete and col.reason.obsolete:
                            continue
                        yield (
                            AngleValueProperty(base.vertex.angle(vec0.end, foot), 180),
                            LazyComment(
                                '%s it the foot of the perpendicular from %s to %s, %s is obtuse',
                                foot, vec1.end, vec0, base
                            ),
                            [perp, col, aa]
                        )

            for aa in [p for p in self.context.list(AngleValueProperty) if p.degree == 90]:
                base = aa.angle
                if base.vertex is None:
                    continue
                for vec0, vec1 in [(base.vector0, base.vector1), (base.vector1, base.vector0)]:
                    for perp in self.context.list(PerpendicularSegmentsProperty, [vec0.as_segment]):
                        other = perp.segments[0] if vec0.as_segment == perp.segments[1] else perp.segments[1]
                        if vec1.end not in other.points:
                            continue
                        foot = next(pt for pt in other.points if pt != vec1.end)
                        col = self.context.collinearity_property(foot, *vec0.points)
                        if col is None or not col.collinear:
                            continue
                        if aa.reason.obsolete and perp.reason.obsolete and col.reason.obsolete:
                            continue
                        yield (
                            PointsCoincidenceProperty(base.vertex, foot, True),
                            LazyComment(
                                '%s it the foot of the perpendicular from %s to %s, %s is right',
                                foot, vec1.end, vec0, base
                            ),
                            [perp, col, aa]
                        )

#            for oa in [p for p in self.context.list(AngleKindProperty) if p.kind == AngleKindProperty.Kind.obtuse]:
#                base = oa.angle
#                if base.vertex is None:
#                    continue
#                for vec0, vec1 in [(base.vector0, base.vector1), (base.vector1, base.vector0)]:
#                    for col in [p for p in self.context.list(PointsCollinearityProperty, [vec0.as_segment]) if p.collinear]:
#                        reasons_are_too_old = oa.reason.obsolete and col.reason.obsolete
#                        pt = next(pt for pt in col.points if pt not in vec0.points)
#                        for angle in [pt.angle(vec1.end, p) for p in vec0.points]:
#                            ka = self.context.angle_value_property(angle)
#                            if ka is None or reasons_are_too_old and ka.reason.obsolete:
#                                continue
#                            if ka.degree <= 90:
#                                comment = LazyComment(
#                                    '%s, %s, %s are collinear, %s is obtuse, and %s = %sº',
#                                    pt, *vec0.points, base, angle, ka.degree
#                                )
#                                zero = base.vertex.angle(vec0.end, pt)
#                                yield (AngleValueProperty(zero, 180), comment, [col, oa, ka])
#                            break

            for ka in self.context.nondegenerate_angle_value_properties():
                base = ka.angle
                if ka.degree >= 90 or base.vertex is None:
                    continue
                ka_is_too_old = ka.reason.obsolete
                for vec0, vec1 in [(base.vector0, base.vector1), (base.vector1, base.vector0)]:
                    for col in [p for p in self.context.list(PointsCollinearityProperty, [vec0.as_segment]) if p.collinear]:
                        reasons_are_too_old = ka_is_too_old and col.reason.obsolete
                        pt = next(pt for pt in col.points if pt not in vec0.points)
                        for angle in [pt.angle(vec1.end, p) for p in vec0.points]:
                            ka2 = self.context.angle_value_property(angle)
                            if ka2 is None or reasons_are_too_old and ka2.reason.obsolete:
                                continue
                            if ka2.degree > ka.degree:
                                comment = LazyComment(
                                    '%s, %s, %s are collinear, %s is acute, and %s > %s',
                                    pt, *vec0.points, base, angle, base
                                )
                                zero = base.vertex.angle(vec0.end, pt)
                                yield (AngleValueProperty(zero, 0), comment, [ka, col, ka2])
                            break

            for aa0, aa1 in itertools.combinations([a for a in self.context.list(AngleKindProperty) if a.angle.vertex and a.kind == AngleKindProperty.Kind.acute], 2):
                vertex = aa0.angle.vertex
                if vertex != aa1.angle.vertex:
                    continue
                vectors0 = [aa0.angle.vector0, aa0.angle.vector1]
                vectors1 = [aa1.angle.vector0, aa1.angle.vector1]
                common = next((v for v in vectors0 if v in vectors1), None)
                if common is None:
                    continue
                other0 = next(v for v in vectors0 if v != common)
                other1 = next(v for v in vectors1 if v != common)
                col = self.context.collinearity_property(*other0.points, other1.end)
                if col is None or not col.collinear or aa0.reason.obsolete and aa1.reason.obsolete and col.reason.obsolete:
                    continue
                yield (
                    AngleValueProperty(other0.angle(other1), 0),
                    LazyComment('Both %s and %s are acute', aa0.angle, aa1.angle),
                    [aa0, aa1, col]
                )

            for ang0, ang1 in self.context.congruent_angles_with_vertex():
                ncl0 = self.context.not_collinear_property(*ang0.point_set)
                ncl1 = self.context.not_collinear_property(*ang1.point_set)
                if ncl0 and ncl1 or not ncl0 and not ncl1:
                    continue
                ca = self.context.angle_ratio_property(ang0, ang1)
                if ncl0:
                    yield (
                        PointsCollinearityProperty(*ang1.point_set, False),
                        'Transitivity',
                        [ca, ncl0]
                    )
                else:
                    yield (
                        PointsCollinearityProperty(*ang0.point_set, False),
                        'Transitivity',
                        [ca, ncl1]
                    )

            for zero in [p for p in self.context.list(AngleValueProperty) if p.angle.vertex is None and p.degree == 0]:
                zero_is_too_old = zero.reason.obsolete
                ang = zero.angle

                for vec0, vec1 in [(ang.vector0, ang.vector1), (ang.vector1, ang.vector0)]:
                    for i, j in [(0, 1), (1, 0)]:
                        ncl = self.context.not_collinear_property(*vec0.points, vec1.points[i])
                        if ncl is None:
                            continue
                        ne = self.context.not_equal_property(*vec1.points)
                        if ne is None:
                            continue
                        if zero_is_too_old and ncl.reason.obsolete and ne.reason.obsolete:
                            continue
                        yield (
                            PointsCollinearityProperty(*vec0.points, vec1.points[j], False),
                            'Transitivity',
                            [ncl, zero, ne]
                        )
                        yield (
                            PointsCollinearityProperty(*vec1.points, vec0.points[i], False),
                            'Transitivity',
                            [ncl, zero, ne]
                        )
                        yield (
                            PointsCollinearityProperty(*vec1.points, vec0.points[j], False),
                            'Transitivity',
                            [ncl, zero, ne]
                        )

            for zero in [p for p in self.context.list(AngleValueProperty) if p.angle.vertex is None and p.degree == 0]:
                ang = zero.angle
                ncl = self.context.not_collinear_property(*ang.vector0.points, ang.vector1.points[0])
                if ncl is None:
                    continue
                ne = self.context.not_equal_property(*ang.vector1.points)
                if ne is None:
                    continue
                if zero.reason.obsolete and ncl.reason.obsolete and ne.reason.obsolete:
                    continue
                comment = LazyComment('%s ↑↑ %s', ang.vector0, ang.vector1)
                premises = [zero, ncl, ne]
                yield (
                    SameOrOppositeSideProperty(ang.vector0.as_segment, *ang.vector1.points, True),
                    comment, premises
                )
                yield (
                    SameOrOppositeSideProperty(ang.vector1.as_segment, *ang.vector0.points, True),
                    comment, premises
                )
                yield (
                    SameOrOppositeSideProperty(
                        ang.vector0.start.segment(ang.vector1.end),
                        ang.vector0.end, ang.vector1.start, False
                    ),
                    comment, premises
                )
                yield (
                    SameOrOppositeSideProperty(
                        ang.vector1.start.segment(ang.vector0.end),
                        ang.vector1.end, ang.vector0.start, False
                    ),
                    comment, premises
                )

            for sos in self.context.list(SameOrOppositeSideProperty):
                for col in [p for p in self.context.list(PointsCollinearityProperty) if p.collinear]:
                    if sos.segment.points[0] not in col.points:
                        continue
                    if sos.segment.points[1] not in col.points:
                        continue
                    too_old = sos.reason.obsolete and col.reason.obsolete
                    other = next(pt for pt in col.points if pt not in sos.segment.points)
                    for pt in sos.segment.points:
                        ne = self.context.not_equal_property(other, pt)
                        if ne is None or too_old and ne.reason.obsolete:
                            continue
                        yield (
                            SameOrOppositeSideProperty(other.segment(pt), *sos.points, sos.same),
                            LazyComment('%s is same line as %s', other.segment(pt), sos.segment),
                            [sos, col, ne]
                        )

        for prop, comment in enumerate_predefined_properties(self.scene, max_layer=self.__options.get('max_layer', 'user')):
            self.__reason(prop, comment, [])

        self.__iteration_step_count = 0
        while itertools.count():
            explained_size = len(self.context)
            for prop, comment, premises in iteration():
                self.__reason(prop, comment, premises)
            for prop in self.context.all:
                prop.reason.obsolete = prop.reason.generation < self.__iteration_step_count
            self.__iteration_step_count += 1
            if len(self.context) == explained_size:
                break

    def dump(self, properties_to_explain=[]):
        def to_string(reason):
            if reason.premises:
                return '%s (%s)' % (
                    reason.comment,
                    ', '.join(['*%s' % self.context.index_of(prop) for prop in reason.premises])
                )
            else:
                return reason.comment

        if len(self.context) > 0:
            print('Explained:')
            explained = self.context.all
            explained.sort(key=lambda p: self.context.index_of(p))
            for prop in explained:
                print('\t%2d (%d): %s [%s]' % (self.context.index_of(prop), prop.reason.generation, prop, to_string(prop.reason)))
        if properties_to_explain:
            unexplained = [prop for prop in properties_to_explain if prop not in self.context]
            if len(unexplained) > 0:
                print('\nNot explained:')
                for prop in unexplained:
                    print('\t%s' % prop)

    def stats(self, properties_to_explain=[]):
        self.context.circles.dump()
        def type_presentation(kind):
            return kind.__doc__.strip() if kind.__doc__ else kind.__name__

        unexplained = [prop for prop in properties_to_explain if prop not in self.context]
        unexplained_by_kind = {}
        for prop in unexplained:
            kind = type(prop)
            unexplained_by_kind[kind] = unexplained_by_kind.get(kind, 0) + 1
        unexplained_by_kind = [(type_presentation(k), v) for k, v in unexplained_by_kind.items()]
        unexplained_by_kind.sort(key=lambda pair: -pair[1])

        return Stats([
            ('Explained properties', len(self.context)),
            self.context.stats(),
            ('Explained property keys', self.context.keys_num()),
            ('Unexplained properties', len(unexplained)),
            Stats(unexplained_by_kind),
            ('Iterations', self.__iteration_step_count),
            ('Explanation time', '%.3f sec' % self.__explanation_time),
        ], 'Explainer stats')

    def explained(self, obj):
        if isinstance(obj, Property):
            return obj in self.context
        if isinstance(obj, Scene.Angle):
            rsn = self.context.angle_value_property(obj)
            return rsn.degree if rsn else None
        raise Exception('Explanation not supported for objects of type %s' % type(obj).__name__)

    def explanation(self, obj):
        if isinstance(obj, Property):
            return self.context[obj]
        if isinstance(obj, Scene.Angle):
            return self.context.angle_value_property(obj)
        return None
