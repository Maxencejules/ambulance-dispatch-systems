# Ambulance Dispatch Route Optimizer

An offline educational comparison of Dijkstra and A* for static shortest paths and priority-ordered ambulance selection. Both searches now return independently verified minimum-cost routes. The project models a dispatch decision; it does not model a working emergency service.

## Run and reproduce

Use Python 3.12 or newer. Runtime, demo, benchmark and tests use only the standard library; no package installation is required. From the repository root:

```sh
python -m unittest discover -s tests -v
python demo.py --seed 2026 --output artifacts/demo.json
python performance_tester.py --seed 2026 --trials 9 --queries 100 --repeats 3 --side 8 --output artifacts/benchmark
```

The demo prints verified dispatch counts and writes every selected vehicle, route, cost and priority order. It checks 100 bundled requests and 12 generated requests per algorithm against an independent edge-list Bellman-Ford oracle, including minimum vehicle selection. The generated demo has 36 nodes and 60 undirected edges. [Recorded demo](examples/demo.json) is deterministic for a fixed seed and unchanged input files; timestamps and timings are deliberately excluded. Tests also compare its bytes under different Python hash seeds and from a different working directory.

For the original console workflow:

```sh
python dijkstra_dispatcher.py
python astar_dispatcher.py
```

These load inputs relative to the source directory and write an explicit CSV log to `artifacts/dispatch.csv`. A programmatic dispatcher can use `verbose=False, log_file=None` to disable console/log output. Log errors propagate instead of silently changing destinations. Demo and benchmark output paths are relative to the calling directory. Generated files under `artifacts/` are ignored.

[CI](.github/workflows/ci.yml) runs the tests, demo and a small seeded benchmark on Ubuntu and Windows with Python 3.12. It verifies correctness, uploads outputs and sets no timing threshold.

## Model and input contracts

The unchanged bundled fixtures contain seven locations, three ambulances, 100 requests and 20 call types. `Data/location_network.csv` has 42 rows, including both orientations of all 21 distinct location pairs. Each row creates a bidirectional edge. Reversed rows often have different weights, so they remain parallel alternatives: 42 undirected input edges and 84 adjacency entries. This preserves the existing undirected multigraph semantics; the two orientations do not represent one-way roads.

| Input | Required CSV columns |
| --- | --- |
| `Data/location_network.csv` | `Start,End,Distance,Travel Time,Traffic Delay` |
| `Data/ambulance.csv` | `Ambulance Number,Staging Location` |
| `Data/calls.csv` | `Call ID,Location,Call Type` |
| `Data/call_priority.csv` | `Call Type,Priority` |

Route cost is `Travel Time + Traffic Delay`, interpreted as modeled minutes. `Distance` is validated but does not influence route selection; its physical unit was not recorded. Costs must be finite, nonnegative numbers. Zero-cost edges and parallel edges are allowed. Malformed rows, missing/duplicate headers, duplicate identifiers, unknown call types or locations, negative/nonfinite weights and arithmetic overflow are rejected. Extra CSV columns are allowed. The provenance, collection method and real-world validity of these fixtures were not recorded; treat them as educational examples.

Lower priority numbers are processed first; equal priorities retain input order. The available ambulance with the least route cost is selected, with fleet order breaking equal-cost ties. After each recorded dispatch, it immediately returns to its staging location and becomes available again. Requests are independent decisions rather than concurrent incidents. The model has static traffic, no service duration, arrivals, capacity constraints, hospital selection or live geographic data.

`route(start, end)` returns `(path, cost)`. A known node routed to itself returns `([node], 0.0)`; an unreachable known destination returns `(None, math.inf)`. Unknown endpoints raise `ValueError`, including unknown self-routes. Unrepresentable route costs or search priorities raise `OverflowError` rather than being labeled unreachable. Costs use Python floats, not exact decimal arithmetic; verification compares within `1e-10` absolute / `1e-12` relative tolerance.

## Search correctness and heuristic assumptions

`routing.py` contains the common heap search. Dijkstra supplies `h=0`; A* supplies a consistent goal-specific lower bound. Every strictly improved path cost pushes a fresh priority, and superseded heap entries are skipped. The shared engine avoids duplicate dispatch/search bookkeeping; comparison between the two algorithms is not itself a correctness oracle.

For coordinates `p`, let `d(u,v)` be Manhattan distance and choose:

```text
alpha = min(cost(u,v) / d(u,v)) over edges with d(u,v) > 0
h(u,goal) = alpha * d(u,goal)
```

If no such edges exist, use `alpha=0`. For every edge, `alpha*d(u,v) <= cost(u,v)`. The triangle inequality gives `h(u) <= cost(u,v) + h(v)`; with `h(goal)=0`, this is a consistent and admissible lower bound. Coincident-coordinate edges satisfy the same inequality because their endpoint estimates are equal. A zero-cost edge with positive span forces `alpha=0`.

The implementation rounds a positive scale down, bounds coordinate extent, and checks the actual floating-point consistency inequalities for every adjacency entry for each goal. Any unsafe computed bound falls back to `h=0`. Supplied coordinates must cover all nodes and have finite components and finite overall span. These safeguards matter because a mathematical proof over real numbers does not remove floating-point rounding hazards.

The bundled network has no geographic coordinates. Its default coordinates are a deterministic grid assigned to sorted location names; they give a valid but weak artificial bound, not geographic distance. Generated networks use their actual synthetic grid coordinates, cardinal edges and seeded quarter-minute costs. Neither example is a real road network.

