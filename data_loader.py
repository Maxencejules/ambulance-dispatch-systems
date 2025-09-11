"""
Data loading utilities for ambulance dispatch system
"""
import pandas as pd
from data_structures import EmergencyCall, Ambulance, CallPriorityQueue, RoadNetwork
import config


def load_ambulances(filepath=config.AMBULANCE_FILE):
    """Load ambulances from CSV file"""
    ambulances = []
    df = pd.read_csv(filepath)

    for _, row in df.iterrows():
        ambulance = Ambulance(
            ambulance_id=row['Ambulance Number'],
            staging_location=row['Staging Location']
        )
        ambulances.append(ambulance)

    print(f"Loaded {len(ambulances)} ambulances")
    return ambulances


def load_network(filepath=config.NETWORK_FILE):
    """Load road network from CSV file"""
    network = RoadNetwork()
    df = pd.read_csv(filepath)

    for _, row in df.iterrows():
        network.add_edge(
            start=row['Start'],
            end=row['End'],
            distance=row['Distance'],
            travel_time=row['Travel Time'],
            traffic_delay=row['Traffic Delay']
        )

    print(f"Loaded network: {network}")
    return network


def load_priorities(filepath=config.PRIORITY_FILE):
    """Load call priorities from CSV file"""
    priorities = {}
    df = pd.read_csv(filepath)

    for _, row in df.iterrows():
        priorities[row['Call Type']] = row['Priority']

    print(f"Loaded {len(priorities)} call type priorities")
    return priorities


def load_calls(calls_filepath=config.CALLS_FILE, priorities_filepath=config.PRIORITY_FILE):
    """Load emergency calls from CSV file"""
    # First load priorities
    priorities = load_priorities(priorities_filepath)

    # Then load calls
    call_queue = CallPriorityQueue()
    df = pd.read_csv(calls_filepath)

    for _, row in df.iterrows():
        call = EmergencyCall(
            call_id=row['Call ID'],
            location=row['Location'],
            call_type=row['Call Type'],
            priority=priorities[row['Call Type']]
        )
        call_queue.add_call(call)

    print(f"Loaded {call_queue.size()} emergency calls")
    return call_queue


def test_data_loading():
    """Test that all data files load correctly"""
    print("\n=== Testing Data Loading ===")
    ambulances = load_ambulances()
    network = load_network()
    priorities = load_priorities()
    calls = load_calls()

    print("\nSample ambulance:", ambulances[0])
    print("Sample network neighbors:", list(network.graph.keys())[:3])
    print("Sample call:", calls.get_next_call())
    print("\n=== Data Loading Test Complete ===\n")

    return ambulances, network, calls


if __name__ == "__main__":
    test_data_loading()