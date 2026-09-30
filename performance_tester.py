"""Repeated, verified offline benchmark; timings are observations, not a recommendation."""
import argparse
import csv
import json
import math
import os
from pathlib import Path
import platform
import statistics
import sys
import time
from astar_dispatcher import AStarDispatcher
from dijkstra_dispatcher import DijkstraDispatcher
from experiments import bundled, generated_grid, queries_for, reference_distances, check_route, input_hashes


def environment():
    cpu = platform.processor() or platform.machine()
    if sys.platform == "win32":
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                               r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as key:
                cpu = winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
        except OSError:
            pass
    elif sys.platform.startswith("linux"):
        try:
            cpu = next(line.split(":", 1)[1].strip() for line in Path("/proc/cpuinfo").read_text().splitlines()
                       if line.startswith("model name"))
        except (OSError, StopIteration):
            pass
    clock = time.get_clock_info("perf_counter")
    return {"python": sys.version, "platform": platform.platform(), "cpu": cpu,
            "logical_processors": os.cpu_count(), "clock": clock.implementation,
            "clock_resolution_seconds": clock.resolution}


def run_trial(cls, network, coordinates, queries, repeats):
    start = time.perf_counter()
    dispatcher = cls(network, verbose=False, log_file=None,
                     **({"coordinates": coordinates} if cls is AStarDispatcher else {}))
    outputs, expansions = [], 0
    for _ in range(repeats):
        current = []
        for first, second in queries:
            current.append(dispatcher.route(first, second))
            expansions += dispatcher.last_expanded
        outputs.append(current)
    elapsed = time.perf_counter() - start
    if not math.isfinite(elapsed) or elapsed <= 0:
        raise RuntimeError("Invalid measured duration")
    return elapsed, outputs, expansions


def run_performance_test(dispatcher_class, num_runs=10):
    """Compatibility helper: verified bundled dispatch routing totals, with no log I/O."""
    if not isinstance(num_runs, int) or isinstance(num_runs, bool) or not 1 <= num_runs <= 15:
        raise ValueError("num_runs must be 1..15")
    _, _, edges = bundled()
    values = []
    for _ in range(num_runs):
        dispatcher = dispatcher_class()
        dispatcher.verbose, dispatcher.log_file = False, None
        dispatcher.load_data()
        oracle = {unit.current_location: reference_distances(dispatcher.network.nodes, edges, unit.current_location)
                  for unit in dispatcher.ambulances}
        dispatcher.process_all_calls()
        for record in dispatcher.dispatches:
            unit = next(unit for unit in dispatcher.ambulances if unit.id == record["ambulance_id"])
            check_route(record["route"], record["time_to_location"], unit.staging_location,
                        record["call_location"], oracle[unit.staging_location][record["call_location"]], edges)
        values.append(dispatcher.total_routing_time)
    return {"times": values, "average": statistics.mean(values), "median": statistics.median(values),
            "min": min(values), "max": max(values)}


def display_results(algorithm_name, results):
    print(f"{algorithm_name}: mean={results['average']:.6f}s "
          f"min={results['min']:.6f}s max={results['max']:.6f}s")


def benchmark(trials=9, queries=100, repeats=3, side=8, seed=2026):
    if not all(isinstance(value, int) and not isinstance(value, bool) for value in (trials, queries, repeats, side, seed)):
        raise ValueError("Benchmark settings must be integers")
    if not (3 <= trials <= 15 and 1 <= queries <= 500 and 1 <= repeats <= 10
            and 2 <= side <= 15 and isinstance(seed, int) and 0 <= seed <= 2**32 - 1):
        raise ValueError("Bounds: trials 3..15, queries 1..500, repeats 1..10, side 2..15, uint32 seed")
    if trials * queries * repeats * side * side > 5_000_000:
        raise ValueError("Benchmark operation budget exceeded")
    rows, summary = [], {}
    classes = (DijkstraDispatcher, AStarDispatcher)
    for scenario, (network, coordinates, edges) in (
            ("bundled", bundled()), ("grid", generated_grid(side, seed))):
        workload = queries_for(network, queries, seed)
        oracle = {first: reference_distances(network.nodes, edges, first) for first in {first for first, _ in workload}}
        def verify(outputs):
            for batch in outputs:
                for (first, second), (path, cost) in zip(workload, batch):
                    check_route(path, cost, first, second, oracle[first][second], edges)
        for cls in classes:  # one excluded warmup; fresh dispatcher in every measured batch
            verify(run_trial(cls, network, coordinates, workload, repeats)[1])
        times = {cls.algorithm: [] for cls in classes}
        for trial in range(trials):
            ordered = classes if trial % 2 == 0 else classes[::-1]
            for cls in ordered:
                elapsed, outputs, expanded = run_trial(cls, network, coordinates, workload, repeats)
                verify(outputs)  # all returned routes, every repetition/trial; outside timing
                times[cls.algorithm].append(elapsed)
                rows.append({"scenario": scenario, "trial": trial + 1,
                             "first_algorithm": ordered[0].algorithm, "algorithm": cls.algorithm,
                             "seconds": elapsed, "nodes": len(network.nodes), "input_edges": len(edges),
                             "queries": queries, "repeats": repeats, "seed": seed,
                             "expansions": expanded, "verified_routes": queries * repeats})
        summary[scenario] = {name: {"median_seconds": statistics.median(values),
                                   "min_seconds": min(values), "max_seconds": max(values),
                                   "q1_seconds": statistics.quantiles(values, n=4, method="inclusive")[0],
                                   "q3_seconds": statistics.quantiles(values, n=4, method="inclusive")[2]}
                             for name, values in times.items()}
    return rows, {"environment": environment(), "seed": seed, "trials": trials, "queries": queries, "repeats": repeats, "side": side,
                  "input_sha256_utf8_lf": input_hashes(), "summary": summary,
                  "timing_scope": "Fresh dispatcher, heuristic setup/goal validation, all route queries; excludes graph/input/oracle generation, verification, I/O."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name, default in (("trials",9), ("queries",100), ("repeats",3), ("side",8), ("seed",2026)):
        parser.add_argument("--" + name, type=int, default=default)
    parser.add_argument("--output", type=Path, default=Path("artifacts/benchmark"))
    args = parser.parse_args()
    try:
        rows, report = benchmark(args.trials, args.queries, args.repeats, args.side, args.seed)
    except ValueError as exc:
        parser.error(str(exc))
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "trials.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    (args.output / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False)+"\n",
                                           encoding="utf-8", newline="\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()