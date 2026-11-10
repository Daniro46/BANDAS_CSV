"""Project paths used by the BANDAS converter."""

from pathlib import Path

# Scrips/Extras/bandas_csv/core/01_paths.py -> parents[4] is the project root.
PROJECT_ROOT = Path(__file__).resolve().parents[4]
BANDAS_DIR = PROJECT_ROOT / "Data Base" / "BANDAS" / "Bases_Datos_Bandas"
DEFAULT_OUT = PROJECT_ROOT / "Data Base" / "BANDAS" / "Bases_Datos_Bandas_CSV"
