#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import logging first
from app.logging_config import logger

try:
    from app import create_app, socketio
    from config import config

    app = create_app()

    if __name__ == '__main__':
        port = int(os.environ.get('PORT', config.PORT))
        logger.info(f"Starting SolarNode v2.0 on port {port}")
        # Removed allow_unsafe_werkzeug - not valid for eventlet
        socketio.run(app, host='0.0.0.0', port=port, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)
except Exception as e:
    logger.exception("Failed to start application")
    raise
