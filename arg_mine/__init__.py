import os
from pathlib import Path

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = Path(SRC_DIR).resolve().parent
