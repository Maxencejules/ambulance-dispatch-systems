"""Shared selection/logging model: every completed call resets its ambulance."""
import csv
from pathlib import Path
import time
import config
from routing import validate_endpoints
from data_loader import load_ambulances, load_calls, load_network


class Dispatcher:
    algorithm = "base"

    def __init__(self, network=None, *, verbose=True, log_file=config.LOG_FILE):
        self.network = network
        self.ambulances = []
        self.call_queue = None
        self.verbose = verbose
        self.log_file = log_file
        self.total_routing_time = 0.0
        self.routing_calls = 0
        self.last_expanded = 0
        self.total_calls_processed = 0
        self.dispatches = []

    def load_data(self):
        self.network = load_network()
        self.ambulances = load_ambulances()
        self.call_queue = load_calls()
        locations = [unit.current_location for unit in self.ambulances]
        locations += [entry[2].location for entry in self.call_queue.queue]
        if any(location not in self.network.nodes for location in locations):
            raise ValueError("Fleet/call location missing from road network")

    def _measure(self, operation):
        start = time.perf_counter()
        self.last_expanded = 0
        try:
            path, cost, self.last_expanded = operation()
            return path, cost
        finally:
            self.total_routing_time += time.perf_counter() - start
            self.routing_calls += 1

    def find_best_ambulance(self, call_location):
        validate_endpoints(self.network, call_location, call_location)
        best, route, cost = None, None, float("inf")
        for unit in self.ambulances:
            if unit.is_available:
                candidate, travel = self.route(unit.current_location, call_location)
                if candidate is not None and travel < cost:
                    best, route, cost = unit, candidate, travel
        return best, route, cost

    def create_dispatch_record(self, call, ambulance, route, time_to_location):
        return {"call_id": call.call_id, "call_type": call.call_type,
                "call_location": call.location, "ambulance_id": ambulance.id,
                "route": route, "time_to_location": time_to_location}

    def log_dispatch(self, record):
        if self.log_file is None:
            return
        path = Path(self.log_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        header = not path.exists() or path.stat().st_size == 0
        with path.open("a", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(record))
            if header:
                writer.writeheader()
            writer.writerow({**record, "route": ">".join(record["route"])})

    def process_single_call(self, call):
        unit, route, cost = self.find_best_ambulance(call.location)
        if unit is None:
            if self.verbose:
                print(f"Call {call.call_id}: no available reachable ambulance")
            return None
        record = self.create_dispatch_record(call, unit, route, cost)
        self.log_dispatch(record)
        unit.reset()
        self.dispatches.append(record)
        if self.verbose:
            print(f"Call {call.call_id}: {unit.id}; {' -> '.join(route)}; {cost:.2f} modeled minutes")
        return record

    def process_all_calls(self):
        if self.call_queue is None:
            raise ValueError("Calls must be loaded")
        while not self.call_queue.is_empty():
            self.process_single_call(self.call_queue.get_next_call())
            self.total_calls_processed += 1

    def display_performance_metrics(self):
        print(f"{self.algorithm}: {self.total_calls_processed} calls, "
              f"{self.routing_calls} route attempts, {self.total_routing_time:.6f} routing seconds")

    def run_simulation(self):
        self.load_data()
        self.process_all_calls()
        self.display_performance_metrics()