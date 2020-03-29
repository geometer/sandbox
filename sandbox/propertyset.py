import itertools
import networkx as nx

from .property import AngleValueProperty, AnglesRatioProperty, LengthsRatioProperty, PointsCoincidenceProperty, PointsCollinearityProperty, EqualLengthsRatiosProperty
from .reason import Reason
from .stats import Stats
from .util import _comment, divide

class ELRPropertySet:
    class Family:
        def __init__(self):
            self.ratio_set = set()
            self.premises_graph = nx.Graph()

        def add_ratio(self, ratio):
            if ratio is self.ratio_set:
                return
            if tuple(reversed(ratio)) in self.ratio_set:
                for r in list(self.ratio_set):
                    self.ratio_set.add(tuple(reversed(r)))
            else:
                self.ratio_set.add(ratio)

        def add_property(self, prop):
            segs = prop.segments
            self.premises_graph.add_edge((segs[0], segs[1]), (segs[2], segs[3]), prop=prop)
            self.premises_graph.add_edge((segs[1], segs[0]), (segs[3], segs[2]), prop=prop)
            self.premises_graph.add_edge((segs[0], segs[2]), (segs[1], segs[3]), prop=prop)
            self.premises_graph.add_edge((segs[2], segs[0]), (segs[3], segs[1]), prop=prop)

        def find_ratio(self, ratio):
            if ratio in self.ratio_set:
                return 1
            if tuple(reversed(ratio)) in self.ratio_set:
                return -1
            return 0

        def explanation(self, ratio0, ratio1):
            if ratio0 not in self.ratio_set:
                return (None, None)
            if ratio1 not in self.ratio_set:
                return (None, None)
            path = nx.algorithms.shortest_path(self.premises_graph, ratio0, ratio1)
            pattern = ' = '.join(['|%s| / |%s|'] * len(path))
            comment = _comment(pattern, *sum(path, ()))
            premises = [self.premises_graph[i][j]['prop'] for i, j in zip(path[:-1], path[1:])]
            return (comment, premises)

    def __init__(self):
        self.families = []

    def __find_family(self, ratio):
        for fam in self.families:
            found = fam.find_ratio(ratio)
            if found != 0:
                return (fam, found == 1)
        return (None, None)

    def __add(self, ratio0, ratio1, prop):
        fam0, order0 = self.__find_family(ratio0)
        fam1, order1 = self.__find_family(ratio1)
        if fam0 and fam1:
            if fam0 == fam1:
                if order0 != order1:
                    for ratio in list(fam0.ratio_set):
                        fam0.add_ratio(tuple(reversed(ratio)))
            else:
                if order0 == order1:
                    fam0.ratio_set.update(fam1.ratio_set)
                else:
                    for ratio in fam1.ratio_set:
                        fam0.add_ratio(tuple(reversed(ratio)))
                fam0.premises_graph.add_edges_from(fam1.premises_graph.edges)
                for v0, v1 in fam1.premises_graph.edges:
                    fam0.premises_graph[v0][v1].update(fam1.premises_graph[v0][v1])
                self.families.remove(fam1)
            fam0.add_property(prop)
        elif fam0:
            fam0.add_ratio(ratio1 if order0 else tuple(reversed(ratio1)))
            if order0 and tuple(reversed(ratio0)) in fam0.ratio_set:
                fam0.add_ratio(tuple(reversed(ratio1)))
            fam0.add_property(prop)
        elif fam1:
            fam1.add_ratio(ratio0 if order1 else tuple(reversed(ratio0)))
            if order1 and tuple(reversed(ratio1)) in fam1.ratio_set:
                fam1.add_ratio(tuple(reversed(ratio0)))
            fam1.add_property(prop)
        else:
            fam = ELRPropertySet.Family()
            fam.add_ratio(ratio0)
            fam.add_ratio(ratio1)
            fam.add_property(prop)
            self.families.append(fam)

    def __contains(self, ratio0, ratio1):
        fam, order = self.__find_family(ratio0)
        if fam is None:
            return False
        if order:
            return ratio1 in fam.ratio_set
        return tuple(reversed(ratio1)) in fam.ratio_set

    def add(self, prop):
        self.__add(prop.segments[0:2], prop.segments[2:4], prop)
        self.__add((prop.segments[0], prop.segments[2]), (prop.segments[1], prop.segments[3]), prop)

    def explanation(self, ratio0, ratio1):
        fam, order = self.__find_family(ratio0)
        if fam is None:
            return (None, None)
        if order:
            return fam.explanation(ratio0, ratio1)
        return fam.explanation(tuple(reversed(ratio0)), tuple(reversed(ratio1)))

    def __contains__(self, prop):
        return self.__contains(prop.segments[0:2], prop.segments[2:4]) or \
            self.__contains((prop.segments[0], prop.segments[2]), (prop.segments[1], prop.segments[3]))

