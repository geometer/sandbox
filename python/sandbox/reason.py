class Reason:
    def __init__(self, index, generation, comments, premises):
        self.index = index
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

    def __str__(self):
        if self.premises:
            return '%s (%s)' % (
                ', '.join([str(com) for com in self.comments]),
                ', '.join(['*%d' % prop.reason.index for prop in self.premises])
            )
        else:
            return ', '.join([str(com) for com in self.comments])
