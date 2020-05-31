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
        self.__cost = None

    @property
    def cost(self):
        if self.__cost is None:
            self.__cost = len(self.all_premises)
        return self.__cost

    @property
    def all_premises(self):
        if self.__all_premises is None:
            self.__all_premises = set(self.premises)
            for p in self.premises:
                self.__all_premises.update(p.reason.all_premises)
        return self.__all_premises