class PropertySet:
    def __init__(self):
        self.__combined = {} # (type, key) => [prop] and type => prop
        self.__full_set = {} # prop => prop
        self.__angle_values = {} # angle => prop
        self.__angle_ratios = {} # {angle, angle} => prop
        self.__length_ratios = {} # {segment, segment} => prop
        self.__elrs = ELRPropertySet()
        self.__coincidence = {} # {point, point} => prop
        self.__collinearity = {} # {point, point, point} => prop
        self.__intersections = {} # {segment, segment} => point, [reasons]

    def add(self, prop):
        def put(key):
            lst = self.__combined.get(key)
            if lst:
                lst.append(prop)
            else:
                self.__combined[key] = [prop]

        type_key = type(prop)
        put(type_key)
        for key in prop.keys():
            put((type_key, key))
        self.__full_set[prop] = prop
        if type_key == AngleValueProperty:
            self.__angle_values[prop.angle] = prop
        elif type_key == AnglesRatioProperty:
            self.__angle_ratios[prop.angle_set] = prop
        elif type_key == LengthsRatioProperty:
            self.__length_ratios[prop.segment_set] = prop
        elif type_key == PointsCoincidenceProperty:
            self.__coincidence[prop.point_set] = prop
        elif type_key == PointsCollinearityProperty:
            self.__collinearity[prop.point_set] = prop
        elif type_key == EqualLengthsRatiosProperty:
            self.__elrs.add(prop)

    def unitary_ratios(self):
        for fam in self.__elrs.families:
            for ratio0, ratio1 in itertools.combinations(fam.ratio_set, 2):
                if ratio0[0] == ratio1[0]:
                    yield (ratio0[1], ratio1[1], *fam.explanation(ratio0, ratio1))
                elif ratio0[1] == ratio1[1]:
                    yield (ratio0[0], ratio1[0], *fam.explanation(ratio0, ratio1))

    def list(self, property_type, keys=None):
        if keys:
            assert isinstance(keys, list)
            if len(keys) == 1:
                lst = self.__combined.get((property_type, keys[0]))
                return list(lst) if lst else []
            sublists = [self.__combined.get((property_type, k)) for k in keys]
            return list(set(itertools.chain(*[l for l in sublists if l])))
        else:
            lst = self.__combined.get(property_type)
            return list(lst) if lst else []

    def __len__(self):
        return len(self.__full_set)

    @property
    def all(self):
        return list(self.__full_set)

    def __contains__(self, prop):
        return prop in self.__full_set

    def __getitem__(self, prop):
        return self.__full_set.get(prop)

    def collinearity_property(self, pt0, pt1, pt2):
        return self.__collinearity.get(frozenset([pt0, pt1, pt2]))

    def not_collinear_property(self, pt0, pt1, pt2):
        prop = self.__collinearity.get(frozenset([pt0, pt1, pt2]))
        return prop if prop and not prop.collinear else None

    def not_equal_property(self, pt0, pt1):
        prop = self.__coincidence.get(frozenset([pt0, pt1]))
        return prop if prop and not prop.coincident else None

    def angle_value_property(self, angle):
        return self.__angle_values.get(angle)

    def angles_ratio_property(self, angle0, angle1):
        return self.__angle_ratios.get(frozenset([angle0, angle1]))

    def lengths_ratio_property_and_value(self, segment0, segment1):
        prop = self.__length_ratios.get(frozenset([segment0, segment1]))
        if prop is None:
            return (None, None)
        return (prop, prop.ratio if prop.segment0 == segment0 else divide(1, prop.ratio))

    def congruent_segments_property(self, segment0, segment1):
        prop = self.__length_ratios.get(frozenset([segment0, segment1]))
        return prop if prop and prop.ratio == 1 else None

    def equal_length_ratios_property(self, segment0, segment1, segment2, segment3):
        prop = EqualLengthsRatiosProperty(segment0, segment1, segment2, segment3)
        existing = self[prop]
        if existing:
            return existing
        if prop in self.__elrs:
            prop.reason = Reason(-2, -2, *self.__elrs.explanation((segment0, segment1), (segment2, segment3)))
            prop.reason.obsolete = False
            return prop

    def intersection_of_lines(self, segment0, segment1):
        key = frozenset([segment0, segment1])
        value = self.__intersections.get(key)
        if value is None:
            value = self.__intersection_of_lines(segment0, segment1)
            if value:
                self.__intersections[key] = value
        return value

    def __intersection_of_lines(self, segment0, segment1):
        common = next((pt for pt in segment0.points if pt in segment1.points), None)
        if common:
            return (common, [])

        for index in range(0, 2):
            col = self.collinearity_property(*segment0.points, segment1.points[index])
            if col and col.collinear:
                return (segment1.points[index], [col])
            col = self.collinearity_property(*segment1.points, segment0.points[index])
            if col and col.collinear:
                return (segment0.points[index], [col])

        first_list = [p for p in self.list(PointsCollinearityProperty, [segment0]) if p.collinear]
        if first_list:
            second_list = [p for p in self.list(PointsCollinearityProperty, [segment1]) if p.collinear]
            for col0 in first_list:
                for col1 in second_list:
                    common = next((pt for pt in col0.points if pt in col1.points), None)
                    if common:
                        return (common, [col0, col1])
        return (None, [])

    def stats(self):
        def type_presentation(kind):
            return kind.__doc__.strip() if kind.__doc__ else kind.__name__

        by_type = {}
        for prop in self.all:
            key = type(prop)
            by_type[key] = by_type.get(key, 0) + 1
        by_type = [(type_presentation(k), v) for k, v in by_type.items()]
        by_type.sort(key=lambda pair: -pair[1])
        others = []
        others.append(('ELR families count', len(self.__elrs.families)))
        others.append(('ELR count', sum(len(f.ratio_set) for f in self.__elrs.families)))
        return Stats(by_type + others)

    def keys_num(self):
        return len(self.__combined)
