import pytest

from devlens.config.tech_prerequisite_graph import DEFAULT_TECH_PREREQUISITE_GRAPH
from devlens.domain.engines.roadmap_engine import RoadmapCycleError, RoadmapEngine

_GRAPH = {"A": [], "B": ["A"], "C": ["B"], "D": []}


def test_topological_order_respects_prerequisites() -> None:
    engine = RoadmapEngine(prerequisite_graph=_GRAPH)

    roadmap = engine.build_roadmap(["C", "B", "D", "A"])

    assert roadmap.index("A") < roadmap.index("B")
    assert roadmap.index("B") < roadmap.index("C")
    assert set(roadmap) == {"A", "B", "C", "D"}


def test_order_is_deterministic_and_ties_favor_input_order() -> None:
    engine = RoadmapEngine(prerequisite_graph=_GRAPH)

    roadmap = engine.build_roadmap(["C", "B", "D", "A"])

    assert roadmap == ["D", "A", "B", "C"]


def test_unknown_technology_is_treated_as_having_no_prerequisites() -> None:
    engine = RoadmapEngine(prerequisite_graph=_GRAPH)

    roadmap = engine.build_roadmap(["Unknown Tech", "A"])

    assert roadmap == ["Unknown Tech", "A"]


def test_prerequisite_outside_the_requested_set_is_ignored() -> None:
    engine = RoadmapEngine(prerequisite_graph=_GRAPH)

    roadmap = engine.build_roadmap(["B"])

    assert roadmap == ["B"]


def test_duplicate_technologies_are_deduplicated() -> None:
    engine = RoadmapEngine(prerequisite_graph=_GRAPH)

    roadmap = engine.build_roadmap(["A", "A", "B"])

    assert roadmap == ["A", "B"]


def test_cycle_raises_roadmap_cycle_error() -> None:
    engine = RoadmapEngine(prerequisite_graph={"A": ["B"], "B": ["A"]})

    with pytest.raises(RoadmapCycleError):
        engine.build_roadmap(["A", "B"])


def test_default_prerequisite_graph_has_no_cycles() -> None:
    engine = RoadmapEngine()

    roadmap = engine.build_roadmap(list(DEFAULT_TECH_PREREQUISITE_GRAPH.keys()))

    assert set(roadmap) == set(DEFAULT_TECH_PREREQUISITE_GRAPH.keys())
