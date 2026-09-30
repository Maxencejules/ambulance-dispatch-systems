"""Repository-relative fixture and output paths; importing creates no files."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "Data"
AMBULANCE_FILE = DATA_DIR / "ambulance.csv"
NETWORK_FILE = DATA_DIR / "location_network.csv"
PRIORITY_FILE = DATA_DIR / "call_priority.csv"
CALLS_FILE = DATA_DIR / "calls.csv"
LOG_FILE = ROOT / "artifacts" / "dispatch.csv"