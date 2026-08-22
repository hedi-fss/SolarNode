"""Routes module - Initialize and export blueprints"""
from flask import Blueprint

# Create blueprints
main_bp = Blueprint('main', __name__)
api_bp = Blueprint('api', __name__, url_prefix='/api')
websocket_bp = Blueprint('websocket', __name__)

# Import route handlers (if they exist)
try:
    from app.routes.main import *
except ImportError:
    pass

try:
    from app.routes.api import *
except ImportError:
    pass

try:
    from app.routes.websocket import *
except ImportError:
    pass

# Export blueprints
__all__ = ['main_bp', 'api_bp', 'websocket_bp']
