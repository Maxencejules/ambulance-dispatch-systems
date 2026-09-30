"""Produce an offline recorded dispatch demonstration, verified against an edge-list oracle."""
import argparse
import json
from pathlib import Path
from astar_dispatcher import AStarDispatcher
from dijkstra_dispatcher import DijkstraDispatcher
from data_structures import Ambulance, CallPriorityQueue, EmergencyCall
from experiments import bundled, generated_grid, input_hashes, reference_distances, check_route


def run_demo(seed=2026):
    scenarios = {}
    for name, (network, coordinates, edges) in (
            ("bundled", bundled()), ("grid", generated_grid(6, seed))):
        records = {}
        for cls in (DijkstraDispatcher, AStarDispatcher):
            dispatcher = cls(network, verbose=False, log_file=None,
                             **({"coordinates": coordinates} if cls is AStarDispatcher else {}))
            if name == "bundled":
                dispatcher.load_data()
            else:
                nodes = sorted(network.nodes)
                dispatcher.ambulances = [Ambulance(f"Unit {index+1}", location)
                                         for index, location in enumerate((nodes[0],nodes[len(nodes)//2],nodes[-1]))]
                dispatcher.call_queue = CallPriorityQueue()
                for index, node in enumerate(nodes[::3], 1):
                    dispatcher.call_queue.add_call(EmergencyCall(index, node, "generated", index % 3 + 1))
            queue_order = [(entry[2].call_id, entry[2].priority)
                           for entry in sorted(dispatcher.call_queue.queue)]
            oracle = {unit.current_location: reference_distances(network.nodes, edges, unit.current_location)
                      for unit in dispatcher.ambulances}
            dispatcher.process_all_calls()
            for record in dispatcher.dispatches:
                unit = next(unit for unit in dispatcher.ambulances if unit.id == record["ambulance_id"])
                check_route(record["route"], record["time_to_location"], unit.staging_location,
                            record["call_location"], oracle[unit.staging_location][record["call_location"]], edges)
                best = min(values[record["call_location"]] for values in oracle.values())
                if abs(record["time_to_location"] - best) > 1e-10:
                    raise AssertionError("Selected ambulance was not minimal")
            records[cls.algorithm] = {"call_order": queue_order, "dispatches": dispatcher.dispatches}
        scenarios[name] = {"nodes": len(network.nodes), "input_edges": len(edges), "algorithms": records}
    return {"seed": seed, "input_sha256_utf8_lf": input_hashes(), "scenarios": scenarios,
            "model": "Independent priority-ordered requests; available ambulance returns immediately to staging. Costs in modeled minutes."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("artifacts/demo.json"))
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    if not 0 <= args.seed <= 2**32 - 1:
        parser.error("Seed must be uint32")
    result = run_demo(args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+"\n",
                           encoding="utf-8", newline="\n")
    for name, scenario in result["scenarios"].items():
        for algorithm, values in scenario["algorithms"].items():
            first = values["dispatches"][0]
            print(f"{name}/{algorithm}: {len(values['dispatches'])} verified dispatches; "
                  f"first={first['ambulance_id']} to {first['call_location']} cost={first['time_to_location']}")
    print(args.output)


if __name__ == "__main__":
    main()