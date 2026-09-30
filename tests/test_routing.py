import math
import random
import unittest
from astar_dispatcher import AStarDispatcher
from dijkstra_dispatcher import DijkstraDispatcher
from data_structures import RoadNetwork
from experiments import check_route, reference_distances, bundled, input_hashes


def make_network(nodes, edges):
    network = RoadNetwork()
    for node in nodes:
        network.add_node(node)
    for first, second, cost in edges:
        network.add_edge(first, second, 0, cost, 0)
    return network


def exhaustive_cost(nodes, edges, start, goal):
    """Enumerate all simple paths from the original edge list, without heaps."""
    best = math.inf
    def walk(node, seen, cost):
        nonlocal best
        if node == goal:
            best = min(best, cost)
            return
        for first, second, weight in edges:
            neighbor = second if first == node else first if second == node else None
            if neighbor is not None and neighbor not in seen:
                walk(neighbor, seen | {neighbor}, cost + weight)
    walk(start, {start}, 0.0)
    return best


class RoutingTests(unittest.TestCase):
    def check_pair(self, network, edges, start, goal, expected, coordinates=None):
        for cls in (DijkstraDispatcher, AStarDispatcher):
            kwargs = {"coordinates": coordinates} if cls is AStarDispatcher else {}
            dispatcher = cls(network, verbose=False, log_file=None, **kwargs)
            path, cost = dispatcher.route(start, goal)
            check_route(path, cost, start, goal, expected, edges)
            if cls is AStarDispatcher:
                for node in network.nodes:
                    for neighbor, weight in network.get_neighbors(node):
                        self.assertLessEqual(dispatcher.heuristic(node, goal),
                                             weight + dispatcher.heuristic(neighbor, goal))

    def test_improved_open_priority_hand_case(self):
        edges = [("S","A",10),("S","B",1),("B","A",1),("A","G",1),("S","G",5)]
        network = make_network(["S","A","B","G"], edges)
        self.check_pair(network, edges, "S", "G", 3, {node:(0,0) for node in network.nodes})
        self.assertEqual(AStarDispatcher(network, coordinates={node:(0,0) for node in network.nodes}).a_star("S","G")[0],
                         ["S","B","A","G"])

    def test_old_manhattan_overestimate_hand_case(self):
        edges = [("S","G",5),("S","A",1),("A","G",1)]
        network = make_network(["S","A","G"], edges)
        coordinates = {"S":(0,0),"A":(100,0),"G":(0,5)}
        self.check_pair(network, edges, "S", "G", 2, coordinates)
        self.assertLessEqual(AStarDispatcher(network, coordinates=coordinates).heuristic("A","G"), 1)

    def test_parallel_zero_cycle_and_disconnected(self):
        edges = [("S","A",8),("A","S",0),("A","B",0),("B","S",0),("B","G",2),("G","G",0)]
        network = make_network(["S","A","B","G","isolated"], edges)
        self.check_pair(network, edges, "S","G",2)
        self.check_pair(network, edges, "S","isolated",math.inf)
        self.check_pair(network, edges, "isolated","isolated",0)
        self.assertEqual(AStarDispatcher(network).heuristic("S","G"), 0)

    def test_membership_before_self_route(self):
        network = make_network(["known"], [])
        for cls in (DijkstraDispatcher, AStarDispatcher):
            dispatcher = cls(network)
            self.assertEqual(dispatcher.route("known","known"), (["known"],0.0))
            for start, goal in (("missing","missing"),("known","missing"),(None,"known"),([],"known")):
                with self.subTest(cls=cls,start=start):
                    with self.assertRaises(ValueError):
                        dispatcher.route(start,goal)
            with self.assertRaises(ValueError):
                cls().route("known","known")
            with self.assertRaises(ValueError):
                cls(RoadNetwork()).route("missing","missing")

    def test_exhaustive_tiny_graphs_all_pairs(self):
        for seed in range(5):
            rng = random.Random(seed)
            nodes = [str(index) for index in range(6)]
            edges = [(first, second, rng.randrange(17)/4)
                     for index, first in enumerate(nodes)
                     for second in nodes[index+1:] if rng.random() < .5]
            network = make_network(nodes, edges)
            for start in nodes:
                for goal in nodes:
                    with self.subTest(seed=seed,start=start,goal=goal):
                        self.check_pair(network, edges, start, goal,
                                        exhaustive_cost(nodes,edges,start,goal))

    def test_seeded_edge_list_reference_all_pairs(self):
        for seed in range(8):
            rng = random.Random(seed + 300)
            nodes = [str(index) for index in range(9)]
            edges = [(first,second,rng.randrange(25)/4)
                     for index,first in enumerate(nodes)
                     for second in nodes[index+1:] if rng.random() < .28]
            network = make_network(nodes,edges)
            for start in nodes:
                expected = reference_distances(nodes,edges,start)
                for goal in nodes:
                    self.check_pair(network,edges,start,goal,expected[goal])

    def test_revision_rebuilds_precomputed_bound(self):
        edges = [("S","A",100),("A","G",100),("S","G",500)]
        network = make_network(["S","A","G"],edges)
        dispatcher = AStarDispatcher(network,coordinates={"S":(0,0),"A":(1,0),"G":(2,0)})
        before = dispatcher.heuristic("S","G")
        self.assertEqual(dispatcher.a_star("S","G")[1],200)
        network.add_edge("S","G",1,1,0)
        self.assertLess(dispatcher.heuristic("S","G"),before)
        self.assertLessEqual(dispatcher.heuristic("S","G"),1)
        self.assertEqual(dispatcher.a_star("S","G"),(["S","G"],1.0))
        network.add_node("new")
        with self.assertRaises(ValueError):
            dispatcher.a_star("S","G")  # supplied geometry no longer covers network

    def test_invalid_and_degenerate_geometry(self):
        network = make_network(["S","G"],[("S","G",1)])
        for coordinates in ({"S":(0,0)}, {"S":(0,0),"G":(math.nan,0)},
                            {"S":(0,0),"G":(math.inf,0)}, {"S":(0,0),"G":(1,)},
                            {"S":(-1e308,0),"G":(1e308,0)}):
            with self.assertRaises(ValueError):
                AStarDispatcher(network,coordinates=coordinates).a_star("S","G")
        for coordinates in ({"S":(0,0),"G":(0,0)},{"S":(0,0),"G":(1e-320,0)}):
            dispatcher = AStarDispatcher(network,coordinates=coordinates)
            self.assertEqual(dispatcher.a_star("S","G")[1],1)
            self.assertEqual(dispatcher.heuristic("S","G"),0)

    def test_invalid_weights_rejected_without_mutation(self):
        for value in (-1,math.nan,math.inf,True,None):
            for field in range(3):
                network = RoadNetwork()
                values = [1,1,1]; values[field] = value
                with self.assertRaises(ValueError):
                    network.add_edge("S","G",*values)
                self.assertEqual(network.nodes,set())
                self.assertEqual(network.revision,0)
        with self.assertRaises(ValueError):
            RoadNetwork().add_edge("S","G",1,1e308,1e308)

    def test_path_arithmetic_overflow_is_not_unreachable(self):
        network = make_network(["S","A","G"],[("S","A",1e308),("A","G",1e308)])
        for cls in (DijkstraDispatcher,AStarDispatcher):
            with self.assertRaises(OverflowError):
                cls(network).route("S","G")

    def test_bundled_semantic_baseline_all_pairs(self):
        network, _, edges = bundled()
        self.assertEqual(len(network.nodes),7)
        self.assertEqual(len(edges),42)
        self.assertEqual(sum(len(network.get_neighbors(node)) for node in network.nodes),84)
        self.assertNotEqual(edges[0][2], next(cost for first,second,cost in edges
                                            if first==edges[0][1] and second==edges[0][0]))
        for start in sorted(network.nodes):
            expected = reference_distances(network.nodes,edges,start)
            for goal in sorted(network.nodes):
                self.check_pair(network,edges,start,goal,expected[goal])
        self.assertEqual(len(input_hashes()),4)


if __name__ == "__main__":
    unittest.main()