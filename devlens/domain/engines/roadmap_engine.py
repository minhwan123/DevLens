from devlens.config.tech_prerequisite_graph import DEFAULT_TECH_PREREQUISITE_GRAPH


class RoadmapCycleError(Exception):
    """Raised if the prerequisite graph induces a cycle among the requested technologies."""


class RoadmapEngine:
    """Orders recommended technologies into a learning path via topological sort.

    The order is never hardcoded: it falls out of the prerequisite DAG in
    config/tech_prerequisite_graph.py. Adding a new technology only means adding a node/edges
    there — no engine changes needed. Technologies with no entry in the graph, or whose
    prerequisites aren't part of the given set, are treated as having no constraints.
    """

    def __init__(
        self, prerequisite_graph: dict[str, list[str]] = DEFAULT_TECH_PREREQUISITE_GRAPH
    ) -> None:
        self._graph = prerequisite_graph

    def build_roadmap(self, technologies: list[str]) -> list[str]:
        subset = list(dict.fromkeys(technologies))
        subset_set = set(subset)
        remaining_deps = {
            tech: {dep for dep in self._graph.get(tech, []) if dep in subset_set}
            for tech in subset
        }

        ordered: list[str] = []
        remaining = list(subset)
        while remaining:
            ready = next((tech for tech in remaining if not remaining_deps[tech]), None)
            if ready is None:
                raise RoadmapCycleError(f"Cycle detected among: {sorted(remaining)}")
            ordered.append(ready)
            remaining.remove(ready)
            for deps in remaining_deps.values():
                deps.discard(ready)

        return ordered
