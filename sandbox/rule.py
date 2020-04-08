from .property import AngleValueProperty, LengthRatioProperty, PointsCoincidenceProperty, SumOfAnglesProperty
from .util import _comment, divide

class SumOfAnglesRule:
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

class LengthRatioRule:
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
