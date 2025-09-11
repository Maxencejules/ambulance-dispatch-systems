"""
Data structures for ambulance dispatch system
"""
from datetime import datetime
import heapq


class EmergencyCall:
    """Represents an emergency call"""
    def __init__(self, call_id, location, call_type, priority):
        self.call_id = call_id
        self.location = location
        self.call_type = call_type
        self.priority = priority
        self.timestamp = datetime.now()

    def __repr__(self):
        return f"Call {self.call_id}: {self.call_type} at {self.location} (Priority {self.priority})"


class Ambulance:
    """Represents an ambulance unit"""
    def __init__(self, ambulance_id, staging_location):
        self.id = ambulance_id
        self.staging_location = staging_location
        self.current_location = staging_location
        self.is_available = True

    def dispatch(self, location):
        """Dispatch ambulance to location"""
        self.current_location = location
        self.is_available = False

    def reset(self):
        """Reset ambulance to staging location"""
        self.current_location = self.staging_location
        self.is_available = True

    def __repr__(self):
        return f"{self.id} at {self.current_location}"


class CallPriorityQueue:
    """Priority queue for emergency calls"""
    def __init__(self):
        self.queue = []
        self.counter = 0  # For FIFO within same priority

    def add_call(self, call):
        """Add call to priority queue"""
        # Use (priority, counter, call) to ensure FIFO within same priority
        heapq.heappush(self.queue, (call.priority, self.counter, call))
        self.counter += 1

    def get_next_call(self):
        """Get highest priority call"""
        if self.queue:
            _, _, call = heapq.heappop(self.queue)
            return call
        return None

    def is_empty(self):
        """Check if queue is empty"""
        return len(self.queue) == 0

    def size(self):
        """Get queue size"""
        return len(self.queue)


class RoadNetwork:
    """Graph representation of road network"""
    def __init__(self):
        self.graph = {}  # Adjacency list: {node: [(neighbor, time), ...]}
        self.nodes = set()

    def add_edge(self, start, end, distance, travel_time, traffic_delay):
        """Add bidirectional edge to graph"""
        total_time = travel_time + traffic_delay

        # Initialize nodes if not exist
        if start not in self.graph:
            self.graph[start] = []
        if end not in self.graph:
            self.graph[end] = []

        # Add bidirectional edges
        self.graph[start].append((end, total_time))
        self.graph[end].append((start, total_time))

        # Track all nodes
        self.nodes.add(start)
        self.nodes.add(end)

    def get_neighbors(self, node):
        """Get neighbors of a node"""
        return self.graph.get(node, [])

    def __repr__(self):
        return f"RoadNetwork with {len(self.nodes)} nodes and {sum(len(n) for n in self.graph.values())//2} edges"