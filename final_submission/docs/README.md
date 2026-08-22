# SolarNode v2.0

## 🌞 5G/6G-Native, AI-Powered Disaster Communication Mesh

SolarNode is a solar-powered, self‑healing mesh network designed for post‑disaster emergency communication.

## Key Features

- **5G/6G Integration** – NTN satellite backhaul, D2D fallback, ISAC sensing
- **AI‑Powered Analytics** – Anomaly detection, failure prediction, recommendations
- **Interactive Dashboard** – Flask + WebSocket + D3.js visualisation
- **Energy Autonomy** – Solar harvesting, 142‑hour network lifetime
- **High Performance** – 94% PDR, 2.5× lifetime improvement

## Installation

```bash
conda env create -f environment.yml
conda activate solarnode2
export PORT=5001
python run.py
Testing
bash

python test_full.py

API Documentation

See Swagger UI (if enabled) or the inline docstrings.
Team

    Emna (Team Leader)

    Khadija (Hardware)

    Hedi (Software)

License

MIT

---

### Step 3: API Documentation (Swagger/OpenAPI)

We'll add Flask-RESTX (or flasgger) for Swagger UI.

```bash
cd ~/solarnode_v2
conda activate solarnode2
pip install flasgger

# Create a new blueprint for API docs
cat > app/routes/docs.py << 'EOF'
"""API Documentation using Flasgger"""
from flask import Blueprint, jsonify
from flasgger import Swagger, swag_from

bp = Blueprint('docs', __name__, url_prefix='/api')

# Swagger template
template = {
    "swagger": "2.0",
    "info": {
        "title": "SolarNode v2.0 API",
        "description": "API for SolarNode disaster communication mesh",
        "version": "2.0.0",
        "contact": {
            "name": "SolarNode Team",
            "email": "emna@university.edu"
        }
    },
    "host": "localhost:5001",
    "basePath": "/api",
    "schemes": ["http"],
    "consumes": ["application/json"],
    "produces": ["application/json"]
}

swagger = Swagger(template=template)

@bp.route('/docs')
def get_docs():
    """Redirect to Swagger UI"""
    return jsonify({"message": "Swagger UI available at /apidocs"})
