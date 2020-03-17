class Reason:
    def __init__(self, index, generation, comments, premises):
        self.index = index
        self.generation = generation
        if not isinstance(comments, (list, tuple)):
            self.comments = [comments]
        else:
            self.comments = list(comments)
        self.premises = premises

    def __str__(self):
        if self.premises:
            return '%s (%s)' % (
                ', '.join([str(com) for com in self.comments]),
                ', '.join(['*%d' % prop.reason.index for prop in self.premises])
            )
        else:
            return ', '.join([str(com) for com in self.comments])
