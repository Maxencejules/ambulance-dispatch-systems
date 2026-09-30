"""Validated standard-library CSV ingestion; defaults work from any directory."""
import csv
from pathlib import Path
from data_structures import Ambulance, EmergencyCall, CallPriorityQueue, RoadNetwork
import config


def _rows(filepath, required):
    path = Path(filepath)
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None or len(set(reader.fieldnames)) != len(reader.fieldnames) or not set(required).issubset(reader.fieldnames):
            raise ValueError(f"{path.name}: missing required columns {required}")
        for line, row in enumerate(reader, 2):
            if None in row or any(row.get(key) is None for key in required):
                raise ValueError(f"{path.name}:{line}: malformed CSV row")
            yield line, {key: row[key].strip() for key in required}


def load_ambulances(filepath=config.AMBULANCE_FILE):
    result, identifiers = [], set()
    for line, row in _rows(filepath, ["Ambulance Number", "Staging Location"]):
        identifier = row["Ambulance Number"]
        if not identifier or identifier in identifiers:
            raise ValueError(f"Ambulance row {line}: empty/duplicate identifier")
        identifiers.add(identifier)
        result.append(Ambulance(identifier, row["Staging Location"]))
    return result


def load_network(filepath=config.NETWORK_FILE):
    result = RoadNetwork()
    for line, row in _rows(filepath, ["Start", "End", "Distance", "Travel Time", "Traffic Delay"]):
        try:
            result.add_edge(row["Start"], row["End"], row["Distance"],
                            row["Travel Time"], row["Traffic Delay"])
        except ValueError as exc:
            raise ValueError(f"Network row {line}: {exc}") from exc
    return result


def load_priorities(filepath=config.PRIORITY_FILE):
    result = {}
    for line, row in _rows(filepath, ["Call Type", "Priority"]):
        try:
            priority = int(row["Priority"])
        except ValueError as exc:
            raise ValueError(f"Priority row {line}: invalid integer") from exc
        if not row["Call Type"] or row["Call Type"] in result or priority < 0:
            raise ValueError(f"Priority row {line}: empty/duplicate type or negative priority")
        result[row["Call Type"]] = priority
    return result


def load_calls(calls_filepath=config.CALLS_FILE, priorities_filepath=config.PRIORITY_FILE):
    priorities = load_priorities(priorities_filepath)
    result, identifiers = CallPriorityQueue(), set()
    for line, row in _rows(calls_filepath, ["Call ID", "Location", "Call Type"]):
        try:
            identifier = int(row["Call ID"])
        except ValueError as exc:
            raise ValueError(f"Call row {line}: invalid identifier") from exc
        if identifier in identifiers or row["Call Type"] not in priorities:
            raise ValueError(f"Call row {line}: duplicate identifier or unknown call type")
        identifiers.add(identifier)
        result.add_call(EmergencyCall(identifier, row["Location"], row["Call Type"],
                                     priorities[row["Call Type"]]))
    return result


def test_data_loading():
    return load_ambulances(), load_network(), load_calls()


if __name__ == "__main__":
    ambulances, network, calls = test_data_loading()
    print(network, f"{len(ambulances)} ambulances, {calls.size()} calls")