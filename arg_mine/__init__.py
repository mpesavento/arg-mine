import os
from pathlib import Path

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = Path(MODULE_DIR).resolve().parent
DATA_DIR = os.path.join(PROJECT_DIR, "data")
REPORTS_DIR = os.path.join(PROJECT_DIR, "reports")
FIGURES_DIR = os.path.join(REPORTS_DIR, "figures")
