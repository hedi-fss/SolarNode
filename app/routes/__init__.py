def register_blueprints(app):
    from .main import bp as main_bp
    app.register_blueprint(main_bp)
    print("[Routes] ✓ main_bp loaded")

    try:
        from .api import bp as api_bp
        app.register_blueprint(api_bp)
        print("[Routes] ✓ api_bp loaded")
    except Exception as e:
        print(f"Warning: Could not import api routes: {e}")

    try:
        from .ml import bp as ml_bp
        # name check prevents double-registration
        if 'ml' not in app.blueprints:
            app.register_blueprint(ml_bp)
            print("[Routes] ✓ ml_bp loaded")
        else:
            print("[Routes] ⚠ ml_bp already registered, skipping")
    except Exception as e:
        print(f"Note: ml module not found (optional): {e}")
