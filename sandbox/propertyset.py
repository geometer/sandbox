import itertools
import networkx as nx

from .property import AngleValueProperty, AnglesRatioProperty, LengthRatioProperty, PointsCoincidenceProperty, PointsCollinearityProperty, EqualLengthRatiosProperty, SameCyclicOrderProperty
from .reason import Reason
from .stats import Stats
from .util import _comment, divide

class CyclicOrderPropertySet:
    class Family:
        def __init__(self):
            self.cycle_set = set()
            self.premises_graph = nx.Graph()

        def explanation(self, cycle0, cycle1):
            if cycle0 not in self.cycle_set or cycle1 not in self.cycle_set:
                return (None, None)

            path = nx.algorithms.shortest_path(self.premises_graph, cycle0, cycle1)
            pattern = ' = '.join(['%s'] * len(path))
            comment = _comment(pattern, *path)
            premises = [self.premises_graph[i][j]['prop'] for i, j in zip(path[:-1], path[1:])]
            return (comment, premises)

    def __init__(self):
        self.families = []

    def __find_by_cycle(self, cycle):
        for fam in self.families:
            if cycle in fam.cycle_set:
                return (fam, True)
            if cycle.reversed in fam.cycle_set:
                return (fam, False)
        return (None, None)

    def add(self, prop):
        fam0, order0 = self.__find_by_cycle(prop.cycle0)
        fam1, order1 = self.__find_by_cycle(prop.cycle1)
        if fam0 and fam1:
            if fam0 == fam1:
                # TODO: better way to report contradiction
                assert order0 == order1, 'Contradiction'
            else:
                if order0 == order1:
                    fam0.cycle_set.update(fam1.cycle_set)
                else:
                    for cycle in fam1.cycle_set:
                        fam0.cycle_set.add(cycle.reversed)
                fam0.premises_graph.add_edges_from(fam1.premises_graph.edges)
                for v0, v1 in fam1.premises_graph.edges:
                    fam0.premises_graph[v0][v1].update(fam1.premises_graph[v0][v1])
                self.families.remove(fam1)
            fam = fam0
        elif fam0:
            fam0.cycle_set.add(prop.cycle1 if order0 else prop.cycle1.reversed)
            fam = fam0
        elif fam1:
            fam1.cycle_set.add(prop.cycle0 if order1 else prop.cycle0.reversed)
            fam = fam1
        else:
            fam = CyclicOrderPropertySet.Family()
            fam.cycle_set.add(prop.cycle0)
            fam.cycle_set.add(prop.cycle1)
            self.families.append(fam)
        fam.premises_graph.add_edge(prop.cycle0, prop.cycle1, prop=prop)
        fam.premises_graph.add_edge(prop.cycle0.reversed, prop.cycle1.reversed, prop=prop)

    def explanation(self, cycle0, cycle1):
        fam, order = self.__find_by_cycle(cycle0)
        if fam is None:
            return (None, None)
        if order:
            return fam.explanation(cycle0, cycle1)
        return fam.explanation(cycle0.reversed, cycle1.reversed)

