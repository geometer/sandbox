"""
This module is to be extended in the future to add more construction methods.
"""

from .core import CoreScene, Constraint

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
        fourth = self.opposite_parallelogram_point(point, line.point0, line.point1, auxiliary=True)
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
        tmp2.add_constraint(Constraint.Kind.not_equal, tmp)
        return tmp.ratio_point(tmp2, 1, 1, **kwargs)
