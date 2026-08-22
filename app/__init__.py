"""SolarNode Flask Application Factory"""
import os
from pathlib import Path
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
socketio = SocketIO(cors_allowed_origins="*")
limiter = Limiter(key_func=get_remote_address)

def create_app():
    """Application factory function"""
    
    # Configure template and static paths
    app_dir = Path(__file__).parent.parent
    template_dir = app_dir / 'templates'
    static_dir = app_dir / 'static'
    
    print(f"[Flask] Template folder: {template_dir}")
    print(f"[Flask] Static folder: {static_dir}")
    print(f"[Flask] Template dir exists: {template_dir.exists()}")
    if template_dir.exists():
        print(f"[Flask] Templates in dir: {list(template_dir.glob('*.html'))}")
    
    # Create Flask app with explicit paths
    app = Flask(
        __name__,
        template_folder=str(template_dir),
        static_folder=str(static_dir),
        static_url_path='/static'
    )
    
    # Load configuration
    from config import config
    app.config.from_object(config)
    
    # Ensure data directory exists
    data_dir = Path(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
    data_dir.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    socketio.init_app(app, async_mode='eventlet')
    limiter.init_app(app)
    
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
    
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return {'error': 'Internal server error'}, 500
    
    @app.route('/health')
    def health():
        return {'status': 'ok'}, 200
    
    logger.info("✓ Flask application created successfully")
    return app
