"""
This module is to be extended in the future to add more construction methods.
"""

from .core import CoreScene

class Scene(CoreScene):
    """
    The main class Scene.
    Adds composite construction methods to CoreScene.
    """

    def middle_point(self, A, B, **kwargs):
        """
        Constructs middle point of the segment AB.
        """
        self.assert_point(A)
        self.assert_point(B)
        return A.ratio_point(B, 1, 1, **kwargs)

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
        return self.middle_point(tmp, tmp2, **kwargs)

    def orthocentre_point(self, A, B, C, **kwargs):
        """
        Orthocentre of △ABC (heights intersection point)
        """
        self.assert_point(A)
        self.assert_point(B)
        self.assert_point(C)
        A.not_collinear_constraint(B, C)
        height_A = self.height((A, B, C), A, auxiliary = True)
        height_B = self.height((A, B, C), B, auxiliary = True)
        point = height_A.intersection_point(height_B, **kwargs)
        height_C = self.height((A, B, C), C, auxiliary = True)
        point.belongs_to(height_C)
        return point

    def circumcentre_point(self, A, B, C, **kwargs):
        """
        Circumcentre of △ABC (perpendicular bisectors intersection point)
        """
        self.assert_point(A)
        self.assert_point(B)
        self.assert_point(C)
        A.not_collinear_constraint(B, C)
        bisector_AB = self.perpendicular_bisector_line(A, B, auxiliary=True)
        bisector_AC = self.perpendicular_bisector_line(A, C, auxiliary=True)
        return bisector_AB.intersection_point(bisector_AC, **kwargs)

    def free_line_through(self, point, **kwargs):
        """
        A line through the point
        """
        self.assert_point(point)
        extra = self.free_point(auxiliary=True)
        extra.not_equal_constraint(point)
        return point.line_through(extra, **kwargs)

    def perpendicular_bisector_line(self, point0, point1, **kwargs):
        """
        The perpendicular bisector to the segment [point0, point1]
        """
        self.assert_point(point0)
        self.assert_point(point1)
        point0.not_equal_constraint(point1)
        circle0 = point0.circle_through(point1, auxiliary=True)
        circle1 = point1.circle_through(point0, auxiliary=True)
        tmp0 = circle0.intersection_point(circle1, auxiliary=True)
        tmp1 = circle0.intersection_point(circle1, auxiliary=True)
        tmp1.not_equal_constraint(tmp0)
        bisector = tmp0.line_through(tmp1, **kwargs)
        self.middle_point(point0, point1, auxiliary=True).belongs_to(bisector)
        return bisector

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
        perpendicular = x_0.line_through(x_1, **kwargs)
        point.belongs_to(perpendicular)
        perpendicular.perpendicular_constraint(line)
        return perpendicular

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

    def circumcircle(self, A, B, C, **kwargs):
        """
        Circumscribed circle of △ABC
        """
        centre = self.circumcentre_point(A, B, C, auxiliary=True)
        return centre.circle_through(A, **kwargs)

    def triangle(self, labels=None, auxiliary=False):
        """
        Free triangle
        Pass array of three strings as 'labels' to use as point labels
        Returns tuple of three points
        """
        assert not labels or len(labels) == 3
        def point(index):
            args = {}
            if auxiliary:
                args['auxiliary'] = True
            if labels and labels[index]:
                args['label'] = labels[index]
            return self.free_point(**args)

        points = (point(0), point(1), point(2))
        points[0].not_collinear_constraint(points[1], points[2])
        return points

    def height(self, triangle, vertex, **kwargs):
        """
        Height from the vertex in the triangle
        """
        assert len(triangle) == 3
        assert vertex in triangle
        points = list(triangle)
        points.remove(vertex)
        side = points[0].line_through(points[1], auxiliary=True)
        return self.perpendicular_line(side, vertex, **kwargs)

    def parallelogram(self, labels=None, auxiliary=False):
        """
        Free parallelogram
        Pass array of four strings as 'labels' to use as point labels
        Returns tuple of four points, in cyclic order
        """
        assert not labels or len(labels) == 4
        def point(index):
            args = {}
            if auxiliary:
                args['auxiliary'] = True
            if labels and labels[index]:
                args['label'] = labels[index]
            return self.free_point(**args)

        pt0 = point(0)
        pt1 = point(1)
        pt2 = point(2)
        pt0.not_collinear_constraint(pt1, pt2)
        args = {}
        if auxiliary:
            args['auxiliary'] = True
        if labels and labels[3]:
            args['label'] = labels[3]
        pt3 = self.opposite_parallelogram_point(pt1, pt0, pt2, **args)
        return (pt0, pt1, pt2, pt3)
