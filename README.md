Geometer's sandbox
==================

Solver/explainer of elementary planimetric problems.

The goal of the project is to create an app that takes a human-readable description of a planimetry problem and generates a human-readable solution.

## The concept

The first step is to write an exhaustive search prover. It starts from a set of known properties and deducts new properties by applying rules from the ruleset to existing properties. This process repeats until the iteration does not generate new properties. The difference from existing provers is that the properties and the rules are defined in high-level terms like a human can use. E.g., there are properties “two angles are congruent” and “two triangles are similar”, and rule “if two pairs of angles of given triangles are congruent, the triangles are similar”.

Additionally, if the direct search fails, the prover should try some additional constructions as well as assumptions. E.g., if a proof is not found, it might consider variants “the angle A is acute”, “is obtuse”, and “is right”.

The main benefit is that the proof is immediately human-readable. And can be made even more readable by reviewing some proofs, and adding new rules/priorities.

Possible problems are
* The prover needs a large number of rules
* It is not clear how to be sure that the rule set is complete

## Current state

**Prerequisites**:

* Python 3 (tested with 3.6 and 3.7)
* Required libraries: numpy, scipy, sympy, networkx
* Optional library: matplotlib (used in the sketcher only)

**Implemented features**:

* Set of python functions for creating scenes ([core.py](python/sandbox/core.py), [scene.py](python/sandbox/scene.py))
* Scene placement: an app that takes a scene and tries to find a configuration of objects that meets all the constraints ([placement.py](python/sandbox/placement.py))
* Property hunter: a script that takes a scene placement and collects properties like “two triangles are similar” or “the ratio of two angles is integer” ([hunter.py](python/sandbox/hunter.py))
* Explainer, an app that takes a scene, and applies rules to prove the facts about the scene. The explainer does not add any additional constructions nor make assumptions to analyse separate variants ([explainer.py](python/sandbox/explainer.py))
* Web UI for explanations that shows the reason tree and a sketch of the scene. The sketch is implemented using [JSXGraph](https://jsxgraph.uni-bayreuth.de/wp/index.html). See examples in the [examples](examples) folder and `visualise_*.py` generator scripts in the [python](python) folder.
* Sketcher: a simple app that takes scene, makes several placements, selects "the best one" and plots it using matplotlib ([sketcher.py](python/sketcher.py))

**Tests and samples**:

* To run the tests, execute `pyhton run_tests.py` in `python` folder
* The samples are assorted files in the `python` folder. Please note that some of them might be outdated. Good idea is to start from [napoleon.py](python/napoleon.py). The common command-line interface is provided by [runner.py](python/runner.py) file that is imported in most of the samples. Run `python napoleon.py -h` for options

## Plans

**Most important features to code**:

* In the explainer, introduce `ContradictionException`, that raises if the reason generates a contradiction. This is an important part of the meta explainer (see the next item)
* Meta explainer that uses existing explainer and does an exhaustive search of additional constructions and assumptions

**Other features**:

* Write documentation that explains the existing code API
* Introduce a machine-readable format for tasks (or use some existing, if any; maybe GeoGebra language?)
* Create/collect/find a large task set in machine-readable form (using own task format, or python, or some existing format + parser)
* For each property, introduce a negated property. E.g., for “two triangles are similar”, there should be “two triangles are **not** similar”. This would be useful for detecting contradictions as soon as possible, and also for speeding up the algorithm. There is no need to test for similarity again and again on each iteration if it is already known, but also if its negation is already known. Of course, there is no need to generate all possible negated properties. Only the negations that are found in a natural way (i.e., during looking for “positive” properties) should be stored.
