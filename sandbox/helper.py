from .core import CoreScene

class PlacementHelper:
    def __init__(self, placement):
        self.placement = placement

    def distance(self, point0, point1):
        if isinstance(point0, str):
            point0 = self.placement.scene.get(point0)
        if isinstance(point1, str):
            point1 = self.placement.scene.get(point1)

        assert isinstance(point0, CoreScene.Point), 'Parameter is not a point'
        assert isinstance(point1, CoreScene.Point), 'Parameter is not a point'

        return self.placement.length(point0.vector(point1))

    def angle(self, pt0, pt1, pt2, pt3):
        """Angle between vectors (pt0, pt1) and (pt2, pt3)"""
        if isinstance(pt0, str):
            pt0 = self.placement.scene.get(pt0)
        if isinstance(pt1, str):
            pt1 = self.placement.scene.get(pt1)
        if isinstance(pt2, str):
            pt2 = self.placement.scene.get(pt2)
        if isinstance(pt3, str):
            pt3 = self.placement.scene.get(pt3)

        assert isinstance(pt0, CoreScene.Point), 'Parameter is not a point'
        assert isinstance(pt1, CoreScene.Point), 'Parameter is not a point'
        assert isinstance(pt2, CoreScene.Point), 'Parameter is not a point'
        assert isinstance(pt3, CoreScene.Point), 'Parameter is not a point'

        return self.placement.angle(pt0.vector(pt1), pt2.vector(pt3))
