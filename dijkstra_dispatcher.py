"""
Ambulance dispatcher using Dijkstra's algorithm
"""
import csv
import heapq
import time
import config
from data_loader import load_ambulances, load_network, load_calls


class DijkstraDispatcher:
    """Dispatcher using Dijkstra's algorithm for routing"""

    def __init__(self):
        self.ambulances = []
        self.network = None
        self.call_queue = None

        # Performance metrics
        self.total_routing_time = 0.0
        self.routing_calls = 0

        # Dispatch statistics
        self.total_calls_processed = 0
        self.dispatches = []

    def load_data(self):
        """Load all required data files"""
        print("Loading data files...")
        self.ambulances = load_ambulances()
        self.network = load_network()
        self.call_queue = load_calls()
        print("Data loading complete!\n")

    def dijkstra(self, start, end):
        """
        Find shortest path using Dijkstra's algorithm
        Returns: (path, total_time)
        """
        # Start performance timer
        start_time = time.perf_counter()

        # Initialize distances and parents
        distances = {node: float('infinity') for node in self.network.nodes}
        distances[start] = 0
        parents = {node: None for node in self.network.nodes}

        # Priority queue: (distance, node)
        pq = [(0, start)]
        visited = set()

        while pq:
            current_dist, current_node = heapq.heappop(pq)

            # Skip if already visited
            if current_node in visited:
                continue

            visited.add(current_node)

            # Found destination
            if current_node == end:
                # Reconstruct path
                path = []
                node = end
                while node is not None:
                    path.append(node)
                    node = parents[node]
                path.reverse()

                # End performance timer
                elapsed = time.perf_counter() - start_time
                self.total_routing_time += elapsed
                self.routing_calls += 1

                return path, distances[end]

            # Explore neighbors
            for neighbor, travel_time in self.network.get_neighbors(current_node):
                if neighbor not in visited:
                    new_dist = current_dist + travel_time

                    if new_dist < distances[neighbor]:
                        distances[neighbor] = new_dist
                        parents[neighbor] = current_node
                        heapq.heappush(pq, (new_dist, neighbor))

        # No path found
        elapsed = time.perf_counter() - start_time
        self.total_routing_time += elapsed
        self.routing_calls += 1

        return None, float('infinity')

    def find_best_ambulance(self, call_location):
        """
        Find ambulance with shortest time to call location
        Returns: (best_ambulance, best_route, best_time)
        """
        best_ambulance = None
        best_route = None
        best_time = float('infinity')

        for ambulance in self.ambulances:
            if ambulance.is_available:
                route, time_to_location = self.dijkstra(
                    ambulance.current_location,
                    call_location
                )

                if route and time_to_location < best_time:
                    best_time = time_to_location
                    best_ambulance = ambulance
                    best_route = route

        return best_ambulance, best_route, best_time

    def create_dispatch_record(self, call, ambulance, route, time_to_location):
        """Create dispatch record dictionary"""
        return {
            'call_id': call.call_id,
            'call_type': call.call_type,
            'call_location': call.location,
            'ambulance_id': ambulance.id,
            'route': route,
            'time_to_location': time_to_location
        }

    def log_dispatch(self, dispatch_record):
        """Log dispatch to CSV file"""
        try:
            with open(config.LOG_FILE, 'a', newline='') as f:
                writer = csv.writer(f)

                # Format route as string with > separator
                route_str = '>'.join(dispatch_record['route'])

                # Write as name-value pairs
                writer.writerow([
                    f"Call_ID={dispatch_record['call_id']}",
                    f"Call_Type={dispatch_record['call_type']}",
                    f"Call_Location={dispatch_record['call_location']}",
                    f"Selected_Ambulance={dispatch_record['ambulance_id']}",
                    f"Route_to_Call_Location={route_str}",
                    f"Time_to_Call_Location={dispatch_record['time_to_location']:.2f}"
                ])
        except Exception as e:
            print(f"Warning: Could not write to log file: {e}")
            # Create local log file instead
            with open('local_ambulance_log.csv', 'a', newline='') as f:
                writer = csv.writer(f)
                route_str = '>'.join(dispatch_record['route'])
                writer.writerow([
                    f"Call_ID={dispatch_record['call_id']}",
                    f"Call_Type={dispatch_record['call_type']}",
                    f"Call_Location={dispatch_record['call_location']}",
                    f"Selected_Ambulance={dispatch_record['ambulance_id']}",
                    f"Route_to_Call_Location={route_str}",
                    f"Time_to_Call_Location={dispatch_record['time_to_location']:.2f}"
                ])

    def process_single_call(self, call):
        """Process a single emergency call"""
        print(f"Processing {call}")

        # Find best ambulance
        ambulance, route, time_to_location = self.find_best_ambulance(call.location)

        if ambulance and route:
            # Create and log dispatch record
            dispatch_record = self.create_dispatch_record(
                call, ambulance, route, time_to_location
            )
            self.log_dispatch(dispatch_record)

            # Reset ambulance to staging location
            ambulance.reset()

            # Store for statistics
            self.dispatches.append(dispatch_record)

            print(f"  ✓ Dispatched {ambulance.id} to {call.location}")
            print(f"    Route: {' -> '.join(route)}")
            print(f"    Time: {time_to_location:.2f} minutes\n")
        else:
            print(f"  ✗ No ambulance available for {call.location}\n")

    def process_all_calls(self):
        """Process all calls in priority queue"""
        print("=" * 60)
        print("STARTING AMBULANCE DISPATCH SIMULATION")
        print("=" * 60 + "\n")

        while not self.call_queue.is_empty():
            call = self.call_queue.get_next_call()
            self.process_single_call(call)
            self.total_calls_processed += 1

        print("=" * 60)
        print("DISPATCH SIMULATION COMPLETE")
        print("=" * 60)

    def display_performance_metrics(self):
        """Display algorithm performance metrics"""
        print("\n" + "=" * 60)
        print("DIJKSTRA'S ALGORITHM PERFORMANCE METRICS")
        print("=" * 60)
        print(f"Total calls processed: {self.total_calls_processed}")
        print(f"Total routing calculations: {self.routing_calls}")
        print(f"Total routing time: {self.total_routing_time:.6f} seconds")

        if self.routing_calls > 0:
            avg_time = self.total_routing_time / self.routing_calls
            print(f"Average time per route: {avg_time:.6f} seconds")

        print("=" * 60 + "\n")

    def run_simulation(self):
        """Run complete dispatch simulation"""
        # Load data
        self.load_data()

        # Process all calls
        self.process_all_calls()

        # Display metrics
        self.display_performance_metrics()


def main():
    """Main execution function"""
    dispatcher = DijkstraDispatcher()
    dispatcher.run_simulation()


if __name__ == "__main__":
    main()