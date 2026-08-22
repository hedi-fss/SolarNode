"""SolarNode v2.0 Application"""
from flask import Flask
from config import config
import warnings
warnings.filterwarnings("ignore")
from app.extensions import db, socketio, limiter

def create_app():
    app = Flask(__name__,
                template_folder='../frontend/templates',
                static_folder='../frontend/static')
    app.config.from_object(config)
    db.init_app(app)
    socketio.init_app(app)
    limiter.init_app(app)

    from app.routes import main, api, simulation, ml, docs
    app.register_blueprint(main.bp)
    app.register_blueprint(api.bp, url_prefix='/api')
    app.register_blueprint(simulation.bp, url_prefix='/simulation')
    app.register_blueprint(ml.bp, url_prefix='/ml')
    app.register_blueprint(docs.bp, url_prefix='/api')  # docs blueprint uses /api prefix

    with app.app_context():
        db.create_all()
    return app
    from app.routes import docs
    app.register_blueprint(docs.bp)
