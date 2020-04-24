class Reason:
    def __init__(self, generation, comments, premises):
        self.generation = generation
        if not isinstance(comments, (list, tuple)):
            self.comments = [comments]
        else:
            self.comments = list(comments)
        self.premises = premises
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
