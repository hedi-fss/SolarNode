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
    
    # Register blueprints - handle both naming conventions
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
            # Continue anyway, some blueprints might be optional
        
        # Create database tables
        try:
            logger.info("Creating database tables...")
            db.create_all()
            logger.info("✓ Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            # Don't fail - just warn
            pass
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return {'error': 'Internal server error'}, 500
    
    # Health check endpoint (fallback if not in blueprints)
    @app.route('/health')
    def health():
        return {'status': 'ok'}, 200
    
    logger.info("✓ Flask application created successfully")
    return app
