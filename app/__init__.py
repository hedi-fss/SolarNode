import os
from flask import Flask, jsonify
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
socketio = SocketIO()
limiter = Limiter(key_func=get_remote_address)

def create_app():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_dir = os.path.join(base_dir, 'frontend', 'templates')
    static_dir   = os.path.join(base_dir, 'frontend', 'static')

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

    from config import config
    app.config.from_object(config)

    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*", async_mode='threading')
    limiter.init_app(app)

    from app.routes import register_blueprints
    register_blueprints(app)

    @app.errorhandler(Exception)
    def handle_exception(e):
        import traceback
        from werkzeug.exceptions import HTTPException
        code = e.code if isinstance(e, HTTPException) else 500
        return jsonify({
            'status': 'error',
            'message': str(e),
        }), code

    return app
