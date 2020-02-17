from .core import CoreScene
from .constraint import OppositeSideConstraint

class Scene(CoreScene):
    def gravity_centre_point(self, *points, **kwargs):
        assert len(points) > 0
        for p in points:
            self.assert_point(p)

        if len(points) == 1:
            return points[0]
        intermediate = self.gravity_centre_point(*points[1:], auxiliary=True)
        return points[0].ratio_point(intermediate, 1, len(points) - 1, **kwargs)

    def parallel_line(self, line, point, **kwargs):
        self.assert_line(line)
        self.assert_point(point)
        circle0 = point.circle_with_radius(line.point0, line.point1, auxiliary=True)
        circle1 = line.point0.circle_with_radius(line.point1, point, auxiliary=True)
        extra_line = point.line_via(line.point0, auxiliary=True)
        extra_point = circle0.intersection_point(circle1, auxiliary=True)
        extra_point.add_constraint(OppositeSideConstraint(extra_point, line.point1, extra_line))
        return point.line_via(extra_point)
