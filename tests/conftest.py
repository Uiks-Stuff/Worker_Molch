import sys
from pathlib import Path

# Projektwurzel importierbar machen (core, modules, main).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
