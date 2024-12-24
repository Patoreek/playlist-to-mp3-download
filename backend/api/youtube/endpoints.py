import requests
import time
from flask import Blueprint, jsonify, request

# Authorization blueprint
youtube_blueprint = Blueprint('youtube', __name__)
    
# Example function that processes the song names
def get_youtube_links_from_songs(song_names):
    # For simplicity, let's assume this just returns the songs with " - Extended"
    return [f"{song} - Extended" for song in song_names]


@youtube_blueprint.route('/get-links', methods=['POST'])
def get_youtube_links():
    # Get the JSON data from the request
    data = request.get_json()
    print(data)
    # Ensure the data contains the 'songNames' field (an array of strings)
    if not data or 'songNames' not in data:
        return jsonify({'message': 'Invalid request, no songNames found'}), 400

    song_names = data['songNames']
    
    # Process the song names to add ' - Extended' to each one
    youtube_links = get_youtube_links_from_songs(song_names)

    # Return the YouTube links in the response
    return jsonify({
        'message': 'Youtube Links created!',
        'tracks': youtube_links,
    })