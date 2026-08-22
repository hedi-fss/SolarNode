"""SolarNode v2.0 Configuration"""
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent
# Ensure critical directories exist
DATA_DIR = BASE_DIR / 'data'
LOGS_DIR = BASE_DIR / 'logs'
DATA_DIR.mkdir(parents=True, exist_ok=True)  # ← ADD THIS
LOGS_DIR.mkdir(parents=True, exist_ok=True)   # ← ADD THIS
class Config:
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 5001
    
    # Database
    # Ensure directories exist
    data_dir = BASE_DIR / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)

    SQLALCHEMY_DATABASE_URI = f'sqlite:///{str(data_dir)}/solarnode.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Simulation
    AREA_KM = 5.0
    NODES_DEFAULT = 50
    RANGE_KM = 0.8
    GATEWAY_ID = 0
    MONTE_CARLO_RUNS = 100
    
    # Energy
    BATTERY_CAPACITY_MAH = 2000
    AVG_CURRENT_MA = 35.0
    SOLAR_MAX_MA = 40.0
    
    # 5G/6G
    NTN_ENABLED = True
    SATELLITE_BACKHAUL = True
    D2D_ENABLED = True
    
    # ML
    ANOMALY_THRESHOLD = 0.7
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = BASE_DIR / 'logs/solarnode.log'
    
    # Rate Limiting
    RATE_LIMIT_DEFAULT = "100 per minute"

config = Config()

# Rate limiting with Redis (optional)
# Uncomment if Redis is installed
# REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
