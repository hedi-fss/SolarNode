"""Routes module - Initialize and export blueprints"""

# Import route modules
try:
    from . import main
    main_bp = main.bp
except (ImportError, AttributeError) as e:
    print(f"Warning: Could not import main routes: {e}")
    main_bp = None

try:
    from . import api
    api_bp = api.bp
except (ImportError, AttributeError) as e:
    print(f"Warning: Could not import api routes: {e}")
    api_bp = None

# Optional: Import simulation and ml modules if they exist
try:
    from . import simulation
except ImportError:
    print("Note: simulation module not found (optional)")

try:
    from . import ml
except ImportError:
    print("Note: ml module not found (optional)")

# Export blueprints
__all__ = ['main_bp', 'api_bp']

# Log what was imported
if main_bp:
    print("[Routes] ✓ main_bp loaded")
if api_bp:
    print("[Routes] ✓ api_bp loaded")
