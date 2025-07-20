"""
Example of how to register the NoCodeBackend blueprint in your Flask app
"""

from flask import Flask
from routes.nocode_routes import nocode_api

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Register blueprints
    app.register_blueprint(nocode_api)
    
    # Example route
    @app.route('/')
    def index():
        return 'Sapyyn Patient Referral System'
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)