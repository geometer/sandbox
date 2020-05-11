from enum import Enum, auto
import re
import sys

class Token:
    class Kind(Enum):
        number       = auto()
        identifier   = auto()
        article      = auto()
        noun         = auto()
        verb         = auto()
        adjective    = auto()
        adverb       = auto()
        preposition  = auto()
        conjunction  = auto()
        unknown      = auto()

        def __str__(self):
            return self.name

    @staticmethod
    def __detect(text):
        if re.match(r'[\d]+', text):
            return (Token.Kind.number, text)
        if re.match(r'[A-Z_\d]+', text):
            return (Token.Kind.identifier, text)
        word = text.lower()
        if word.endswith('center'):
            word = word[:-6] + 'centre'
        if word in ('triangle', 'square', 'centre', 'altitude', 'incentre', 'orthocentre', 'circumcentre', 'centroid', 'point', 'segment', 'line', 'vector', 'halfline', 'intersection', 'circle', 'circumcircle'):
            return (Token.Kind.noun, word)
        if word in ('equilateral', 'non-degenerate', 'collinear', 'isosceles'):
            return (Token.Kind.adjective, word)
        if word in ('inward', 'outward', 'inside', 'outside', 'acute', 'obtuse', 'right', 'not'):
            return (Token.Kind.adverb, word)
        if word in ('of', 'in', 'with'):
            return (Token.Kind.preposition, word)
        if word in ('is', 'lies', 'are', 'does', 'coincide'):
            return (Token.Kind.verb, word)
        if word in ('a', 'an', 'the'):
            return (Token.Kind.article, word)
        if word in ('and'):
            return (Token.Kind.article, word)
        return (Token.Kind.unknown, word)

    def __init__(self, text):
        self.text = text
        self.type, self.canonical = Token.__detect(text)

    def __str__(self):
        if self.type == Token.Kind.unknown:
            return '[UNKNOWN] %s' % self.text
        if self.type == Token.Kind.identifier:
            return '$%s$' % self.canonical
        if self.type in (Token.Kind.article, Token.Kind.preposition, Token.Kind.conjunction):
            return '[%s]' % self.canonical
        return self.canonical

    def __eq__(self, other):
        return self.type == other.type and self.canonical == other.canonical

    def __hash__(self):
        return hash(self.type) + hash(self.canonical)

def tokenize(string):
    return [Token(elt) for elt in filter(None, re.split(r'[^a-zA-Z0-9_º|-]+', string))]

with open(sys.argv[1]) as f:
    unknown_words = {}
    for line in f.readlines():
        tokens = tokenize(line)
        for tok in tokens:
            if tok.type == Token.Kind.unknown:
                unknown_words[tok] = unknown_words.get(tok, 0) + 1
        if tokens:
            print(' '.join(str(tok) for tok in tokens))
    print('\n%d token(s) of unknown type' % len(unknown_words))
    for tok, count in unknown_words.items():
        print('%s:\t%s' % (tok, count))
