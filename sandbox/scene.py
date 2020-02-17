from .base import BaseScene
from .constraint import OppositeSideConstraint

class Scene(BaseScene):
    def gravity_centre_point(self, *points, **kwargs):
        assert len(points) > 1
        for p in points:
            self.assert_point(p)

        if len(points) == 2:
            circle0 = points[0].circle_via(points[1], auxiliary=True)
            circle1 = points[1].circle_via(points[0], auxiliary=True)
            line0 = points[0].line_via(points[1], auxiliary=True)
            pt0 = circle0.intersection_point(circle1, auxiliary=True)
            pt1 = circle0.intersection_point(circle1, auxiliary=True)
            pt1.add_constraint(OppositeSideConstraint(pt1, pt0, line0))
            line1 = pt0.line_via(pt1, auxiliary=True)
            return line0.intersection_point(line1, **kwargs)
        
        # TODO: does not work for collinear points 
        centre0 = self.gravity_centre_point(*points[1:], auxiliary=True)
        centre1 = self.gravity_centre_point(*points[:-1], auxiliary=True)
        line0 = points[0].line_via(centre0, auxiliary=True);
        line1 = points[-1].line_via(centre1, auxiliary=True);
        return line0.intersection_point(line1, **kwargs)

    def parallel_line(self, line, point, **kwargs):
        self.assert_line(line)
        self.assert_point(point)
        circle0 = point.circle_with_radius(line.point0, line.point1, auxiliary=True)
        circle1 = line.point0.circle_with_radius(line.point1, point, auxiliary=True)
        extra_line = point.line_via(line.point0, auxiliary=True)
        extra_point = circle0.intersection_point(circle1, auxiliary=True)
        extra_point.add_constraint(OppositeSideConstraint(extra_point, line.point1, extra_line))
        return point.line_via(extra_point)
