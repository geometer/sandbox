class Figure:
    pass

class Circle(Figure):
    def __init__(self, *points):
        assert len(points) >= 3
        self.points = points
        self.__key = frozenset(self.points)

    def __str__(self):
        return ('\\odot' + ' %s' * len(self.points)) % self.points

    def __eq__(self, other):
        return self.__key == other.__key

    def __hash__(self):
        return hash(self.__key)
