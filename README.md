Geometer's Sandbox
==================

Solver/explainer of elementary planimetric problems.

The goal of the project is to create an app that takes a human-readable description of a planimetry problem and generates a human-readable solution.

## Web demos

Live demos are available on [the project site](https://sandbox.geometer.name/). No way to enter your own problem at the moment, the site generates visualisations and solutions for a set of selected problems.

## The concept

The first step is to write an exhaustive search prover. It starts from a set of known properties and deducts new properties by applying rules from the ruleset to existing ones. This process repeats until the iteration stops to generate properties.

Additionally, if the direct search fails, the prover should try some additional constructions as well as assumptions. E.g., if a proof is not found, it might consider variants “the angle A is acute”, “is obtuse”, and “is right”.

The difference from existing provers is that the properties and the rules are defined in high-level terms like a human can use. E.g., there are properties “two angles are congruent” and “two triangles are similar”, and rule “if two pairs of angles of given triangles are congruent, the triangles are similar”. To be clear: there is no translation to “low-level” logical notation even inside the code.

The main benefit is that the proof is immediately human-readable. And can be made even more readable by reviewing some proofs, and adding new rules/priorities.

Possible problems are
* The prover needs a large number of rules
* It is not clear how to be sure that the rule set is complete

## Current state

**Prerequisites**:

* Python 3 (tested with 3.6 and 3.7)
* Required libraries: numpy, scipy, sympy, networkx

**Implemented features**:

* Set of python functions for creating scenes ([core.py](python/sandbox/core.py), [scene.py](python/sandbox/scene.py))
* Scene placement: an app that takes a scene and tries to find a configuration of objects that meets all the constraints ([placement.py](python/sandbox/placement.py))
* Property hunter: a script that takes a scene placement and collects properties like “two triangles are similar” or “the ratio of two angles is integer” ([hunter.py](python/sandbox/hunter.py))
* Explainer, an app that takes a scene, and applies rules to prove the facts about the scene. The explainer does not add any additional constructions nor make assumptions to analyse separate variants ([explainer.py](python/sandbox/explainer.py))
* Web UI for explanations that shows the reason tree and a sketch of the scene. The sketch is implemented using [JSXGraph](https://jsxgraph.uni-bayreuth.de/wp/index.html). See examples in the [examples](examples) folder and `visualise_*.py` generator scripts in the [python](python) folder.

**Tests and samples**:

* To run the tests, execute `pyhton run_tests.py` in `python` folder
* The samples are assorted files in the `python` folder. Please note that some of them might be outdated. Good idea is to start from [napoleon.py](python/napoleon.py). The common command-line interface is provided by [runner.py](python/runner.py) file that is imported in most of the samples. Run `python napoleon.py -h` for options

## Plans

Please refer [the issues tracker](https://github.com/geometer/sandbox/issues) to browse planned features, ideas, etc.
