import itertools

class PropertySet:
    class ByType:
        def __init__(self):
            self.all = []
            self.by_key_map = {}

    def __init__(self):
        self.by_type_map = {}
        self.__full_set = {}

    def add(self, prop):
        key = type(prop)
        by_type = self.by_type_map.get(key)
        if by_type is None:
            by_type = PropertySet.ByType()
            self.by_type_map[key] = by_type
        by_type.all.append(prop)
        for key in prop.keys():
            arr = by_type.by_key_map.get(key)
            if arr is None:
                by_type.by_key_map[key] = [prop]
            else:
                arr.append(prop)
        self.__full_set[prop] = prop

    def list(self, property_type, keys=None):
        by_type = self.by_type_map.get(property_type)
        if not by_type:
            return []
        if keys:
            assert isinstance(keys, list)
            if len(keys) == 1:
                lst = by_type.by_key_map.get(keys[0])
                return list(lst) if lst else []
            sublists = [by_type.by_key_map.get(k) for k in keys]
            return list(set(itertools.chain(*[l for l in sublists if l])))
        else:
            return list(by_type.all)

    def __len__(self):
        return len(self.__full_set)

    @property
    def all(self):
        return list(self.__full_set)

    def __contains__(self, prop):
        return prop in self.__full_set

    def __getitem__(self, prop):
        return self.__full_set.get(prop)

    def keys_num(self):
        return sum(len(by_type.by_key_map) for by_type in self.by_type_map.values())

    def copy(self):
        copy = PropertySet()
        for prop in self.all:
            copy.add(prop)
        return copy
