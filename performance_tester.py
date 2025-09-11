"""
Performance testing for dispatch algorithms
"""
from dijkstra_dispatcher import DijkstraDispatcher
from astar_dispatcher import AStarDispatcher


def run_performance_test(dispatcher_class, num_runs=10):
    """Run performance test for a dispatcher"""
    times = []

    for run in range(1, num_runs + 1):
        print(f"Run {run}/{num_runs}...", end=" ")

        dispatcher = dispatcher_class()
        dispatcher.load_data()

        # Suppress output during test
        import sys
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        # Run simulation
        dispatcher.process_all_calls()

        # Restore output
        sys.stdout = old_stdout

        # Record time
        routing_time = dispatcher.total_routing_time
        times.append(routing_time)
        print(f"Time: {routing_time:.6f} seconds")

    # Calculate statistics
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    return {
        'times': times,
        'average': avg_time,
        'min': min_time,
        'max': max_time
    }


def display_results(algorithm_name, results):
    """Display performance test results"""
    print(f"\n{'=' * 60}")
    print(f"{algorithm_name} PERFORMANCE TEST RESULTS")
    print(f"{'=' * 60}")

    print("\nIndividual run times:")
    for i, time_val in enumerate(results['times'], 1):
        print(f"  Run {i:2d}: {time_val:.6f} seconds")

    print(f"\nStatistics:")
    print(f"  Average: {results['average']:.6f} seconds")
    print(f"  Minimum: {results['min']:.6f} seconds")
    print(f"  Maximum: {results['max']:.6f} seconds")
    print(f"{'=' * 60}\n")


def main():
    """Run performance tests for both prototypes"""
    print("PERFORMANCE TESTING - COMPARING PROTOTYPES")
    print("=" * 60)

    # Test A* (Prototype Two)
    print("\nTesting A* Algorithm...")
    astar_results = run_performance_test(AStarDispatcher, 10)
    display_results("A* ALGORITHM", astar_results)

    # Test Dijkstra (for comparison)
    print("\nTesting Dijkstra's Algorithm...")
    dijkstra_results = run_performance_test(DijkstraDispatcher, 10)
    display_results("DIJKSTRA'S ALGORITHM", dijkstra_results)

    # Comparison
    print("\n" + "=" * 60)
    print("PERFORMANCE COMPARISON")
    print("=" * 60)
    improvement = (1 - astar_results['average'] / dijkstra_results['average']) * 100
    print(f"A* Average: {astar_results['average']:.6f} seconds")
    print(f"Dijkstra Average: {dijkstra_results['average']:.6f} seconds")
    print(f"Performance Improvement: {improvement:.2f}%")
    print("=" * 60)


if __name__ == "__main__":
    main()