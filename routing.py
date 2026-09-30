"""Dijkstra is best-first search with h=0; A* supplies consistent lower bounds."""
import heapq
import itertools
import math
from data_structures import RoadNetwork


def validate_endpoints(network, start, end):
    if not isinstance(network, RoadNetwork):
        raise ValueError("A RoadNetwork must be loaded")
    if not isinstance(start, str) or not isinstance(end, str) or start not in network.nodes or end not in network.nodes:
        raise ValueError("Start and destination must be known network nodes")


def best_first(network, start, end, estimates=None):
    """Return path, float cost, and non-goal expansions. Never hide overflow."""
    validate_endpoints(network, start, end)
    if start == end:
        return [start], 0.0, 0
    counter = itertools.count()
    distance, parent = {start: 0.0}, {}
    initial = 0.0 if estimates is None else estimates[start]
    heap = [(initial, 0.0, next(counter), start)]
    expanded = 0
    while heap:
        _, queued_cost, _, node = heapq.heappop(heap)
        if queued_cost != distance[node]:
            continue  # superseded entry; every improved g pushes a fresh priority
        if node == end:
            path = [end]
            while path[-1] != start:
                path.append(parent[path[-1]])
            return path[::-1], queued_cost, expanded
        expanded += 1
        for neighbor, cost in network.get_neighbors(node):
            candidate = queued_cost + cost
            if not math.isfinite(candidate):
                raise OverflowError("Route cost overflow")
            if candidate < distance.get(neighbor, math.inf):
                remaining = 0.0 if estimates is None else estimates[neighbor]
                priority = candidate + remaining
                if not math.isfinite(priority):
                    raise OverflowError("Search priority overflow")
                distance[neighbor], parent[neighbor] = candidate, node
                heapq.heappush(heap, (priority, candidate, next(counter), neighbor))
    return None, math.inf, expanded