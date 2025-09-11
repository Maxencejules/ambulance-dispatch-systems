# Ambulance Dispatch Route Optimizer

A comparative analysis of pathfinding algorithms for emergency vehicle dispatch systems, implementing and benchmarking Dijkstra's algorithm versus A* search for optimal ambulance routing.

## 📊 Key Findings

- **Dijkstra outperformed A* by 16%** on small road networks (< 50 nodes)
- Both algorithms achieve sub-12ms routing times for 100 emergency calls
- Heuristic overhead exceeded search space reduction benefits in dense, small networks

## 🚑 Project Overview

This system simulates emergency ambulance dispatch operations, processing prioritized emergency calls and computing optimal routes from staging locations to incident sites. The project compares two fundamental shortest-path algorithms to determine which performs better for real-world emergency response scenarios.

### Features

- **Priority-based dispatch queue** using min-heap for call triage
- **Real-time route calculation** with traffic delay considerations
- **Comparative algorithm analysis** with performance benchmarking
- **Comprehensive dispatch logging** with route details and response times
- **Graph-based road network** representation with bidirectional edges

## 🛠️ Technology Stack

- **Language:** Python 3.x
- **Data Processing:** Pandas
- **Algorithms:** Dijkstra's Algorithm, A* Search
- **Data Structures:** Priority Queue (heapq), Graph (adjacency list)

## 📁 Project Structure

```
ambulance-dispatch-optimizer/
├── README.md
├── requirements.txt
├── config.py                    # Configuration and file paths
├── data_structures.py           # Core data structures
├── data_loader.py              # CSV data ingestion
├── dijkstra_dispatcher.py     # Dijkstra implementation
├── astar_dispatcher.py        # A* implementation  
├── performance_tester.py      # Benchmarking suite
└── data/
    ├── ambulance.csv          # Ambulance staging locations
    ├── calls.csv              # Emergency call data
    ├── call_priority.csv      # Call type priorities
    └── location_network.csv   # Road network graph
```

## 🚀 Getting Started

### Prerequisites

```bash
python --version  # Python 3.7 or higher
pip --version     # pip package manager
```

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Maxencejules/ambulance-dispatch-system.git
cd ambulance-dispatch-optimizer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Simulation

**Run Dijkstra's Algorithm:**
```bash
python dijkstra_dispatcher.py
```

**Run A* Algorithm:**
```bash
python astar_dispatcher.py
```

**Run Performance Comparison:**
```bash
python performance_tester.py
```

## 📈 Performance Results

### Benchmark Summary (100 Emergency Calls, 10 Runs Each)

| Algorithm | Average Time | Min Time | Max Time | Variance |
|-----------|-------------|----------|----------|----------|
| **Dijkstra** | 0.007652s | 0.004628s | 0.009766s | 53% |
| **A*** | 0.008879s | 0.006393s | 0.011228s | 43% |

**Performance Difference:** Dijkstra performed 16% faster (1.227ms improvement)

### Why Dijkstra Outperformed A*

1. **Network Scale:** With only 42 edges and ~20 nodes, overhead costs dominate
2. **High Connectivity:** Average degree of 4.2 means most destinations are 3-4 hops away
3. **Heuristic Overhead:** A* requires coordinate lookups and distance calculations (~0.012ms/node)

## 🔬 Algorithm Implementations

### Dijkstra's Algorithm
- **Strategy:** Greedy best-first expansion using min-heap
- **Complexity:** O((V+E)log V) time, O(V) space
- **Guarantee:** Optimal paths for non-negative edge weights
- **Best for:** Small networks, consistent performance requirements

### A* Algorithm
- **Strategy:** Informed search using f(n) = g(n) + h(n) scoring
- **Heuristic:** Conservative Manhattan distance with admissibility guarantee
- **Complexity:** O((V+E)log V) worst case, O(b^d) average
- **Best for:** Large sparse networks with good spatial structure

## 🎯 System Design

### Core Components

1. **EmergencyCall**: Tracks call details with priority levels
2. **Ambulance**: Manages vehicle state and availability
3. **CallPriorityQueue**: Min-heap implementation for call triage
4. **RoadNetwork**: Graph representation using adjacency lists

### Dispatch Workflow

1. Load road network and ambulance staging locations
2. Ingest emergency calls with priority mapping
3. Process calls in priority order (lower number = higher priority)
4. For each call:
   - Calculate routes from all available ambulances
   - Select ambulance with minimum response time
   - Log dispatch details and reset ambulance

## 💡 Future Improvements

### Dijkstra Optimizations
- **Bidirectional Search:** Expected 40-45% improvement
- **Early Termination:** Stop at destination (20-30% improvement)
- **Route Caching:** LRU cache for common routes (60-70% of calls are recurring)

### A* Enhancements
- **Improved Heuristic:** Landmark-based or true road distance
- **Weighted A* (ε=1.5):** Trade optimality for speed
- **Hierarchical Preprocessing:** Multi-scale heuristics

### System Extensions
- Real-time traffic updates
- Multiple ambulance coordination
- Dynamic ambulance repositioning
- Visualization dashboard

## 📊 Data Format

### Input Files

**ambulance.csv:**
```csv
Ambulance Number,Staging Location
Ambulance 1,Hospital A
Ambulance 2,Fire Station B
```

**calls.csv:**
```csv
Call ID,Location,Call Type
1,Intersection D,Stroke
2,Address 456 Oak St,Cardiac Arrest
```

**location_network.csv:**
```csv
Start,End,Distance,Travel Time,Traffic Delay
Hospital A,Intersection B,2.5,3.2,1
```

## 🔍 Key Insights

The 1.227ms performance difference between algorithms is negligible compared to real-world factors:
- Ambulance travel time: 5-15 minutes
- Dispatch decision time: 15-30 seconds
- Communication overhead: 30-60 seconds

**Recommendation:** Use Dijkstra for networks under 100 nodes, A* for larger networks where guided search provides measurable benefits.

## 📚 References

- Dijkstra, E. W. (1959). A note on two problems in connexion with graphs. *Numerische Mathematik*, 1(1), 269-271.
- Hart, P. E., Nilsson, N. J., & Raphael, B. (1968). A formal basis for the heuristic determination of minimum cost paths. *IEEE Transactions on Systems Science and Cybernetics*, 4(2), 100-107.
- Cormen, T. H., et al. (2009). *Introduction to Algorithms* (3rd ed.). MIT Press.

## 📄 License

This project is available under the MIT License. See LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## 👤 Author

**Maxence Jules**

- GitHub: Maxencejules(https://github.com/Maxencejules)
- LinkedIn: Maxence Jules(https://linkedin.com/in/julesmax)
- Email: powe840@gmail.com

---

*This project demonstrates algorithm selection considerations for emergency response systems, showing that theoretical complexity isn't everything - implementation details and network characteristics significantly impact real-world performance.*