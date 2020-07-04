import itertools
import time
import sympy as sp

from .core import Constraint
from .predefined import enumerate_predefined_properties
from .property import *
from .propertyset import PropertySet
from .reason import Reason
from .rules.abstract import PredefinedPropertyRule, SyntheticPropertyRule
from .rules.advanced import *
from .rules.basic import *
from .rules.circle import *
from .rules.cycle import *
from .rules.line import *
from .rules.linear import *
from .rules.quadrilateral import *
from .rules.triangle_elements import *
from .rules.triangles import *
from .rules.trigonometric import *
from .scene import Scene
from .stats import Stats
from .util import LazyComment, Comment

class Explainer:
    def __init__(self, scene, options={}):
        self.scene = scene
        self.__options = options
        self.context = PropertySet(self.scene.points(max_layer=self.__max_layer))
        self.__explanation_time = None
        self.__iteration_step_count = -1
        self.__rules = [
            SegmentWithEndpointsOnAngleSidesRule(self.context),
            CollinearityToSameLineRule(self.context),
            NonCollinearityToDifferentLinesRule(self.context),
            CollinearityToPointOnLineRule(self.context),
            NonCollinearityToPointNotOnLineRule(self.context),
            MissingLineKeysRule(self.context),

            LengthRatioTransitivityRule(self.context),
            ProportionalLengthsToLengthsRatioRule(self.context),
            LengthRatiosWithCommonDenominatorRule(self.context),
            SumOfThreeAnglesOnLineRule(self.context),
            SumOfThreeAnglesOnLineRule2(self.context),
            AngleInTriangleWithTwoKnownAnglesRule(self.context),
            SumOfTwoAnglesInTriangleRule(self.context),
            SumOfThreeAnglesInTriangleRule(self.context),
            AngleBySumOfThreeRule(self.context),
            EliminateAngleFromSumRule(self.context),
            SumAndRatioOfTwoAnglesRule(self.context),
            EqualSumsOfAnglesRule(self.context),
            #SumOfAngles180DegreeRule(self.context),
            AngleTypeAndPerpendicularRule(self.context),
            CoincidenceTransitivityRule(self.context),
            TwoPointsBelongsToTwoLinesRule(self.context),
            TwoPointsBelongsToTwoPerpendicularsRule(self.context),
            LengthRatioRule(self.context),
            ParallelVectorsRule(self.context),
            PerpendicularSegmentsRule(self.context),
            Degree90ToPerpendicularSegmentsRule(self.context),
            Degree90ToPerpendicularSegmentsRule2(self.context),
            PerpendicularTransitivityRule(self.context),
            PerpendicularToEquidistantRule(self.context),
            EquidistantToPerpendicularRule(self.context),
            PointsSeparatedByLineAreNotCoincidentRule(self.context),
            PointInsideAngleAndSecantRule(self.context),
            PointInsideSegmentRelativeToLineRule(self.context),
            SameSidePointInsideSegmentRule(self.context),
            TwoPerpendicularsRule(self.context),
            TwoPerpendicularsRule2(self.context),
            ParallelSameSideRule(self.context),
            CommonPerpendicularRule(self.context),
            SideProductsInSimilarTrianglesRule(self.context),
            CorrespondingAnglesInCongruentTrianglesRule(self.context),
            CorrespondingAnglesInSimilarTrianglesRule(self.context),
            CorrespondingAnglesInSimilarTrianglesRule2(self.context),
            CorrespondingSidesInCongruentTrianglesRule(self.context),
            CorrespondingSidesInSimilarTrianglesRule(self.context),
            LengthProductEqualityToRatioRule(self.context),
            MiddleOfSegmentRule(self.context),
            KnownAnglesToConvexQuadrilateralRule(self.context),
            PointsToConvexQuadrilateralRule(self.context),
            ConvexQuadrilateralRule(self.context),
            SumOfAnglesOfConvexQuadrilateralRule(self.context),
            SquareRule(self.context),
            SquareDegeneracyRule(self.context),
            NondegenerateSquareRule(self.context),
            EquilateralTriangleRule(self.context),
            PointInsideTwoAnglesRule(self.context),
            PointInsideTriangleRule(self.context),
            CentreOfEquilateralTriangleRule(self.context),
            BaseAnglesOfIsoscelesWithKnownApexAngleRule(self.context),
            BaseAnglesOfIsoscelesRule(self.context),
            LegsOfIsoscelesRule(self.context),
            TwoAcuteOrRightAnglesWithCommonSideRule(self.context),
            CongruentAnglesWithCommonPartRule(self.context),
            RotatedAngleSimplifiedRule(self.context),
            RotatedAngleRule(self.context),
            AngleTypeByDegreeRule(self.context),
            PointsCollinearityByAngleDegreeRule(self.context),
            EqualAnglesToCollinearityRule(self.context),
            RightAngleDegreeRule(self.context),
            AngleTypesInObtuseangledTriangleRule(self.context),
            PointInsidePartOfAngleRule(self.context),
            PartOfAcuteAngleIsAcuteRule(self.context),
            TwoPointsInsideSegmentRule(self.context),
            TwoPointsOnRayRule(self.context),
            SameAngleRule(self.context),
            SameAngleRule2(self.context),
            SameAngleRule3(self.context),
            TransversalRule(self.context),
            SupplementaryAnglesRule(self.context),
            VerticalAnglesRule(self.context),
            ReversedVerticalAnglesRule(self.context),
            CorrespondingAndAlternateAnglesRule(self.context),
            CyclicOrderRule(self.context),
            PlanePositionsToLinePositionsRule(self.context),
            CeviansIntersectionRule(self.context),
            PointOnCevianRule(self.context),
            OppositeSidesToInsideTriangleRule(self.context),
            TwoAnglesWithCommonSideRule(self.context),
            TwoAnglesWithCommonSideDegreeRule(self.context),
            KnownAnglesWithCommonSideRule(self.context),
            TwoPointsRelativeToLineTransitivityRule(self.context),
            CongruentAnglesDegeneracyRule(self.context),
            CongruentAnglesKindRule(self.context),
            PointAndAngleRule(self.context),
            PointInsideAngleConfigurationRule(self.context),
            PointInsideAngleAndPointOnSideRule(self.context),
            PerpendicularToSideOfObtuseAngledRule(self.context),
            PerpendicularInAcuteAngleRule(self.context),
            PerpendicularInAcuteAngleRule2(self.context),
            PointOnSegmentWithEndpointsOnSidesOfAngleRule(self.context),

            EquilateralTriangleByThreeSidesRule(self.context),
            EquilateralTriangleByConrguentLegsAndAngleRule(self.context),
            IsoscelesTriangleByConrguentLegsRule(self.context),
            IsoscelesTriangleByConrguentBaseAnglesRule(self.context),
            CongruentTrianglesByAngleAndTwoSidesRule(self.context),
            CongruentTrianglesByThreeSidesRule(self.context),
            SimilarTrianglesByTwoAnglesRule(self.context),
            SimilarTrianglesByAngleAndTwoSidesRule(self.context),
            SimilarTrianglesByAngleAndTwoSidesRule2(self.context),
            SimilarTrianglesByThreeSidesRule(self.context),
            SimilarTrianglesWithCongruentSideRule(self.context),
        ]

        if options.get('circles'):
            self.__rules += [
                #ThreeNonCoincidentPointsOnACicrleAreNonCollinearRule(self.context),
                CyclicQuadrilateralRule(self.context),
                CyclicQuadrilateralRule2(self.context),
                PointsOnCircleRule(self.context),
                ConcyclicToSameCircleRule(self.context),
                InscribedAnglesWithCommonCircularArcRule(self.context),
                #PointsOnChordRule(self.context),
                TwoChordsIntersectionRule(self.context),
                #ThreeCollinearPointsOnCircleRule(self.context),
            ]
        if options.get('advanced'):
            self.__rules += [
                RightAngledTriangleMedianRule(self.context),
                Triangle30_60_90SidesRule(self.context),
                Triangle30_30_120SidesRule(self.context),
                Triangle36_36_108SidesRule(self.context),
                Triangle72_72_36SidesRule(self.context),
            ]
        if options.get('trigonometric'):
            self.__rules += [
                LawOfSinesRule(self.context),
            ]

    @property
    def __max_layer(self):
        return self.__options.get('max_layer', 'user')

    def __reason(self, prop, rule, comment, premises=None):
        reason = Reason(rule, self.__iteration_step_count, comment, premises)
        def insert(pro):
            for pre in pro.reason.premises:
                if self.context.index_of(pre) is None:
                    insert(pre)
            self.context.add(pro)

        existing = self.context[prop]
        if existing is None:
            prop.reason = reason
            prop.reason.obsolete = False
            insert(prop)
        elif reason.cost < existing.reason.cost:
            #### +++ HACK +++
            # TODO: move this hack outside of explainer
            if isinstance(prop, AngleRatioProperty) and prop.same:
                existing.same = True
            #### --- HACK ---
            prop.reason = reason
            reason.obsolete = existing.reason.obsolete
            was_synthetic = existing.reason.rule == SyntheticPropertyRule.instance()
            existing.reason = reason
            if was_synthetic or self.context.index_of(existing) is None:
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
                    yield (prop, rule, comment, premises)

            angle_values = [prop for prop in self.context.angle_value_properties() \
                if prop.angle.vertex is not None]

            for av in [av for av in angle_values if av.degree == 0]:
                av_is_too_old = av.reason.obsolete
                vertex = av.angle.vertex
                pt0 = av.angle.vectors[0].end
                pt1 = av.angle.vectors[1].end
                for vec in av.angle.vectors:
                    for pt2 in self.context.not_collinear_points(vec.as_segment):
                        nc = self.context.collinearity_property(pt2, *vec.points)
                        if av_is_too_old and nc.reason.obsolete:
                            continue
                        segment = vertex.segment(pt2)
                        yield (
                            SameOrOppositeSideProperty(segment, pt0, pt1, True),
                            None,
                            LazyComment('%s, %s', av, nc), #TODO: better comment
                            [av, nc]
                        )

            for aa in [p for p in self.context.list(AngleKindProperty) if p.kind == AngleKindProperty.Kind.acute]:
                base = aa.angle
                if base.vertex is None:
                    continue
                for vec0, vec1 in [base.vectors, reversed(base.vectors)]:
                    for pt in self.context.collinear_points(vec0.as_segment):
                        col = self.context.collinearity_property(pt, *vec0.points)
                        reasons_are_too_old = aa.reason.obsolete and col.reason.obsolete
                        for angle in [pt.angle(vec1.end, p) for p in vec0.points]:
                            ka = self.context.angle_value_property(angle)
                            if ka is None or reasons_are_too_old and ka.reason.obsolete:
                                continue
                            if ka.degree >= 90:
                                comment = Comment(
                                    '$%{point:pt0}$, $%{point:pt1}$, $%{point:pt2}$ are collinear, $%{angle:base}$ is acute, and $%{anglemeasure:angle} = %{degree:degree}$',
                                    {
                                        'pt0': pt,
                                        'pt1': vec0.points[0],
                                        'pt2': vec0.points[1],
                                        'base': base,
                                        'angle': angle,
                                        'degree': ka.degree
                                    }
                                )
                                zero = base.vertex.angle(vec0.end, pt)
                                yield (AngleValueProperty(zero, 0), None, comment, [col, aa, ka])
                            break

            for aa in self.context.angle_value_properties_for_degree(90):
                base = aa.angle
                if base.vertex is None:
                    continue
                for vec0, vec1 in [base.vectors, reversed(base.vectors)]:
                    for perp in self.context.list(PerpendicularSegmentsProperty, [vec0.as_segment]):
                        other = perp.segments[0] if vec0.as_segment == perp.segments[1] else perp.segments[1]
                        if vec1.end not in other.points:
                            continue
                        foot = next(pt for pt in other.points if pt != vec1.end)
                        if foot in vec0.points:
                            continue
                        col = self.context.collinearity_property(foot, *vec0.points)
                        if col is None or not col.collinear:
                            continue
                        if aa.reason.obsolete and perp.reason.obsolete and col.reason.obsolete:
                            continue
                        yield (
                            PointsCoincidenceProperty(base.vertex, foot, True),
                            None,
                            Comment(
                                '$%{point:foot}$ is the foot of the perpendicular from $%{point:pt}$ to $%{line:line}$, and $%{angle:angle}$ is right',
                                {'foot': foot, 'pt': vec1.end, 'line': vec0, 'angle': base}
                            ),
                            [perp, col, aa]
                        )

