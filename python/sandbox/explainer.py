import itertools
import time
import sympy as sp

from .core import Constraint
from .predefined import enumerate_predefined_properties
from .property import *
from .propertyset import PropertySet
from .reason import Reason
from .rules.abstract import PredefinedPropertyRule, SyntheticPropertyRule, create_rule
from .rules.advanced import *
from .rules.basic import *
from .rules.circle import *
from .rules.complex import *
from .rules.cycle import *
from .rules.length import *
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
        self.explanation_time = None
        self.optimization_time = 0
        self.__iteration_step_count = -1

        rule_classes = [
            LineAndTwoPointsToNoncollinearityRule,
            SegmentWithEndpointsOnAngleSidesRule,
            CollinearityToSameLineRule,
            NonCollinearityToDifferentLinesRule,
            NonCollinearityToDifferentLinesRule2,
            CollinearityToPointOnLineRule,
            NonCollinearityToPointNotOnLineRule,
            MissingLineKeysRule,

            LengthRatioTransitivityRule,
            ProportionalLengthsToLengthsRatioRule,
            LengthRatiosWithCommonDenominatorRule,
            SumOfThreeAnglesOnLineRule,
            SumOfThreeAnglesOnLineRule2,
            AngleInTriangleWithTwoKnownAnglesRule,
            SumOfTwoAnglesInTriangleRule,
            SumOfThreeAnglesInTriangleRule,
            AngleBySumOfThreeRule,
            EliminateAngleFromSumRule,
            SumAndRatioOfTwoAnglesRule,
            EqualSumsOfAnglesWithCommonSummandRule,
            EqualSumsOfAnglesRule,
            AngleTypeAndPerpendicularRule,
            CoincidenceTransitivityRule,
            TwoPointsBelongsToTwoLinesRule,
            TwoPointsBelongsToTwoPerpendicularsRule,
            LengthRatioRule,
            IsoscelesNonzeroBaseImpliesNonzeroLegsRule,
            ParallelVectorsRule,
            PerpendicularSegmentsRule,
            PerpendicularSegmentsRule2,
            Degree90ToPerpendicularSegmentsRule,
            Degree90ToPerpendicularSegmentsRule2,
            PerpendicularTransitivityRule,
            PerpendicularToEquidistantRule,
            EquidistantToPerpendicularRule,
            PointsSeparatedByLineAreNotCoincidentRule,
            PointInsideAngleAndSecantRule,
            PointInsideSegmentRelativeToLineRule,
            SameSidePointInsideSegmentRule,
            TwoPerpendicularsRule,
            TwoPerpendicularsRule2,
            ZeroAngleVectorsToPointAndLineConfigurationRule,
            ParallelSameSideRule,
            CommonPerpendicularRule,
            SideProductsInSimilarTrianglesRule,
            SideRatiosInNondegenerateSimilarTrianglesRule,
            CorrespondingAnglesInCongruentTrianglesRule,
            CorrespondingAnglesInSimilarTrianglesRule,
            CorrespondingAnglesInSimilarTrianglesRule2,
            CorrespondingSidesInCongruentTrianglesRule,
            CorrespondingSidesInSimilarTrianglesRule,
            LengthProductEqualityToRatioRule,
            LengthEqualityToRatioEqualityRule,
            MiddleOfSegmentRule,
            KnownAnglesToConvexQuadrilateralRule,
            PointsToConvexQuadrilateralRule,
            PointOnSideOfConvexQuadrialteralRule,
            ConvexQuadrilateralRule,
            SumOfAnglesOfConvexQuadrilateralRule,
            IntersectionOfDiagonalsOfConvexQuadrilateralRule,
            SquareRule,
            SquareDegeneracyRule,
            NondegenerateSquareRule,
            PointInsideHalfOfSquareRule,
            PointInsideSquareRule,
            EquilateralTriangleRule,
            PointInsideTwoAnglesOfTriangleRule,
            PointInsideTriangleRule,
            CentreOfEquilateralTriangleRule,
            BaseAnglesOfIsoscelesWithKnownApexAngleRule,
            BaseAnglesOfIsoscelesRule,
            SecondBaseAngleOfIsoscelesRule,
            LegsOfIsoscelesRule,
            TwoAcuteOrRightAnglesWithCommonSideRule,
            CongruentAnglesWithCommonPartRule,
            RotatedAngleSimplifiedRule,
            RotatedAngleRule,
            AngleTypeByDegreeRule,
            PointsCollinearityByAngleDegreeRule,
            EqualAnglesToCollinearityRule,
            RightAngleDegreeRule,
            AngleTypesInObtuseangledTriangleRule,
            PointInsidePartOfAngleRule,
            PartOfAcuteAngleIsAcuteRule,
            TwoPointsInsideSegmentRule,
            TwoPointsOnRayRule,
            FourPointsOnLineRule,
            FourPointsOnLineRule2,
            SameAngleRule,
            SameAngleRule2,
            SameAngleRule3,
            ZeroDegreeTransitivityRule,
            CorrespondingAnglesRule,
            ConsecutiveInteriorAnglesRule,
            AlternateInteriorAnglesRule,
            SupplementaryAnglesRule,
            VerticalAnglesRule,
            ReversedVerticalAnglesRule,
            CorrespondingAndAlternateAnglesRule,
            CyclicOrderRule,
            ZeroAngleToSameSideRule,
            Angle180ToSameOppositeSideRule,
            PlanePositionsToLinePositionsRule,
            CeviansIntersectionRule,
            PointOnCevianRule,
            OppositeSidesToInsideTriangleRule,
            KnownSumOfAnglesWithCommonSideRule,
            TwoAnglesWithCommonSideRule,
            TwoAnglesWithCommonSideDegreeRule,
            KnownAnglesWithCommonSideRule,
            TwoPointsRelativeToLineTransitivityRule,
            TwoPointsRelativeToLineTransitivityRule2,
            CongruentAnglesDegeneracyRule,
            CongruentAnglesKindRule,
            PointAndAngleRule,
            PointInsideAngleConfigurationRule,
            PointInsideAngleAndPointOnSideRule,
            PerpendicularToSideOfObtuseAngleRule,
            PerpendicularInAcuteAngleRule,
            PerpendicularInAcuteAngleRule2,
            PointOnSegmentWithEndpointsOnSidesOfAngleRule,

            EquilateralTriangleByThreeSidesRule,
            EquilateralTriangleByConrguentLegsAndAngleRule,
            IsoscelesTriangleByConrguentLegsRule,
            IsoscelesTriangleByConrguentBaseAnglesRule,
            CongruentTrianglesByAngleAndTwoSidesRule,
            CongruentTrianglesByThreeSidesRule,
            SimilarTrianglesByTwoAnglesRule,
            SimilarTrianglesByAngleAndTwoSidesRule,
            SimilarTrianglesByAngleAndTwoSidesRule2,
            SimilarTrianglesByThreeSidesRule,
            SimilarTrianglesWithCongruentSideRule,

            SideOppositeToNonAcuteAngleRule,
            SideOppositeToNonAcuteAngleRule2,
            PointInsideSegmentToLengthsInequalityRule,
            LengthsInequalityAndEqualityRule,
            ZeroAngleWithLengthInequalityRule,

            LineAndAcuteAngleRule,
        ]

        if options.get('circles'):
            rule_classes += [
                #ThreeNonCoincidentPointsOnACicrleAreNonCollinearRule,
                CyclicQuadrilateralRule,
                CyclicQuadrilateralRule2,
                PointsOnCircleRule,
                ConcyclicToSameCircleRule,
                InscribedAnglesWithCommonCircularArcRule,
                #PointsOnChordRule,
                TwoChordsIntersectionRule,
                #ThreeCollinearPointsOnCircleRule,
            ]
        if options.get('advanced'):
            rule_classes += [
                RightAngledTriangleMedianRule,
                Triangle30_60_90SidesRule,
                Triangle30_30_120SidesRule,
                Triangle36_36_108SidesRule,
                Triangle72_72_36SidesRule,
            ]
        if options.get('trigonometric'):
            rule_classes += [
                LawOfSinesRule,
            ]

        self.__rules = [create_rule(clazz, self.context) for clazz in rule_classes]

    @property
    def __max_layer(self):
        return self.__options.get('max_layer', 'user')

    def __reason(self, prop, rule, comment, premises=None):
        def normalize_prop(prop):
            for base in prop.bases:
                normalize_prop(base)
            for r in prop.proper_reasons:
                normalize(r)
            prop.reason = prop.reason

        def normalize(reason):
            for index, pre in enumerate(reason.premises):
                prop_and_index = self.context.prop_and_index(pre)
                existing = prop_and_index[0] if prop_and_index else None
                if existing is None:
                    normalize_prop(pre)
                    self.context.add(pre)
                elif pre is not existing:
                    normalize_prop(pre)
                    existing.merge(pre)
                    reason.premises[index] = existing

        reason = Reason(rule, self.__iteration_step_count, comment, premises)
        normalize(reason)
        prop.reason = reason

        existing = self.context[prop]
        if existing is None:
            prop.reason.obsolete = False
            self.context.add(prop)
        else:
            prop.reason.obsolete = existing.reason.obsolete
            was_synthetic = existing.reason.rule == SyntheticPropertyRule.instance()
            existing.merge(prop)
            is_synthetic = existing.reason.rule == SyntheticPropertyRule.instance()
            if was_synthetic and not is_synthetic or self.context.prop_and_index(existing) is None:
                self.context.add(existing)

    def explain(self):
        start = time.time()
        frozen = self.scene.is_frozen
        if not frozen:
            self.scene.freeze()
        self.__explain_all()
        if not frozen:
            self.scene.unfreeze()
        self.explanation_time = time.time() - start

    def __explain_all(self):
        def obsolete_loop_step():
            for aa in self.context.angle_value_properties_for_degree(90, lambda a: a.vertex):
                base = aa.angle
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

        def iteration():
            for rule in self.__rules:
                for prop, comment, premises in rule.generate():
                    yield (prop, rule, comment, premises)

            for four in obsolete_loop_step():
                yield four

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

    def optimize(self):
        def adjust0():
            changed = set()
            for prop in self.context.all:
                if prop.optimize():
                    changed.add(type(prop))
            return changed

        def adjust1():
            changed = set()
            while True:
                changed_diff = adjust0()
                if changed_diff:
                    changed.update(changed_diff)
                else:
                    break

        start = time.time()
        adjust1()
        changed = {'*'}
        while changed:
            self.context.add_synthetics(changed)
            changed = adjust1()
        self.optimization_time = time.time() - start

    def dump(self, properties_to_explain=[]):
        def to_string(reason):
            if reason.premises:
                return '%s (%s)' % (
                    reason.comment,
                    ', '.join(['*%s' % self.context.prop_and_index(prop)[1] for prop in reason.premises])
                )
            else:
                return reason.comment

        if len(self.context) > 0:
            print('Explained:')
            explained = self.context.all
            explained.sort(key=lambda p: self.context.prop_and_index(p)[1])
            for prop in explained:
                print('\t%2d (%d): %s [%s]' % (self.context.prop_and_index(prop)[1], prop.reason.generation, prop, to_string(prop.reason)))
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
            ('Explanation time', '%.3f sec' % self.explanation_time),
            ('Optimisation time', '%.3f sec' % self.optimization_time),
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
