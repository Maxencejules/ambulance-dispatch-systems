"""Small educational dispatch model; travel-time units are minutes."""
from datetime import datetime
import heapq
import math


def location_name(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Location must be a nonempty string")
    return value


def nonnegative_number(value, label):
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{label} must be a finite nonnegative number") from exc
    if isinstance(value, bool) or not math.isfinite(number) or number < 0:
        raise ValueError(f"{label} must be a finite nonnegative number")
    return number


class EmergencyCall:
    def __init__(self, call_id, location, call_type, priority):
        if not isinstance(priority, int) or isinstance(priority, bool) or priority < 0:
            raise ValueError("Priority must be a nonnegative integer")
        if not isinstance(call_type, str) or not call_type.strip():
            raise ValueError("Call type must be nonempty")
        self.call_id = call_id
        self.location = location_name(location)
        self.call_type = call_type
        self.priority = priority
        self.timestamp = datetime.now()

    def __repr__(self):
        return f"Call {self.call_id}: {self.call_type} at {self.location} (Priority {self.priority})"


class Ambulance:
    def __init__(self, ambulance_id, staging_location):
        self.id = ambulance_id
        self.staging_location = location_name(staging_location)
        self.current_location = self.staging_location
        self.is_available = True

    def dispatch(self, location):
        self.current_location = location_name(location)
        self.is_available = False

    def reset(self):
        self.current_location = self.staging_location
        self.is_available = True

    def __repr__(self):
        return f"{self.id} at {self.current_location}"


class CallPriorityQueue:
    def __init__(self):
        self.queue = []
        self.counter = 0

    def add_call(self, call):
        heapq.heappush(self.queue, (call.priority, self.counter, call))
        self.counter += 1

    def get_next_call(self):
        return heapq.heappop(self.queue)[2] if self.queue else None

    def is_empty(self):
        return not self.queue

    def size(self):
        return len(self.queue)


class RoadNetwork:
    """Undirected multigraph. Mutate only through add_node/add_edge, between queries."""

    def __init__(self):
        self.graph = {}
        self.nodes = set()
        self.revision = 0

    def add_node(self, node):
        location_name(node)
        if node not in self.nodes:
            self.nodes.add(node)
            self.graph[node] = []
            self.revision += 1

    def add_edge(self, start, end, distance, travel_time, traffic_delay):
        location_name(start)
        location_name(end)
        nonnegative_number(distance, "Distance")
        travel = nonnegative_number(travel_time, "Travel time")
        delay = nonnegative_number(traffic_delay, "Traffic delay")
        cost = travel + delay
        if not math.isfinite(cost):
            raise ValueError("Combined travel time overflow")
        self.add_node(start)
        self.add_node(end)
        self.graph[start].append((end, cost))
        self.graph[end].append((start, cost))
        self.revision += 1

    def get_neighbors(self, node):
        return tuple(self.graph.get(node, ()))

    @property
    def edge_count(self):
        return sum(map(len, self.graph.values())) // 2

    def __repr__(self):
        return f"RoadNetwork with {len(self.nodes)} nodes and {self.edge_count} input edges"