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

    def orthocentre_point(self, triangle, **kwargs):
        """
        Orthocentre of the triangle (intersection of the altitudes)
        """
        self.__is_triangle(triangle)
        altitude0 = self.altitude(triangle, triangle[0], auxiliary=True)
        altitude1 = self.altitude(triangle, triangle[1], auxiliary=True)
        centre = altitude0.intersection_point(altitude1, **kwargs)
        altitude2 = self.altitude(triangle, triangle[2], auxiliary=True)
        centre.belongs_to(altitude2)
        return centre

    def circumcentre_point(self, triangle, **kwargs):
        """
        Circumcentre of the triangle (perpendicular bisectors intersection point)
        """
        self.__is_triangle(triangle)
        bisector0 = self.perpendicular_bisector_line(triangle[1], triangle[2], auxiliary=True)
        bisector1 = self.perpendicular_bisector_line(triangle[0], triangle[2], auxiliary=True)
        centre = bisector0.intersection_point(bisector1, **kwargs)
        bisector2 = self.perpendicular_bisector_line(triangle[0], triangle[1], auxiliary=True)
        centre.belongs_to(bisector2)
        return centre

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

    def angle_bisector_line(self, vertex, B, C, **kwargs):
        """
        The bisector of ∠ B vertex C
        """
        self.assert_point(vertex)
        self.assert_point(B)
        self.assert_point(C)
        vertex.not_equal_constraint(B)
        vertex.not_equal_constraint(C)
        circle = vertex.circle_through(B, auxiliary=True)
        line = vertex.line_through(C, auxiliary=True)
        X = circle.intersection_point(line, auxiliary=True)
        vertex.same_direction_constraint(X, C)
        Y = X.ratio_point(B, 1, 1, auxiliary=True)
        return vertex.line_through(Y, **kwargs)

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
        perpendicular.perpendicular_constraint(line, guaranteed=True)
        return perpendicular

    def incentre_point(self, triangle, **kwargs):
        """
        Centre of the inscribed circle of the triangle
        """
        self.__is_triangle(triangle)
        bisector0 = self.angle_bisector_line(triangle[0], triangle[1], triangle[2], auxiliary=True)
        bisector1 = self.angle_bisector_line(triangle[1], triangle[0], triangle[2], auxiliary=True)
        centre = bisector0.intersection_point(bisector1, **kwargs)
        bisector2 = self.angle_bisector_line(triangle[2], triangle[0], triangle[1], auxiliary=True)
        centre.belongs_to(bisector2)
        return centre

    def incircle(self, triangle, **kwargs):
        """
        Inscribed circle of △ABC
        """
        centre = self.incentre_point(triangle, auxiliary=True)
        side = triangle[0].line_through(triangle[1], auxiliary=True)
        foot = self.perpendicular_foot_point(centre, side, auxiliary=True)
        return centre.circle_through(foot, **kwargs)

    def circumcircle(self, triangle, **kwargs):
        """
        Circumscribed circle of the triangle
        """
        centre = self.circumcentre_point(triangle, auxiliary=True)
        return centre.circle_through(triangle[0], **kwargs)

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

    def __is_triangle(self, triangle):
        assert len(triangle) == 3
        for pt in triangle:
            self.assert_point(pt)
        triangle[0].not_collinear_constraint(triangle[1], triangle[2])

    def altitude(self, triangle, vertex, **kwargs):
        """
        Height from the vertex in the triangle
        """
        if isinstance(triangle, CoreScene.Point):
            triangle, vertex = vertex, triangle
        self.__is_triangle(triangle)
        assert vertex in triangle
        points = list(triangle)
        points.remove(vertex)
        base = points[0].line_through(points[1], auxiliary=True)
        altitude = self.perpendicular_line(base, vertex, **kwargs)
        altitude.perpendicular_constraint(base, comment='Altitude is perpendicular to the base', guaranteed=True)
        return altitude

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
