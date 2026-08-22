"""Extensions module – avoids circular imports"""
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize extensions (without app context)
db = SQLAlchemy()
socketio = SocketIO(cors_allowed_origins="*")
limiter = Limiter(key_func=get_remote_address)