Use `RoadNetwork.add_node` and `add_edge` for all graph mutations between queries. Their revision counter invalidates cached coordinates and goal bounds; a newly added node needs a supplied coordinate if a custom map was used. Direct edits to public `graph`, `nodes`, cached coordinates or the supplied coordinate values are unsupported. Do not mutate a network during a query. Goal bounds are cached within a dispatcher, requiring up to `O(V^2)` additional storage across all distinct goals; their construction and edge consistency checks add preprocessing cost.

### Independent evidence

The 18 unittest methods include these substantive checks:

- Manual counterexamples where the old A* returned cost 5 instead of 3 after an improved open priority, and cost 5 instead of 2 with an overestimating heuristic.
- Exhaustive enumeration of simple paths for every ordered pair in five seeded six-node graphs; synchronous Bellman-Ford over original edge lists for every pair in eight seeded nine-node graphs and all 49 bundled pairs.
- Returned path endpoints, simplicity, existing edges, summed cost and agreement with the independent optimum; parallel/reversed rows, zero-cost cycles, self-loops, isolated nodes and unreachable queries.
- Native-float heuristic consistency, invalid/collapsed/extreme coordinates, graph revision changes, invalid weights and cost overflow.
- Priority/FIFO ordering, stable vehicle ties, availability/reset behavior, CSV validation, explicit log failure, deterministic demo bytes and benchmark rejection of intentionally corrupted results.

The reference algorithms consume the original edge list rather than production adjacency or heap-search code. The benchmark validates every returned route in every measured repetition and trial outside the timed section. Generated costs are binary-exact multiples of a quarter; bundled decimal costs are compared with the stated float tolerance.

## Recorded benchmark

[Raw trials](examples/benchmark/trials.csv) and [environment, settings and summary](examples/benchmark/report.json) were recorded on 2026-09-29 using Python 3.12.10 (MSC v.1943, 64-bit), Windows 11 build 26100, Intel Core i7-7700 at 3.60 GHz and eight logical processors. `perf_counter` used QueryPerformanceCounter with reported resolution 100 ns. This shared machine was not performance-isolated.

The seed is 2026. Each algorithm has nine measured trials per graph, following one excluded warmup batch. A trial creates a fresh dispatcher and executes the same 100 seeded source/destination queries three times. Algorithm order alternates across trials. The generated benchmark is an 8x8 grid with 64 nodes and 112 undirected edges. All 10,800 measured returned routes were verified.

Timings include dispatcher construction, A* coordinate/scale setup, first-use goal consistency checks, cached goal bounds on subsequent queries, search and routing counters. They exclude input/graph/oracle generation, correctness verification, CSV/JSON I/O and console output. This is a mixed setup-and-repeated-query workload, not a measurement of purely cold or purely warm single-route latency. It differs from the demo's ambulance-selection workflow, which can route from several vehicles per request.

| Graph | Algorithm | Median batch (ms) | Q1–Q3 (ms) | Min–max (ms) |
| --- | --- | ---: | ---: | ---: |
| Bundled, 7 nodes | Dijkstra | 13.726 | 11.876–17.983 | 10.386–21.100 |
| Bundled, 7 nodes | A* | 14.052 | 12.153–15.901 | 8.735–21.666 |
| Generated, 64 nodes | Dijkstra | 47.348 | 43.650–59.293 | 41.007–89.975 |
| Generated, 64 nodes | A* | 47.912 | 44.208–67.663 | 43.524–77.358 |

Quartiles use Python's inclusive method. The ranges overlap substantially. These observations support no general speed ranking, node-count cutoff, emergency response latency claim or statistical significance claim. Retiming will change numbers; retain the raw trials and actual environment when comparing variants. Seeded graph/query generation and verified outcomes are reproducible, wall-clock durations are not.

The earlier “Dijkstra is 16% faster” conclusion and sub-12 ms/real-world recommendations were removed: the previous implementation had correctness defects, no recorded environment/raw trials and an incorrect estimate of the bundled node count. Those numbers are not a valid baseline for the corrected search.

Benchmark CLI limits bound work: 3–15 trials, 1–500 queries, 1–10 repetitions, grid sides 2–15, an unsigned 32-bit seed and an additional operation-budget cap. `expansions` counts non-goal nodes expanded across the batch, and `seconds` is the full batch duration. The compatibility function `run_performance_test` instead returns bundled dispatch routing totals; do not mix that metric with the CLI batch timings.

Both recorded outputs include SHA-256 values for the four input files after UTF-8 BOM removal and newline normalization to LF, so Windows/Linux checkouts reconcile. They match the unchanged original Git inputs. `Data/ambulance_call_log.csv` is a legacy generated log, excluded from inputs and new evidence.

## Layout and references

`data_structures.py` and `data_loader.py` define validated fixtures; `dispatcher.py` owns priority/vehicle selection and logging; the two dispatcher wrappers select the heuristic; `routing.py` owns search. `experiments.py` supplies bounded seeded fixtures, the independent oracle and provenance; `demo.py` records verified dispatches; `performance_tester.py` records verified timing trials; `tests/` checks their contracts.

Foundational references: [Dijkstra (1959), A note on two problems in connexion with graphs](https://doi.org/10.1007/BF01386390); [Hart, Nilsson and Raphael (1968), A Formal Basis for the Heuristic Determination of Minimum Cost Paths](https://doi.org/10.1109/TSSC.1968.300136). The heuristic argument above specializes their search principles to this implementation's nonnegative static graph model.
