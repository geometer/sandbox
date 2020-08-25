from ..property import *

from .abstract import Rule, accepts_auto, processed_cache, source_type

@source_type(PointInsideAngleProperty)
@processed_cache(set())
@accepts_auto
class PartOfAngleIsLessThanWholeRule(Rule):
    def apply(self, prop):
        self.processed.add(prop)
        for vec in prop.angle.vectors:
            angle = prop.angle.vertex.angle(vec.end, prop.point)
            yield (
                AnglesInequalityProperty(angle, prop.angle),
                Comment('$%{angle:part}$ is part of $%{angle:whole}$', {'part': angle, 'whole': prop.angle}),
                [prop]
            )

@source_type(LineAndTwoPointsProperty)
@processed_cache(set())
class InequalAnglesWithCommonSide(Rule):
    def accepts(self, prop):
        return prop.same_side

    def apply(self, prop):
        line = self.context.line_for_key(prop.line_key)
        pt_set = frozenset(prop.points)
        for segment in line.segments:
            same_side_prop = None
            for pt0, pt1 in (segment.points, reversed(segment.points)):
                key = (pt0, pt1, pt_set)
                if key in self.processed:
                    continue

                angle0 = pt0.angle(pt1, prop.points[0])
                angle1 = pt0.angle(pt1, prop.points[1])
                comp = self.context.compare_angles(angle0, angle1)
                if comp is None:
                    continue
                self.processed.add(key)
                if comp == 0:
                    continue
                inequality = self.context.angles_inequality_property(angle0, angle1)

                if prop.points[0] in inequality.angles[0].endpoints:
                    point = prop.points[0]
                else:
                    point = prop.points[1]

                if same_side_prop is None:
                    same_side_prop = self.context.line_and_two_points_property(segment, *prop.points)
                
                yield (
                    PointInsideAngleProperty(point, inequality.angles[1]),
                    Comment(
                        '$%{angle:part}$ is part of $%{angle:whole}$',
                        {'part': inequality.angles[0], 'whole': inequality.angles[1]}
                    ),
                    [same_side_prop, inequality]
                )

@source_type(LengthsInequalityProperty)
@processed_cache(set())
class LengthsInequalityAndEqualityRule(Rule):
    def apply(self, prop):
        congruents0 = self.context.congruent_segments_for(prop.segments[0])
        congruents1 = self.context.congruent_segments_for(prop.segments[1])
        congruency = {} # seg => congruency property
        def congruency_prop(seg, index):
            cached = congruency.get(seg)
            if cached:
                return cached
            cong = self.context.congruent_segments_property(prop.segments[index], seg, allow_zeroes=True)
            congruency[seg] = cong
            return cong

        for seg in congruents0:
            key = (prop, seg)
            if key in self.processed:
                continue
            self.processed.add(key)
            cong = congruency_prop(seg, 0) 
            yield (
                LengthsInequalityProperty(seg, prop.segments[1]),
                Comment(
                    '$|%{segment:seg}| = |%{segment:seg0}| < |%{segment:seg1}|$',
                    {'seg': seg, 'seg0': prop.segments[0], 'seg1': prop.segments[1]}
                ),
                [prop, cong]
            )

        for seg in congruents1:
            key = (prop, seg)
            if key in self.processed:
                continue
            self.processed.add(key)
            cong = congruency_prop(seg, 1) 
            yield (
                LengthsInequalityProperty(prop.segments[0], seg),
                Comment(
                    '$|%{segment:seg0}| < |%{segment:seg1}| = |%{segment:seg}|$',
                    {'seg': seg, 'seg0': prop.segments[0], 'seg1': prop.segments[1]}
                ),
                [prop, cong]
            )

        for seg0, seg1 in itertools.product(congruents0, congruents1):
            key = (prop, seg0, seg1)
            if key in self.processed:
                continue
            self.processed.add(key)
            cong0 = congruency_prop(seg0, 0) 
            cong1 = congruency_prop(seg1, 1) 
            yield (
                LengthsInequalityProperty(seg0, seg1),
                Comment(
                    '$|%{segment:seg0}| = |%{segment:known0}| < |%{segment:known1}| = |%{segment:seg1}|$',
                    {'seg0': seg0, 'seg1': seg1, 'known0': prop.segments[0], 'known1': prop.segments[1]}
                ),
                [cong0, prop, cong1]
            )
