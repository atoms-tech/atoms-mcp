"""Auto-generated Pydantic models from Supabase.

To generate models, run:
    python scripts/generate_schemas.py

Or use the simple version:
    python scripts/generate_schemas_simple.py
"""

# Import all generated models when they exist
try:
    from .models import *  # noqa: F401, F403
    from .models import __all__
except ImportError:
    # Models not generated yet
    __all__ = []
    import warnings
    warnings.warn(
        "Generated models not found. Run: python scripts/generate_schemas.py",
        UserWarning,
        stacklevel=2
    )

