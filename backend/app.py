from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/get-spotify-playlist/<playlist_id>')
def get_spotify_playlist(playlist_id):
    print(f"Received playlist ID: {playlist_id}")
    
    return jsonify({'message': 'Playlist ID received!', 'playlist_id': playlist_id})

@app.route('/api/data')
def get_data():
    return jsonify({'message': 'Hello from Flask!', 'status': 'success'})

# Serve the Svelte built files
@app.route('/<path:path>')
def serve_frontend(path):
    return send_from_directory('../frontend/dist', path)

@app.route('/')
def serve_root():
    return '''
    <h1>Welcome to the Playlist to MP3 API!</h1>
    <p>This API allows you to grab Spotify playlists (and more) and generate MP3 files for you to download.</p>
    <p>Simply provide the playlist URL, and we'll handle the rest, delivering downloadable MP3s for each track.</p>
    '''

if __name__ == '__main__':
    app.run(debug=True)