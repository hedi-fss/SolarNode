import os
from flask import Flask, jsonify
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy import inspect, text

db = SQLAlchemy()
socketio = SocketIO()
limiter = Limiter(key_func=get_remote_address)

def _reconcile_telemetry_schema_for_sqlite(app):
    database_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if not database_uri.startswith('sqlite:///'):
        return

    inspector = inspect(db.engine)
    if 'telemetry' not in inspector.get_table_names():
        return

    existing_columns = {column['name'] for column in inspector.get_columns('telemetry')}
    if 'id' in existing_columns:
        return

    target_columns = [
        'node_id', 'timestamp', 'latitude', 'longitude', 'altitude', 'battery',
        'temperature', 'humidity', 'light', 'packet_type', 'hop_count'
    ]
    columns_to_copy = [column for column in target_columns if column in existing_columns]
    insert_columns = ', '.join(columns_to_copy)
    select_columns = ', '.join(columns_to_copy)

    with db.engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE telemetry__new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_id INTEGER,
                timestamp DATETIME,
                latitude FLOAT,
                longitude FLOAT,
                altitude FLOAT,
                battery FLOAT,
                temperature FLOAT,
                humidity FLOAT,
                light FLOAT,
                packet_type VARCHAR(20),
                hop_count INTEGER
            )
        """))
        if columns_to_copy:
            connection.execute(text(
                f"INSERT INTO telemetry__new ({insert_columns}) "
                f"SELECT {select_columns} FROM telemetry"
            ))
        connection.execute(text("DROP TABLE telemetry"))
        connection.execute(text("ALTER TABLE telemetry__new RENAME TO telemetry"))

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

    with app.app_context():
        db.create_all()
        _reconcile_telemetry_schema_for_sqlite(app)

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
