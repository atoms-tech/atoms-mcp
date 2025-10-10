"""
Site customization to add vendored pheno-sdk packages to sys.path.

This file is automatically loaded by Python at startup and ensures
vendored packages in pheno_vendor/ are available for import.
"""

import sys
from pathlib import Path

# Add pheno_vendor to path if it exists
vendor_path = Path(__file__).parent / "pheno_vendor"
if vendor_path.exists() and str(vendor_path) not in sys.path:
    sys.path.insert(0, str(vendor_path))
