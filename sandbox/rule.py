from .property import *
from .util import _comment, divide

class Rule:
    pass

class SingleSourceRule(Rule):
    def accepts(self, prop):
        return True

    def sources(self, context):
        return [p for p in context.list(self.property_type) if self.accepts(p)]

class DifferentAnglesToDifferentPointsRule(Rule):
    def sources(self, context):
        return itertools.combinations(context.angle_value_properties(), 2)

    def apply(self, src, context):
        av0, av1 = src

        if av0.degree == av1.degree or av0.reason.obsolete and av1.reason.obsolete:
            return
        ang0 = av0.angle
        ang1 = av1.angle

        if ang0.vector0 == ang1.vector0:
            vec0, vec1 = ang0.vector1, ang1.vector1
        elif ang0.vector0 == ang1.vector1:
            vec0, vec1 = ang0.vector1, ang1.vector0
        elif ang0.vector1 == ang1.vector0:
            vec0, vec1 = ang0.vector0, ang1.vector1
        elif ang0.vector1 == ang1.vector1:
            vec0, vec1 = ang0.vector0, ang1.vector0
        else:
            return

        if vec0.start == vec1.start:
            prop = PointsCoincidenceProperty(vec0.end, vec1.end, False)
        elif vec0.end == vec1.end:
            prop = PointsCoincidenceProperty(vec0.start, vec1.start, False)
        else:
            return

        yield (prop, _comment('Otherwise, %s = %s', ang0, ang1), [av0, av1])

class SumOfAnglesRule(SingleSourceRule):
    property_type = SumOfAnglesProperty

    def apply(self, prop, context):
        ar = context.angles_ratio_property(prop.angle0, prop.angle1)
        if ar is None or prop.reason.obsolete and ar.reason.obsolete:
            return
        value1 = divide(prop.degree, 1 + ar.value)
        value0 = prop.degree - value1
        if ar.value == 1:
            comment0 = _comment('%s + %s = %s', ar.angle0, ar.angle0, prop.degree),
            comment1 = _comment('%s + %s = %s', ar.angle1, ar.angle1, prop.degree),
        else:
            comment0 = _comment('%s + %s / %s = %s', ar.angle0, ar.angle0, ar.value, prop.degree),
            comment1 = _comment('%s + %s %s = %s', ar.angle1, ar.value, ar.angle1, prop.degree),
        yield (AngleValueProperty(ar.angle0, value0), comment0, [prop, ar])
        yield (AngleValueProperty(ar.angle1, value1), comment1, [prop, ar])

class LengthRatioRule(SingleSourceRule):
    property_type = LengthRatioProperty

    def apply(self, prop, context):
        seg0 = prop.segment0
        seg1 = prop.segment1

        ne0 = context.not_equal_property(*seg0.points)
        ne1 = context.not_equal_property(*seg1.points)
        if ne0 is not None and ne1 is None:
            if prop.reason.obsolete and ne0.reason.obsolete:
                return
            yield (PointsCoincidenceProperty(*seg1.points, False), _comment('Otherwise, %s = %s', *seg0.points), [prop, ne0])
        elif ne1 is not None and ne0 is None:
            if prop.reason.obsolete and ne1.reason.obsolete:
                return
            yield (PointsCoincidenceProperty(*seg0.points, False), _comment('Otherwise, %s = %s', *seg1.points), [prop, ne1])
        elif ne0 is None and ne1 is None:
            common = next((pt for pt in seg0.points if pt in seg1.points), None)
            if common is None:
                return
            pt0 = next(pt for pt in seg0.points if pt != common)
            pt1 = next(pt for pt in seg1.points if pt != common)
            ne = context.not_equal_property(pt0, pt1)
            if ne is None or prop.reason.obsolete and ne.reason.obsolete:
                return
            yield (PointsCoincidenceProperty(*seg0.points, False), _comment('Otherwise, %s = %s = %s', ne.points[0], common, ne.points[1]), [prop, ne])
            yield (PointsCoincidenceProperty(*seg1.points, False), _comment('Otherwise, %s = %s = %s', ne.points[1], common, ne.points[0]), [prop, ne])

class ParallelVectorsRule(SingleSourceRule):
    property_type = ParallelVectorsProperty

    def apply(self, pv, context):
        vec0 = pv.vector0
        vec1 = pv.vector1
        ne0 = context.not_equal_property(*vec0.points)
        ne1 = context.not_equal_property(*vec1.points)
        if ne0 is None or ne1 is None:
            return
        if pv.reason.obsolete and ne0.reason.obsolete and ne1.reason.obsolete:
            return
        for prop in AngleValueProperty.generate(vec0, vec1, 0):
            yield (
                prop,
                _comment('Non-zero parallel vectors %s and %s', vec0, vec1),
                [pv, ne0, ne1]
            )

class PerpendicularVectorsRule(SingleSourceRule):
    property_type = PerpendicularVectorsProperty

    def apply(self, pv, context):
        vec0 = pv.vector0
        vec1 = pv.vector1
        ne0 = context.not_equal_property(*vec0.points)
        ne1 = context.not_equal_property(*vec1.points)
        if ne0 is None or ne1 is None:
            return
        if pv.reason.obsolete and ne0.reason.obsolete and ne1.reason.obsolete:
            return
        for prop in AngleValueProperty.generate(vec0, vec1, 90):
            yield (
                prop,
                _comment('Non-zero perpendicular vectors %s and %s', vec0, vec1),
                [pv, ne0, ne1]
            )

class SeparatedPointsRule(SingleSourceRule):
    property_type = SameOrOppositeSideProperty

    def accepts(self, prop):
        return not prop.same

    def apply(self, prop, context):
        if not prop.reason.obsolete:
            yield (
                PointsCoincidenceProperty(prop.points[0], prop.points[1], False),
                _comment('%s and %s are separated by line %s', prop.points[0], prop.points[1], prop.segment),
                [prop]
            )