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
from .rules.inequality import *
from .rules.length import *
from .rules.line import *
from .rules.linear import *
from .rules.quadrilateral import *
from .rules.triangle_elements import *
from .rules.triangles import *
from .rules.trigonometric import *
from .scene import Scene
from .stats import Stats
from .util import Comment

class Explainer:
    def __init__(self, scene, context=None, extra_properties=[], extra_rules=set(), rules=None):
        self.scene = scene
        self.explanation_time = None
        self.optimization_time = 0
        self.__iteration_step_count = -1

        if context is not None:
            self.context = context
        else:
            self.context = PropertySet(self.scene.points(max_layer='user'))

        if extra_properties:
            for prop, comment in extra_properties:
                self.__reason(prop, PredefinedPropertyRule.instance(), comment, [])

        if rules:
            self.rules = rules
        else:
            self.__create_rules(extra_rules)

    def __create_rules(self, extra_rules):
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
            CongruentOrientedAnglesWithPerpendicularSidesRule,
            AngleTypeByDegreeRule,
            PointsCollinearityByAngleDegreeRule,
            EqualAnglesToCollinearityRule,
            RightAngleDegreeRule,
            AngleTypesInObtuseangledTriangleRule,
            PointInsidePartOfAngleRule,
            PartOfAngleIsLessThanWholeRule,
            PartOfAcuteAngleIsAcuteRule,
            #AnglesInequalityAndEqualityRule,
            InequalAnglesWithCommonSide,
            TwoPointsInsideSegmentRule,
            TwoPointsOnRayRule,
            FourPointsOnLineRule,
            FourPointsOnLineRule2,
            SameAngleRule,
            SameAngleRule2,
            SameAngleDegreeRule2,
            SameAngleRule3,
            SameAngleDegreeRule3,
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
            OrthocenterLiesOnAltitudeRule,

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
            LineAndTwoAnglesRule,
            TwoFootsOfSamePerpendicularRule,
            TwoAnglesWithCommonAndCollinearSidesRule,
        ]

        if 'circles' in extra_rules:
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
        if 'advanced' in extra_rules:
            rule_classes += [
                RightAngledTriangleMedianRule,
                Triangle30_60_90SidesRule,
                Triangle30_30_120SidesRule,
                Triangle36_36_108SidesRule,
                Triangle72_72_36SidesRule,
                IntersectionOfTwoAltitudesIsTheOrthocentreRule,
            ]
        if 'trigonometric' in extra_rules:
            rule_classes += [
                LawOfSinesRule,
            ]

        self.rules = [create_rule(clazz, self.context) for clazz in rule_classes]

    def __reason(self, prop, rule, comment, premises):
        reason = Reason(rule, comment, premises)
        prop.reason = reason
        self.context.insert(prop)

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
        def iteration():
            for rule in self.rules:
                for prop, comment, premises in rule.generate():
                    yield (prop, rule, comment, premises)

        if len(self.context) == 0:
            for prop, comment in enumerate_predefined_properties(self.scene, set(self.context.points)):
                self.__reason(prop, PredefinedPropertyRule.instance(), comment, [])

        self.__iteration_step_count = 0
        while itertools.count():
            count = 0
            for prop, rule, comment, premises in iteration():
                count += 1
                self.__reason(prop, rule, comment, premises)
            self.__iteration_step_count += 1
            if count == 0:
                break

    def optimize(self):
        def adjust0():
            changed = set()
            for prop in self.context.all:
                prop.reason.reset_premises()
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
                print('\t%2d: %s [%s]' % (self.context.prop_and_index(prop)[1], prop, to_string(prop.reason)))
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
