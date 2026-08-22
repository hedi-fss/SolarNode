# SolarNode Blueprint Fix Guide

## Problem Identified

Your route files use `bp` but the app is looking for `main_bp` and `api_bp`:

- `app/routes/main.py` → `bp = Blueprint('main', __name__)`
- `app/routes/api.py` → `bp = Blueprint('api', __name__)`
- `app/__init__.py` → trying to import `from app.routes import main_bp, api_bp` ❌

**Solution:** Rename `bp` to the expected names when importing.

---

## Fix Steps

### Step 1: Update `app/routes/__init__.py`

Replace your entire `app/routes/__init__.py` with this:

```python
"""Routes module - Initialize and export blueprints"""

# Import route modules
try:
    from . import main
    main_bp = main.bp  # Rename bp to main_bp
except (ImportError, AttributeError) as e:
    print(f"Warning: Could not import main routes: {e}")
    main_bp = None

try:
    from . import api
    api_bp = api.bp  # Rename bp to api_bp
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
```

---

### Step 2: Update `app/__init__.py`

Replace your `create_app()` function with this:

```python
"""SolarNode Flask Application Factory"""
import os
from pathlib import Path
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize extensions
db = SQLAlchemy()
socketio = SocketIO(cors_allowed_origins="*")
limiter = Limiter(key_func=get_remote_address)

def create_app():
    """Application factory function"""
    
    app = Flask(__name__)
    
    # Load configuration
    from config import config
    app.config.from_object(config)
    
    # Ensure data directory exists
    data_dir = Path(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
    data_dir.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize extensions with app
    db.init_app(app)
    socketio.init_app(app, async_mode='eventlet')
    limiter.init_app(app)
    
    # Import logging configuration
    from app.logging_config import logger
    
    # Register blueprints
    with app.app_context():
        try:
            from app.routes import main_bp, api_bp
            
            if main_bp:
                app.register_blueprint(main_bp)
                logger.info("✓ Registered main_bp blueprint")
            
            if api_bp:
                app.register_blueprint(api_bp, url_prefix='/api')
                logger.info("✓ Registered api_bp blueprint")
                
        except ImportError as e:
            logger.warning(f"Blueprint import issue: {e}")
        
        # Create database tables
        try:
            logger.info("Creating database tables...")
            db.create_all()
            logger.info("✓ Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return {'error': 'Internal server error'}, 500
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return {'status': 'ok'}, 200
    
    logger.info("✓ Flask application created successfully")
    return app
```

---

### Step 3: Update `run.py`

Make sure your `run.py` looks like this:

```python
#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.logging_config import logger

try:
    from app import create_app, socketio
    from config import config

    app = create_app()

    if __name__ == '__main__':
        port = int(os.environ.get('PORT', config.PORT))
        logger.info(f"Starting SolarNode v2.0 on port {port}")
        socketio.run(app, host='0.0.0.0', port=port, debug=True)
except Exception as e:
    logger.exception("Failed to start application")
    raise
```

---

### Step 4: Restart Docker

```bash
# Stop and rebuild
docker compose down
docker compose build --no-cache

# Start fresh
docker compose up
```

---

## Expected Output

You should see:

```
solarnode_v2  | Starting SolarNode v2.0 on port 5001
solarnode_v2  | [Routes] ✓ main_bp loaded
solarnode_v2  | [Routes] ✓ api_bp loaded
solarnode_v2  | ✓ Database tables created successfully
solarnode_v2  | ✓ Flask application created successfully
```

**NOT:**
```
Cannot import name 'main_bp' from 'app.routes'
```

---

## Test the API

```bash
# Test health check
curl http://localhost:5001/health
# Expected: {"status":"ok"}

# Test main route
curl http://localhost:5001/
# Expected: (should render index.html)

# Test API routes
curl http://localhost:5001/api/nodes
curl http://localhost:5001/api/nodes/active
```

---

## Remaining Issue: numpy._core

Once the blueprints are fixed, you'll still see:
```
⚠️ Could not load models: No module named 'numpy._core'
```

This is because something in your code is trying to use numpy features that don't exist in numpy 1.24.3.

**Common causes:**
1. Models using pandas/numpy internals
2. Services importing numpy incorrectly

To fix this, share:
```bash
head -30 app/models.py
head -30 app/services/analytics.py
```

And I'll fix the numpy import.

---

## Summary

| File | Change |
|------|--------|
| `app/routes/__init__.py` | Import modules and rename `bp` to `main_bp` and `api_bp` |
| `app/__init__.py` | Update to properly register blueprints |
| `run.py` | Remove `allow_unsafe_werkzeug` argument |

Once these 3 files are updated and Docker restarts, the blueprint warnings will disappear! ✅
