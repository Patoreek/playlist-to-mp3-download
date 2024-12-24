from . import create_app  # Use a relative import to refer to the create_app function in __init__.py

app = create_app()

@app.route('/')
def serve_root():
    return '''
    <h1>Welcome to the Playlist to MP3 API!</h1>
    <p>This API allows you to grab Spotify or SoundCloud playlists (and more) and generate MP3 files for you to download.</p>
    <p>Simply provide the playlist URL or track ID, and we'll handle the rest, delivering downloadable MP3s for each track.</p>
    '''

if __name__ == '__main__':
    app.run(debug=True)