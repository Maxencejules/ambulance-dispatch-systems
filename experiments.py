"""Bounded offline scenarios, original-edge Bellman-Ford oracle, and provenance."""
import csv
import hashlib
import math
from pathlib import Path
import random
import config
from data_loader import load_network
from data_structures import RoadNetwork


def input_hashes():
    return {path.name: hashlib.sha256(path.read_text(encoding="utf-8-sig").encode()).hexdigest()
            for path in sorted(config.DATA_DIR.glob("*.csv"))
            if path.name != "ambulance_call_log.csv"}


def bundled():
    with config.NETWORK_FILE.open(encoding="utf-8-sig", newline="") as stream:
        edges = [(row["Start"], row["End"], float(row["Travel Time"]) + float(row["Traffic Delay"]))
                 for row in csv.DictReader(stream)]
    return load_network(), None, edges


def generated_grid(side=8, seed=2026):
    if not isinstance(side, int) or isinstance(side, bool) or not 2 <= side <= 15 or not isinstance(seed, int) or isinstance(seed, bool) or not 0 <= seed <= 2**32 - 1:
        raise ValueError("Grid requires side 2..15 and uint32 seed")
    rng, network, coordinates, edges = random.Random(seed), RoadNetwork(), {}, []
    for row in range(side):
        for column in range(side):
            node = f"r{row}c{column}"
            network.add_node(node)
            coordinates[node] = (column, row)
    for row in range(side):
        for column in range(side):
            first = f"r{row}c{column}"
            for next_row, next_column in ((row + 1, column), (row, column + 1)):
                if next_row < side and next_column < side:
                    second = f"r{next_row}c{next_column}"
                    travel, delay = 1 + rng.randrange(9) / 4, rng.randrange(4) / 4
                    network.add_edge(first, second, 1, travel, delay)
                    edges.append((first, second, travel + delay))
    return network, coordinates, edges


def reference_distances(nodes, edges, start):
    """Synchronous edge-list Bellman-Ford; does not call production search/adjacency."""
    distance = {node: math.inf for node in nodes}
    distance[start] = 0.0
    for _ in range(max(0, len(nodes) - 1)):
        updated = dict(distance)
        for first, second, cost in edges:
            updated[second] = min(updated[second], distance[first] + cost)
            updated[first] = min(updated[first], distance[second] + cost)
        if updated == distance:
            break
        distance = updated
    return distance


def check_route(path, cost, start, end, expected, edges):
    if math.isinf(expected):
        if path is not None or cost != math.inf:
            raise AssertionError("Unreachable query returned a route")
        return
    if path is None or path[0] != start or path[-1] != end or len(set(path)) != len(path):
        raise AssertionError("Invalid route endpoints or cycle")
    weights = {}
    for first, second, weight in edges:
        weights[first, second] = min(weights.get((first, second), math.inf), weight)
        weights[second, first] = min(weights.get((second, first), math.inf), weight)
    actual = math.fsum(weights.get((first, second), math.inf) for first, second in zip(path, path[1:]))
    if not math.isfinite(cost) or not math.isclose(cost, actual, rel_tol=1e-12, abs_tol=1e-10):
        raise AssertionError("Route edges do not sum to returned cost")
    if not math.isclose(cost, expected, rel_tol=1e-12, abs_tol=1e-10):
        raise AssertionError("Route differs from independent optimum")


def queries_for(network, count, seed):
    rng, nodes = random.Random(seed), sorted(network.nodes)
    return [(rng.choice(nodes), rng.choice(nodes)) for _ in range(count)]