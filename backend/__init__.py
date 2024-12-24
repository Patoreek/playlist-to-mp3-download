from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)

    # Registering API blueprints for different services
    from .api.spotify.endpoints import spotify_blueprint
    from .api.youtube.endpoints import youtube_blueprint

    # Register each blueprint with a unique URL prefix
    app.register_blueprint(spotify_blueprint, url_prefix='/api/spotify')
    app.register_blueprint(youtube_blueprint, url_prefix='/api/youtube')

    return app