from enum import Enum, auto
import re
import sys

class Token:
    class Kind(Enum):
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
        if re.match(r'[A-Z_0-9]+', text):
            return (Token.Kind.identifier, text)
        word = text.lower()
        if word.endswith('center'):
            word = word[:-6] + 'centre'
        if word in ('triangle', 'square', 'centre', 'altitude', 'incentre', 'orthocentre', 'circumcentre', 'centroid', 'point', 'segment', 'line', 'vector', 'halfline', 'intersection'):
            return (Token.Kind.noun, word)
        if word in ('equilateral', 'non-degenerate', 'collinear', 'isosceles'):
            return (Token.Kind.adjective, word)
        if word in ('inward', 'outward', 'inside', 'outside'):
            return (Token.Kind.adverb, word)
        if word in ('of', 'in'):
            return (Token.Kind.preposition, word)
        if word in ('is', 'lies', 'are'):
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

def tokenize(string):
    tokens = [Token(elt) for elt in filter(None, re.split(r'[^a-zA-Z0-9_-]+', string))]
    if tokens:
        print(' '.join(str(t) for t in tokens))

with open(sys.argv[1]) as f:
    for line in f.readlines():
        tokenize(line)