class LengthRatioPropertySet:
    class Family:
        def __init__(self):
            self.ratio_value = None
            self.ratio_set = set()
            self.premises_graph = nx.Graph()

        def add_ratio(self, ratio):
            if ratio is self.ratio_set:
                return
            if tuple(reversed(ratio)) in self.ratio_set:
                self.symmetrize()
            else:
                self.ratio_set.add(ratio)

        def symmetrize(self):
            for ratio in list(self.ratio_set):
                self.ratio_set.add(tuple(reversed(ratio)))

        def merge(self, other, inverse):
            if self.ratio_value is not None:
                # TODO: better way to report contradiction
                if other.ratio_value is not None:
                    value = divide(1, self.ratio_value) if inverse else self.ratio_value
                    assert other.ratio_value == value, 'Contradiction'
            elif other.ratio_value is not None:
                self.ratio_value = divide(1, other.ratio_value) if inverse else other.ratio_value

            if inverse:
                for ratio in other.ratio_set:
                    self.add_ratio(tuple(reversed(ratio)))
            else:
                self.ratio_set.update(other.ratio_set)
            self.premises_graph.add_edges_from(other.premises_graph.edges)
            for v0, v1 in other.premises_graph.edges:
                self.premises_graph[v0][v1].update(other.premises_graph[v0][v1])

        def add_property(self, prop):
            if isinstance(prop, EqualLengthRatiosProperty):
                segs = prop.segments
                self.premises_graph.add_edge((segs[0], segs[1]), (segs[2], segs[3]), prop=prop)
                self.premises_graph.add_edge((segs[1], segs[0]), (segs[3], segs[2]), prop=prop)
                self.premises_graph.add_edge((segs[0], segs[2]), (segs[1], segs[3]), prop=prop)
                self.premises_graph.add_edge((segs[2], segs[0]), (segs[3], segs[1]), prop=prop)
            elif isinstance(prop, LengthRatioProperty):
                if prop.value == 1:
                    self.symmetrize()
                reciprocal = divide(1, prop.value)
                ratio = (prop.segment0, prop.segment1)
                inversed = tuple(reversed(ratio))
                if ratio in self.ratio_set:
                    if inversed in self.ratio_set:
                        # TODO: better way to report contradiction
                        assert prop.value == 1, 'Contradiction'
                    if self.ratio_value is None:
                        self.ratio_value = prop.value
                    else:
                        # TODO: better way to report contradiction
                        assert prop.value == self.ratio_value, 'Contradiction'
                else: #inversed in self.ratio_set
                    if self.ratio_value is None:
                        self.ratio_value = reciprocal
                    else:
                        # TODO: better way to report contradiction
                        assert reciprocal == self.ratio_value, 'Contradiction: %s != %s' % (reciprocal, self.ratio_value)

                self.premises_graph.add_edge(ratio, (prop.value, ), prop=prop)
                self.premises_graph.add_edge(inversed, (reciprocal, ), prop=prop)

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
            pattern = ' = '.join(['|%s| / |%s|' if len(v) == 2 else '%s' for v in path])
            comment = _comment(pattern, *sum(path, ()))
            premises = [self.premises_graph[i][j]['prop'] for i, j in zip(path[:-1], path[1:])]
            return (comment, premises)

    def __init__(self):
        self.families = []

    def __find_by_ratio(self, ratio):
        for fam in self.families:
            found = fam.find_ratio(ratio)
            if found != 0:
                return (fam, found == 1)
        return (None, None)

    def __find_by_value(self, value):
        reciprocal = divide(1, value)
        for fam in self.families:
            if fam.ratio_value is None:
                continue
            if fam.ratio_value == value:
                return (fam, True)
            if fam.ratio_value == reciprocal:
                return (fam, False)
        return (None, None)

    def __add_lr(self, prop):
        ratio = (prop.segment0, prop.segment1)
        fam0, order0 = self.__find_by_ratio(ratio)
        fam1, order1 = self.__find_by_value(prop.value)
        if fam0 and fam1:
            if fam0 == fam1:
                fam0.add_property(prop)
            else:
                fam0.merge(fam1, order0 != order1)
                self.families.remove(fam1)
        elif fam0:
            fam0.add_property(prop)
        elif fam1:
            fam1.add_ratio(ratio if order1 else tuple(reversed(ratio)))
            fam1.add_property(prop)
        else:
            fam = LengthRatioPropertySet.Family()
            fam.add_ratio(ratio)
            fam.add_property(prop)
            self.families.append(fam)

    def __add_elr(self, ratio0, ratio1, prop):
        fam0, order0 = self.__find_by_ratio(ratio0)
        fam1, order1 = self.__find_by_ratio(ratio1)
        if fam0 and fam1:
            if fam0 == fam1:
                if order0 != order1:
                    fam0.symmetrize()
            else:
                fam0.merge(fam1, order0 != order1)
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
            fam = LengthRatioPropertySet.Family()
            fam.add_ratio(ratio0)
            fam.add_ratio(ratio1)
            fam.add_property(prop)
            self.families.append(fam)

    def add(self, prop):
        if isinstance(prop, EqualLengthRatiosProperty):
            self.__add_elr(prop.segments[0:2], prop.segments[2:4], prop)
            self.__add_elr((prop.segments[0], prop.segments[2]), (prop.segments[1], prop.segments[3]), prop)
        elif isinstance(prop, LengthRatioProperty):
            self.__add_lr(prop)

    def explanation(self, ratio0, ratio1):
        fam, order = self.__find_by_ratio(ratio0)
        if fam is None:
            return (None, None)
        if order:
            return fam.explanation(ratio0, ratio1)
        return fam.explanation(tuple(reversed(ratio0)), tuple(reversed(ratio1)))

class PropertySet:
    def __init__(self):
        self.__combined = {} # (type, key) => [prop] and type => prop
        self.__full_set = {} # prop => prop
        self.__angle_values = {} # angle => prop
        self.__angle_ratios = {} # {angle, angle} => prop
        self.__length_ratios = {} # {segment, segment} => prop
        self.__elrs = LengthRatioPropertySet()
        self.__cyclic_orders = CyclicOrderPropertySet()
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
        elif type_key == LengthRatioProperty:
            self.__length_ratios[prop.segment_set] = prop
            self.__elrs.add(prop)
        elif type_key == PointsCoincidenceProperty:
            self.__coincidence[prop.point_set] = prop
        elif type_key == PointsCollinearityProperty:
            self.__collinearity[prop.point_set] = prop
        elif type_key == EqualLengthRatiosProperty:
            self.__elrs.add(prop)
        elif type_key == SameCyclicOrderProperty:
            self.__cyclic_orders.add(prop)

    def length_ratios_equal_to_one(self):
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
        return (prop, prop.value if prop.segment0 == segment0 else divide(1, prop.value))

    def congruent_segments_property(self, segment0, segment1):
        prop = self.__length_ratios.get(frozenset([segment0, segment1]))
        return prop if prop and prop.value == 1 else None

    def equal_length_ratios_property(self, segment0, segment1, segment2, segment3):
        prop = EqualLengthRatiosProperty(segment0, segment1, segment2, segment3)
        existing = self[prop]
        if existing:
            return existing
        comment, premises = self.__elrs.explanation((segment0, segment1), (segment2, segment3))
        # this is a hack TODO: add symmetric properties during adding LengthRatioProperty
        if comment is None:
            comment, premises = self.__elrs.explanation((segment0, segment2), (segment1, segment3))
        if comment is None:
            return None
        prop.reason = Reason(-2, -2, comment, premises)
        prop.reason.obsolete = False
        return prop

    def same_cyclic_order_property(self, cycle0, cycle1):
        prop = SameCyclicOrderProperty(cycle0, cycle1)
        existing = self[prop]
        if existing:
            return existing
        comment, premises = self.__cyclic_orders.explanation(cycle0, cycle1)
        if comment:
            prop.reason = Reason(-2, -2, comment, premises)
            prop.reason.obsolete = False
            return prop
        return None

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
        return Stats(by_type + others)

    def keys_num(self):
        return len(self.__combined)
