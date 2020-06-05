from .util import LazyComment

class Figure:
    pass

class Circle(Figure):
    def __init__(self, pt0, pt1, pt2):
        self.points = (pt0, pt1, pt2)
        self.__key = frozenset(self.points)

    def css_class(self):
        return LazyComment('circ__%s__%s__%s', *self.points)

    def __str__(self):
        return '○ %s %s %s' % self.points

    def __eq__(self, other):
        return self.__key == other.__key

    def __hash__(self):
        return hash(self.__key)
