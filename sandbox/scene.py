"""
This module is to be extended in the future to add more construction methods.
"""

from .core import CoreScene

class Scene(CoreScene):
    """
    The main class Scene.
    Adds composite construction methods to CoreScene.
    """

    def gravity_centre_point(self, *points, **kwargs):
        """
        Constructs the gravity centre of the points, with equal weghts.
        """
        assert len(points) > 0
        for pnt in points:
            self.assert_point(pnt)

        if len(points) == 1:
            return points[0]
        intermediate = self.gravity_centre_point(*points[1:], auxiliary=True)
        return points[0].ratio_point(intermediate, 1, len(points) - 1, **kwargs)

    def opposite_parallelogram_point(self, point0, point1, point2, **kwargs):
        """
        Constructs the fourth point of the parallelogram, opposite to point0.
        Does not suppose any (non-)collinearity conditions.
        """
        self.assert_point(point0)
        self.assert_point(point1)
        self.assert_point(point2)
        centre = point1.ratio_point(point2, 1, 1, auxiliary=True)
        return centre.ratio_point(point0, 2, -1, **kwargs)

    def parallel_line(self, line, point, **kwargs):
        """
        Constructs a line parallel to the given line through the given point.
        """
        fourth = self.opposite_parallelogram_point(line.point0, point, line.point1, auxiliary=True)
        return point.line_through(fourth, **kwargs)

    def perpendicular_foot_point(self, point, line, **kwargs):
        """
        The foot of the perpendicular from the point to the line
        """
        self.assert_point(point)
        self.assert_line(line)
        tmp = line.free_point(auxiliary=True)
        circle = point.circle_through(tmp, auxiliary=True)
        tmp2 = line.intersection_point(circle, auxiliary=True)
        tmp2.not_equal_constraint(tmp)
        return tmp.ratio_point(tmp2, 1, 1, **kwargs)

    def line_through(self, point, **kwargs):
        """
        A line through the point
        """
        self.assert_point(point)
        return point.line_through(self.free_point(auxiliary=True), **kwargs)

    def perpendicular_bisector_line(self, point0, point1, **kwargs):
        """
        The perpendicular bisector to the segment [point0, point1]
        """
        self.assert_point(point0)
        self.assert_point(point1)
        circle0 = point0.circle_through(point1, auxiliary=True)
        circle1 = point1.circle_through(point0, auxiliary=True)
        tmp0 = circle0.intersection_point(circle1, auxiliary=True)
        tmp1 = circle0.intersection_point(circle1, auxiliary=True)
        tmp1.not_equal_constraint(tmp0)
        return tmp0.line_through(tmp1, **kwargs)

    def angle_bisector_line(self, A, B, C, **kwargs):
        """
        The bisector of ∠ BAC
        """
        self.assert_point(A)
        self.assert_point(B)
        self.assert_point(C)
        A.not_equal_constraint(B)
        A.not_equal_constraint(C)
        circle = A.circle_through(B, auxiliary=True)
        line = A.line_through(C, auxiliary=True)
        X = circle.intersection_point(line, auxiliary=True)
        X.same_side_constraint(C, A.line_through(B, auxiliary=True))
        Y = X.ratio_point(B, 1, 1, auxiliary=True)
        return A.line_through(Y, **kwargs)

    def perpendicular_line(self, point, line, **kwargs):
        """
        Perpendicular to the line through the point
        """
        if isinstance(point, CoreScene.Line) and isinstance(line, CoreScene.Point):
            point, line = line, point
        self.assert_point(point)
        self.assert_line(line)
        on_line_point = line.free_point(auxiliary=True)
        circle = point.circle_through(on_line_point, auxiliary=True)
        on_line_point2 = line.intersection_point(circle, auxiliary=True)
        on_line_point2.not_equal_constraint(on_line_point)
        circle1 = on_line_point.circle_through(on_line_point2, auxiliary=True)
        circle2 = on_line_point2.circle_through(on_line_point, auxiliary=True)
        x_0 = circle1.intersection_point(circle2, auxiliary=True)
        x_1 = circle2.intersection_point(circle1, auxiliary=True)
        x_1.not_equal_constraint(x_0)
        return x_0.line_through(x_1, **kwargs)

    def incentre_point(self, A, B, C, **kwargs):
        """
        Centre of the inscribed circle of △ABC
        """
        self.assert_point(A)
        self.assert_point(B)
        self.assert_point(C)
        A.not_collinear_constraint(B, C)
        bisectorA = self.angle_bisector_line(A, B, C, auxiliary=True)
        bisectorB = self.angle_bisector_line(B, A, C, auxiliary=True)
        return bisectorA.intersection_point(bisectorB, **kwargs)

    def incircle(self, A, B, C, **kwargs):
        """
        Inscribed circle of △ABC
        """
        centre = self.incentre_point(A, B, C, auxiliary=True)
        side = A.line_through(B, auxiliary=True)
        foot = self.perpendicular_foot_point(centre, side, auxiliary=True)
        return centre.circle_through(foot, **kwargs)
