"""Explainable smart-parking modules."""
import sys
from pathlib import Path
_local_dependencies=Path(__file__).resolve().parents[2]/'dependencies/python'
if _local_dependencies.exists():sys.path.insert(0,str(_local_dependencies))
