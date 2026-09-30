import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import os
from astar_dispatcher import AStarDispatcher
from dijkstra_dispatcher import DijkstraDispatcher
from data_structures import Ambulance, EmergencyCall, CallPriorityQueue, RoadNetwork
from data_loader import load_network, load_calls, load_priorities
from demo import run_demo
from performance_tester import benchmark


class DispatchTests(unittest.TestCase):
    def test_priority_fifo_and_availability_ties(self):
        network = RoadNetwork()
        network.add_edge("S","G",1,2,1)
        network.add_node("isolated")
        for cls in (DijkstraDispatcher,AStarDispatcher):
            dispatcher = cls(network,verbose=False,log_file=None)
            first, second = Ambulance("first","S"), Ambulance("second","S")
            dispatcher.ambulances = [first,second]
            self.assertIs(dispatcher.find_best_ambulance("G")[0],first)
            first.is_available = False
            self.assertIs(dispatcher.find_best_ambulance("G")[0],second)
            self.assertEqual(dispatcher.find_best_ambulance("isolated"),(None,None,float("inf")))
            second.is_available = False
            with self.assertRaises(ValueError):
                dispatcher.find_best_ambulance("unknown")
            second.reset()
            dispatcher.call_queue = CallPriorityQueue()
            for identifier, priority in ((1,2),(2,1),(3,1)):
                dispatcher.call_queue.add_call(EmergencyCall(identifier,"G","fixture",priority))
            dispatcher.process_all_calls()
            self.assertEqual([record["call_id"] for record in dispatcher.dispatches],[2,3,1])
            self.assertEqual(dispatcher.total_calls_processed,3)
            self.assertTrue(second.is_available)
            self.assertEqual(second.current_location,"S")

    def test_loader_validation_and_location_relative_defaults(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            previous = Path.cwd()
            try:
                os.chdir(directory)
                self.assertEqual(len(load_network().nodes),7)
                self.assertEqual(load_calls().size(),100)
            finally:
                os.chdir(previous)
            for contents in ("Start,End,Distance\nA,B,1\n",
                             "Start,End,Distance,Travel Time,Traffic Delay\nA,B,1,-2,0\n",
                             "Start,End,Distance,Travel Time,Traffic Delay\nA,B,1,nan,0\n",
                             "Start,Start,End,Distance,Travel Time,Traffic Delay\nA,A,B,1,1,0\n"):
                path = directory/"network.csv"; path.write_text(contents,encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_network(path)
            priorities = directory/"priority.csv"
            priorities.write_text("Call Type,Priority\nfixture,1\nfixture,2\n",encoding="utf-8")
            with self.assertRaises(ValueError):
                load_priorities(priorities)
            priorities.write_text("Call Type,Priority\nfixture,1\n",encoding="utf-8")
            calls = directory/"calls.csv"
            calls.write_text("Call ID,Location,Call Type\n1,A,unknown\n",encoding="utf-8")
            with self.assertRaises(ValueError):
                load_calls(calls,priorities)

    def test_explicit_log_path_header_and_no_fallback(self):
        network = RoadNetwork(); network.add_node("S")
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/"nested"/"dispatch.csv"
            dispatcher = DijkstraDispatcher(network,verbose=False,log_file=path)
            dispatcher.ambulances = [Ambulance("unit","S")]
            dispatcher.process_single_call(EmergencyCall(1,"S","fixture",1))
            dispatcher.process_single_call(EmergencyCall(2,"S","fixture",1))
            with path.open(newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows),2)
            self.assertEqual(rows[0]["route"],"S")
            with patch("dispatcher.Path.open",side_effect=OSError("intentional")):
                with self.assertRaises(OSError):
                    dispatcher.process_single_call(EmergencyCall(3,"S","fixture",1))

    def test_demo_records_and_repeats_exactly(self):
        result = run_demo()
        self.assertEqual(result,run_demo())
        for name, count in (("bundled",100),("grid",12)):
            for records in result["scenarios"][name]["algorithms"].values():
                self.assertEqual(len(records["dispatches"]),count)
                order = records["call_order"]
                self.assertEqual([priority for _,priority in order],
                                 sorted(priority for _,priority in order))

    def test_demo_is_independent_of_hash_seed(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            outputs = []
            for seed in ("1","99"):
                output = Path(temporary)/f"{seed}.json"
                subprocess.run([sys.executable,str(root/"demo.py"),"--output",str(output)],
                               cwd=temporary,env={**os.environ,"PYTHONHASHSEED":seed},
                               check=True,capture_output=True,text=True,timeout=30)
                outputs.append(output.read_bytes())
            self.assertEqual(outputs[0],outputs[1])

    def test_benchmark_records_and_rejects_bad_bounds(self):
        rows, report = benchmark(trials=3,queries=4,repeats=1,side=3)
        self.assertEqual(len(rows),12)
        self.assertEqual(report["trials"],3)
        self.assertEqual({row["first_algorithm"] for row in rows if row["trial"]==2},{"astar"})
        self.assertTrue(all(row["verified_routes"]==4 and row["seconds"]>0 for row in rows))
        for options in ({"trials":0},{"side":1},{"queries":0},{"seed":-1},
                        {"trials":15,"queries":500,"repeats":10,"side":15}):
            with self.assertRaises(ValueError):
                benchmark(**options)

    def test_benchmark_does_not_report_corrupt_routes(self):
        with patch.object(AStarDispatcher,"route",return_value=(["wrong"],0.0)):
            with self.assertRaises(AssertionError):
                benchmark(trials=3,queries=2,repeats=1,side=2)


if __name__ == "__main__":
    unittest.main()