#            for oa in [p for p in self.context.list(AngleKindProperty) if p.kind == AngleKindProperty.Kind.obtuse]:
#                base = oa.angle
#                if base.vertex is None:
#                    continue
#                for vec0, vec1 in [base.vectors, reversed(base.vectors)]:
#                    for pt in self.context.collinear_points(vec0.as_segment):
#                        col = self.context.collinearity_property(pt, *vec0.points)
#                        reasons_are_too_old = oa.reason.obsolete and col.reason.obsolete
#                        for angle in [pt.angle(vec1.end, p) for p in vec0.points]:
#                            ka = self.context.angle_value_property(angle)
#                            if ka is None or reasons_are_too_old and ka.reason.obsolete:
#                                continue
#                            if ka.degree <= 90:
#                                comment = LazyComment(
#                                    '%s, %s, %s are collinear, %s is obtuse, and %s = %s',
#                                    pt, *vec0.points, base, angle, ka.degree_str
#                                )
#                                zero = base.vertex.angle(vec0.end, pt)
#                                yield (AngleValueProperty(zero, 180), None, comment, [col, oa, ka])
#                            break

            for ka in self.context.nondegenerate_angle_value_properties():
                base = ka.angle
                if ka.degree == 180 or base.vertex is None:
                    continue
                ka_is_too_old = ka.reason.obsolete
                for vec0, vec1 in [base.vectors, reversed(base.vectors)]:
                    for pt in self.context.collinear_points(vec0.as_segment):
                        col = self.context.collinearity_property(pt, *vec0.points)
                        reasons_are_too_old = ka_is_too_old and col.reason.obsolete
                        for angle in [pt.angle(vec1.end, p) for p in vec0.points]:
                            ka2 = self.context.angle_value_property(angle)
                            if ka2 is None or reasons_are_too_old and ka2.reason.obsolete:
                                continue
                            if ka2.degree > ka.degree:
                                comment = Comment(
                                    '$%{point:pt0}$, $%{point:pt1}$, $%{point:pt2}$ are collinear and $%{anglemeasure:angle0}$ > $%{anglemeasure:angle1}$',
                                    {'pt0': pt, 'pt1': vec0.points[0], 'pt2': vec0.points[1], 'angle0': angle, 'angle1': base}
                                )
                                zero = base.vertex.angle(vec0.end, pt)
                                yield (AngleValueProperty(zero, 0), None, comment, [col, ka2, ka])
                            break

            for aa0, aa1 in itertools.combinations([a for a in self.context.list(AngleKindProperty) if a.angle.vertex and a.kind == AngleKindProperty.Kind.acute], 2):
                vertex = aa0.angle.vertex
                if vertex != aa1.angle.vertex:
                    continue
                vectors0 = aa0.angle.vectors
                vectors1 = aa1.angle.vectors
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
                    None,
                    Comment(
                        'both $%{angle:angle0}$ and $%{angle:angle1}$ are acute',
                        {'angle0': aa0.angle, 'angle1': aa1.angle}
                    ),
                    [aa0, aa1, col]
                )

