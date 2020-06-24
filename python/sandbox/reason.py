class Reason:
    def __init__(self, generation, comment, premises):
        self.generation = generation
        self.comment = comment
        self.premises = []
        for pre in premises:
            if pre not in self.premises:
                self.premises.append(pre)
        self.reset_premises()

    def reset_premises(self):
        self.__all_premises = None
        self.__depth = None
        self.__total_nodes = None
        self.__unique_nodes = None

    @property
    def cost(self):
        return self.unique_nodes

    @property
    def depth(self):
        if self.__depth is None:
            self.__depth = 1 + max((p.reason.depth for p in self.premises), default=0)
        return self.__depth

    @property
    def total_nodes(self):
        if self.__total_nodes is None:
            self.__total_nodes = sum((p.reason.total_nodes for p in self.premises), 1)
        return self.__total_nodes

    @property
    def unique_nodes(self):
        if self.__unique_nodes is None:
            self.__unique_nodes = len(self.all_premises)
        return self.__unique_nodes

    @property
    def all_premises(self):
        if self.__all_premises is None:
            self.__all_premises = set(self.premises)
            for p in self.premises:
                self.__all_premises.update(p.reason.all_premises)
        return self.__all_premises
