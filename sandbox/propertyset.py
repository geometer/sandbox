import itertools

from .property import AngleValueProperty, AnglesRatioProperty, LengthsRatioProperty, PointsCoincidenceProperty, PointsCollinearityProperty

class PropertySet:
    def __init__(self):
        self.__combined = {} # (type, key) => [prop] and type => prop
        self.__full_set = {} # prop => prop
        self.__angle_values = {} # angle => prop
        self.__angle_ratios = {} # {angle, angle} => prop
        self.__length_ratios = {} # {segment, segment} => prop
        self.__coincidence = {} # {point, point} => prop
        self.__collinearity = {} # {point, point, point} => prop

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

    def lengths_ratio_property(self, segment0, segment1):
        return self.__length_ratios.get(frozenset([segment0, segment1]))

    def intersection_of_lines(self, segment0, segment1):
        ne0 = self.not_equal_property(*segment0.points)
        if ne0 is None:
            return (None, [])
        ne1 = self.not_equal_property(*segment1.points)
        if ne1 is None:
            return (None, [])

        try:
            return (next(pt for pt in segment0.points if pt in segment1.points), [ne0, ne1])
        except StopIteration:
            pass

        first_list = [p for p in self.list(PointsCollinearityProperty, [segment0]) if p.collinear]
        second_list = [p for p in self.list(PointsCollinearityProperty, [segment1]) if p.collinear]
        if len(first_list) == 0:
            for col in second_list:
                try:
                    return (next(pt for pt in segment0.points if pt in col.points), [col, ne0, ne1])
                except StopIteration:
                    pass
        elif len(second_list) == 0:
            for col in first_list:
                try:
                    return (next(pt for pt in segment1.points if pt in col.points), [col, ne0, ne1])
                except StopIteration:
                    pass
        else:
            for col0 in first_list:
                for col1 in second_list:
                    try:
                        return (next(pt for pt in col0.points if pt in col1.points), [col0, col1, ne0, ne1])
                    except StopIteration:
                        pass
        return (None, [])

    def keys_num(self):
        return len(self.__combined)

    def copy(self):
        copy = PropertySet()
        for prop in self.all:
            copy.add(prop)
        return copy
