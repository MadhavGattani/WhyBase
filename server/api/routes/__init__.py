# server/api/routes/__init__.py
from flask import Blueprint

def register_routes(app):
    """Register all route blueprints"""
    from .queries import queries_bp
    from .templates import templates_bp
    from .uploads import uploads_bp
    from .organizations import organizations_bp
    from .export import export_bp
    
    app.register_blueprint(queries_bp, url_prefix='/api')
    app.register_blueprint(templates_bp, url_prefix='/api')
    app.register_blueprint(uploads_bp, url_prefix='/api')
    app.register_blueprint(organizations_bp, url_prefix='/api')
    app.register_blueprint(export_bp, url_prefix='/api')