#            for zero in [p for p in self.context.list(AngleValueProperty) if p.angle.vertex is None and p.degree == 0]:
#                zero_is_too_old = zero.reason.obsolete
#                ang = zero.angle
#
#                for vec0, vec1 in [ang.vectors, reversed(ang.vectors)]:
#                    for i, j in [(0, 1), (1, 0)]:
#                        ncl = self.context.collinearity(*vec0.points, vec1.points[i])
#                        if ncl is None or ncl.collinear:
#                            continue
#                        ne = self.context.not_equal_property(*vec1.points)
#                        if ne is None:
#                            continue
#                        if zero_is_too_old and ncl.reason.obsolete and ne.reason.obsolete:
#                            continue
#                        yield (
#                            PointsCollinearityProperty(*vec0.points, vec1.points[j], False),
#                            None,
#                            'Transitivity',
#                            [ncl, zero, ne]
#                        )
#                        yield (
#                            PointsCollinearityProperty(*vec1.points, vec0.points[i], False),
#                            None,
#                            'Transitivity',
#                            [ncl, zero, ne]
#                        )
#                        yield (
#                            PointsCollinearityProperty(*vec1.points, vec0.points[j], False),
#                            None,
#                            'Transitivity',
#                            [ncl, zero, ne]
#                        )

            for zero in [p for p in self.context.list(AngleValueProperty) if p.angle.vertex is None and p.degree == 0]:
                ang = zero.angle
                ncl = self.context.collinearity_property(*ang.vectors[0].points, ang.vectors[1].points[0])
                if ncl is None or ncl.collinear:
                    continue
                ne = self.context.not_equal_property(*ang.vectors[1].points)
                if ne is None:
                    continue
                if zero.reason.obsolete and ncl.reason.obsolete and ne.reason.obsolete:
                    continue
                comment = Comment(
                    '$%{vector:vec0} \\uparrow\\!\\!\\!\\uparrow %{vector:vec1}$',
                    {'vec0': ang.vectors[0], 'vec1': ang.vectors[1]}
                )
                premises = [zero, ncl, ne]
                yield (
                    SameOrOppositeSideProperty(ang.vectors[0].as_segment, *ang.vectors[1].points, True),
                    None, comment, premises
                )
                yield (
                    SameOrOppositeSideProperty(ang.vectors[1].as_segment, *ang.vectors[0].points, True),
                    None, comment, premises
                )
                yield (
                    SameOrOppositeSideProperty(
                        ang.vectors[0].start.segment(ang.vectors[1].end),
                        ang.vectors[0].end, ang.vectors[1].start, False
                    ),
                    None, comment, premises
                )
                yield (
                    SameOrOppositeSideProperty(
                        ang.vectors[1].start.segment(ang.vectors[0].end),
                        ang.vectors[1].end, ang.vectors[0].start, False
                    ),
                    None, comment, premises
                )

            for sos in self.context.list(SameOrOppositeSideProperty):
                for other in self.context.collinear_points(sos.segment):
                    col = self.context.collinearity_property(other, *sos.segment.points)
                    too_old = sos.reason.obsolete and col.reason.obsolete
                    for pt in sos.segment.points:
                        ne = self.context.not_equal_property(other, pt)
                        if ne is None or too_old and ne.reason.obsolete:
                            continue
                        yield (
                            SameOrOppositeSideProperty(other.segment(pt), *sos.points, sos.same),
                            None,
                            Comment(
                                '$%{line:line0}$ is the same line as $%{line:line1}$',
                                {'line0': other.segment(pt), 'line1': sos.segment}
                            ),
                            [sos, col, ne]
                        )

        for prop, comment in enumerate_predefined_properties(self.scene, max_layer=self.__max_layer):
            self.__reason(prop, PredefinedPropertyRule.instance(), comment, [])

        self.__iteration_step_count = 0
        while itertools.count():
            explained_size = len(self.context)
            for prop, rule, comment, premises in iteration():
                self.__reason(prop, rule, comment, premises)
            for prop in self.context.all:
                prop.reason.obsolete = prop.reason.generation < self.__iteration_step_count - 1
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
