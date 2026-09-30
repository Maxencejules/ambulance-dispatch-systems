"""A* with a scaled Manhattan lower bound, validated at each graph revision."""
import math
import sys
from dispatcher import Dispatcher
from routing import best_first, validate_endpoints


class AStarDispatcher(Dispatcher):
    algorithm = "astar"

    def __init__(self, network=None, *, coordinates=None, **kwargs):
        super().__init__(network, **kwargs)
        self._supplied_coordinates = None if coordinates is None else dict(coordinates)
        self.coordinates = {}
        self.min_edge_cost = 0.0
        self.heuristic_scale = 0.0
        self._revision = None
        self._goal_estimates = {}

    @staticmethod
    def _metric(first, second):
        return abs(first[0] - second[0]) + abs(first[1] - second[1])

    def _prepare(self):
        signature = (self.network, self.network.revision)
        if signature == self._revision:
            return
        nodes = sorted(self.network.nodes)
        if self._supplied_coordinates is None:
            width = max(1, math.ceil(math.sqrt(len(nodes))))
            coordinates = {node: (index % width, index // width) for index, node in enumerate(nodes)}
        else:
            if not set(nodes).issubset(self._supplied_coordinates):
                raise ValueError("Coordinates must cover every network node")
            coordinates = {}
            for node in nodes:
                point = self._supplied_coordinates[node]
                if not isinstance(point, (tuple, list)) or len(point) != 2:
                    raise ValueError("Each coordinate must contain two finite numbers")
                try:
                    coordinates[node] = tuple(float(value) for value in point)
                except (TypeError, ValueError, OverflowError) as exc:
                    raise ValueError("Invalid coordinate") from exc
                if not all(math.isfinite(value) for value in coordinates[node]):
                    raise ValueError("Coordinates must be finite")
        if nodes:
            extent = sum(max(point[axis] for point in coordinates.values()) -
                         min(point[axis] for point in coordinates.values()) for axis in (0, 1))
            if not math.isfinite(extent):
                raise ValueError("Coordinate span overflow")
        else:
            extent = 0.0
        ratios, costs = [], []
        for node in nodes:
            for neighbor, cost in self.network.get_neighbors(node):
                costs.append(cost)
                span = self._metric(coordinates[node], coordinates[neighbor])
                if span:
                    ratios.append(cost / span)
        scale = min(ratios, default=0.0)
        if not math.isfinite(scale):
            scale = 0.0
        if scale and extent:
            scale = math.nextafter(min(scale, sys.float_info.max / extent), 0.0)
        self.coordinates = coordinates
        self.min_edge_cost = min(costs, default=0.0)
        self.heuristic_scale = scale
        self._goal_estimates = {}
        self._revision = signature

    def _estimates(self, goal):
        self._prepare()
        if goal not in self._goal_estimates:
            values = {node: self.heuristic_scale * self._metric(point, self.coordinates[goal])
                      for node, point in self.coordinates.items()}
            # Real-number triangle inequality proves consistency. Check native
            # float inequalities too; unsafe rounding/overflow falls back to h=0.
            safe = all(math.isfinite(value) and value >= 0 for value in values.values())
            safe = safe and values[goal] == 0
            safe = safe and all(values[node] <= cost + values[neighbor]
                                for node in self.network.nodes
                                for neighbor, cost in self.network.get_neighbors(node))
            self._goal_estimates[goal] = values if safe else {node: 0.0 for node in self.network.nodes}
        return self._goal_estimates[goal]

    def heuristic(self, node1, node2):
        validate_endpoints(self.network, node1, node2)
        return self._estimates(node2)[node1]

    def a_star(self, start, end):
        def operation():
            validate_endpoints(self.network, start, end)
            return best_first(self.network, start, end, self._estimates(end))
        return self._measure(operation)

    def route(self, start, end):
        return self.a_star(start, end)


def main():
    AStarDispatcher().run_simulation()


if __name__ == "__main__":
    main()