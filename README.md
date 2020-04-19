Geometer's sandbox
==================

Solver/explainer of elementary planimetric problems.

The goal of the project is to create an app that takes a human-readable description of a planimetry problem and generates a human-readable solution.

## Current state

**Prerequisites**:

* Python 3 (tested with 3.6 and 3.7)
* Python libraries: numpy, scipy, sympy, networkx

**Python library/app prototype(s)**:

* Simple set of python functions for creating scenes ([core.py](python/sandbox/core.py), [scene.py](python/sandbox/scene.py))
* Scene placement: a simple app that takes a scene and tries to find a configuration of objects that meets all the constraints ([placement.py](python/sandbox/placement.py))
* Property hunter: a script that takes a scene placement and collects properties like “two triangles are similar” or “the ratio of two angles is integer” ([hunter.py](python/sandbox/hunter.py))
* An explainer, a simple app that takes a scene, and applies rules to prove the facts about the scene. The explainer does not adds any additional constructions nor makes assumptions to analyse separate variants ([explainer.py](python/sandbox/explainer.py))

**Tests and samples**:

* To run the tests, run `pyhton run_tests.py` in `python` folder
* The samples are assorted files in the `python` folder. Please note that some of them might be outdated. Good idea is to start from [napoleon.py](python/napoleon.py). The common command-line interface is provided bu [runner.py](python/runner.py) file that is imported in most of the samples. Run `python napoleon.py -h` for options

## Plans

**Code cleanup tasks**:

* Complete moving rules from explainer's big loop to separate classes in [sandbox/rules](python/sandbox/rules)

**Most important features to code**:

* In the explainer, introduce `ContradictionException`, that raises if the reason generates a contradiction. This is an important part of the meta explainer (see the next item)
* Meta explainer, that uses existing explainer and supports (a brut-force enumerated) additional constructions as well as assumptions (e.g., if the direct explainer fails, it might consider variants “the angle A is acute”, “is obtuse”, and “is right”)
* Generate an html presentation for explanations (a tree with expandable/collapsable nodes and hideable “non-essential” branches)

**Other features**:

* Write documentation that explains the existing code API
* Introduce a machine-readable format for tasks (or use some existing, if any; maybe GeoGebra language?)
* Make a web-based frontend (based on [JSXGraph](https://jsxgraph.uni-bayreuth.de/wp/index.html) or [GeoGebra](https://github.com/geogebra/geogebra))
* Create/collect/find a big task set in machine-readable form (using own task format, or python, or some existing format + parser)
* For each property, introduce a negated property. E.g., for “two triangles are similar”, there should be “two triangles are **not** similar”. This would be useful for detecting contradictions as soon as possible, and also for speeding up the algorithm. There is no need to test for similarity again and again on each iteration if it is already known, but also if its negation is already known. Of course, there is no need to generate all possible negated properties. Only the negations that are found in a natural way (i.e., during looking for “positive” properties) should be stored.

**Ideas, I don't know how to implement**:

* Re-write explainer rules from python into some compact language, that describes the source properties, the target property, and the matching rules

**Minor features**:

* If the idea works, re-write most important parts in a low-level language (C++?) for perfomance
