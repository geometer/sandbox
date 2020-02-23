from .property import *

class Explainer:
    def __init__(self, scene, properties):
        self.scene = scene
        self.properties = properties
        self.explanations = {}

    def explain(self):
        for prop in self.properties:
            if isinstance(prop, CollinearProperty):
                for line in self.scene.lines():
                    if prop.A in line.all_points and prop.B in line.all_points and prop.C in line.all_points:
                        self.explanations[prop] = 'Given'
                        break

    def dump(self):
        print('Explained:')
        for prop in self.properties:
            if prop in self.explanations:
                print('\t%s [%s]' % (prop, self.explanations[prop]))
        print('\nNot explained:')
        for prop in self.properties:
            if not prop in self.explanations:
                print('\t%s' % prop)
        print('\nTotal properties: %d, explained: %d' % (len(self.properties), len(self.explanations)))
