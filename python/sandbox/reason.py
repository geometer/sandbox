class Reason:
    def __init__(self, generation, comment, premises):
        self.generation = generation
        self.comment = comment
        self.premises = []
        for pre in premises:
            if pre not in self.premises:
                self.premises.append(pre)
        self.__all_premises = None

    def reset_premises(self):
        self.__all_premises = None
        
    @property
    def all_premises(self):
        if self.__all_premises is None:
            self.__all_premises = set()
            if self.premises is not None:
                for p in self.premises:
                    if not p in self.__all_premises:
                        self.__all_premises.add(p)
                        self.__all_premises.update(p.reason.all_premises)
        return self.__all_premises
