import os
import json
import re
import requests
import yt_dlp
from flask import Flask, render_template, request, redirect, url_for, session, send_file, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin')

# Add ngrok skip warning header to all responses
@app.after_request
def add_ngrok_header(response):
    response.headers['ngrok-skip-browser-warning'] = 'true'
    return response

# Directories
DOWNLOADS_DIR = Path('downloads')
DOWNLOADS_DIR.mkdir(exist_ok=True)
DATA_FILE = Path('data.json')

# Initialize data file
if not DATA_FILE.exists():
    DATA_FILE.write_text(json.dumps({'playlists': []}, indent=2))


def load_data():
    """Load playlists data from JSON file."""
    with open(DATA_FILE, 'r') as f:
        return json.load(f)


def save_data(data):
    """Save playlists data to JSON file."""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def extract_apple_music_playlist_id(url):
    """Extract playlist ID from Apple Music URL."""
    # Apple Music playlist URL format: https://music.apple.com/*/playlist/*/pl.*
    match = re.search(r'pl\.[a-zA-Z0-9-]+', url)
    if match:
        return match.group(0)
    return None


def search_youtube(song_name, artist_name):
    """Search YouTube for a song and return the first result URL."""
    query = f"{song_name} {artist_name} official audio"

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(f"ytsearch1:{query}", download=False)
            if result and 'entries' in result and len(result['entries']) > 0:
                video = result['entries'][0]
                return f"https://www.youtube.com/watch?v={video['id']}"
    except Exception as e:
        print(f"Error searching YouTube: {e}")

    return None


def download_from_youtube(youtube_url, output_path):
    """Download audio from YouTube as MP3."""

    # Check if cookies file exists
    cookies_file = Path('cookies.txt')

    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': str(output_path.with_suffix('')),
        'quiet': False,
        'no_warnings': False,
        'writethumbnail': False,
        'extract_audio': True,
    }

    # Try multiple strategies for cookie authentication
    strategies = []

    # Strategy 1: Use cookies.txt if it exists
    if cookies_file.exists():
        strategy_opts = ydl_opts.copy()
        strategy_opts['cookiefile'] = str(cookies_file)
        strategies.append(("cookies.txt file", strategy_opts))

    # Strategy 2: Try Chrome browser cookies (only works locally)
    chrome_check = Path.home() / '.config' / 'google-chrome'
    if chrome_check.exists() or Path('/Applications/Google Chrome.app').exists():
        strategy_opts = ydl_opts.copy()
        strategy_opts['cookiesfrombrowser'] = ('chrome',)
        strategies.append(("Chrome browser cookies", strategy_opts))

    # Strategy 3: Try without cookies (fallback)
    strategies.append(("no authentication", ydl_opts.copy()))

    # Try each strategy until one works
    for strategy_name, opts in strategies:
        try:
            print(f"Attempting download using {strategy_name}...")
            print(f"Downloading from: {youtube_url}")
            print(f"Output path: {output_path}")

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(youtube_url, download=True)

            # Check if the mp3 file was created
            if output_path.exists():
                print(f"✓ File created successfully: {output_path}")
                return True
            else:
                print(f"✗ File not created at expected path: {output_path}")
                # Check if file exists without extension
                base_path = output_path.with_suffix('')
                if base_path.exists():
                    print(f"Found file without .mp3 extension, renaming...")
                    base_path.rename(output_path)
                    return True
        except Exception as e:
            print(f"Strategy '{strategy_name}' failed: {e}")
            # Continue to next strategy
            continue

    # All strategies failed
    print(f"Error: All download strategies failed for {youtube_url}")
    print("Tip: For better reliability, export YouTube cookies to cookies.txt file")
    return False


def parse_apple_music_playlist(url):
    """
    Parse Apple Music playlist URL and return list of songs.
    Note: This is a simplified version. Real implementation would need
    Apple Music API or web scraping.
    """
    # This is a placeholder - in production, you'd use Apple Music API
    # or scrape the webpage
    return []


# ============ PUBLIC ROUTES ============

@app.route('/')
def index():
    """Public homepage showing all playlists."""
    data = load_data()
    return render_template('index.html', playlists=data['playlists'])


@app.route('/playlist/<int:playlist_id>')
def view_playlist(playlist_id):
    """View songs in a specific playlist."""
    data = load_data()

    if playlist_id >= len(data['playlists']):
        return "Playlist not found", 404

    playlist = data['playlists'][playlist_id]
    return render_template('playlist.html', playlist=playlist, playlist_id=playlist_id)


@app.route('/download/<int:playlist_id>/<int:song_id>')
def download_song(playlist_id, song_id):
    """Download a specific song as MP3."""
    data = load_data()

    if playlist_id >= len(data['playlists']):
        return "Playlist not found", 404

    playlist = data['playlists'][playlist_id]

    if song_id >= len(playlist['songs']):
        return "Song not found", 404

    song = playlist['songs'][song_id]
    file_path = DOWNLOADS_DIR / song['filename']

    if not file_path.exists():
        return "File not found", 404

    return send_file(
        file_path,
        as_attachment=True,
        download_name=song['filename'],
        mimetype='audio/mpeg'
    )


# ============ ADMIN ROUTES ============

@app.route('/admin')
def admin_login():
    """Admin login page."""
    if 'admin' in session:
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html')


@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    """Handle admin login."""
    password = request.form.get('password')

    if password == ADMIN_PASSWORD:
        session['admin'] = True
        return redirect(url_for('admin_dashboard'))

    return render_template('admin_login.html', error='Invalid password')


@app.route('/admin/logout')
def admin_logout():
    """Admin logout."""
    session.pop('admin', None)
    return redirect(url_for('index'))


@app.route('/admin/dashboard')
def admin_dashboard():
    """Admin dashboard showing all playlists."""
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    data = load_data()
    return render_template('admin_dashboard.html', playlists=data['playlists'])


@app.route('/admin/add-playlist', methods=['GET', 'POST'])
def admin_add_playlist():
    """Add a new playlist from Apple Music URL."""
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        playlist_url = request.form.get('playlist_url')
        playlist_name = request.form.get('playlist_name')

        if not playlist_url or not playlist_name:
            return render_template('admin_add_playlist.html', error='Please provide both URL and name')

        # For now, create empty playlist - songs will be added manually
        data = load_data()
        data['playlists'].append({
            'name': playlist_name,
            'url': playlist_url,
            'songs': []
        })
        save_data(data)

        return redirect(url_for('admin_dashboard'))

    return render_template('admin_add_playlist.html')


@app.route('/admin/playlist/<int:playlist_id>/add-song', methods=['GET', 'POST'])
def admin_add_song(playlist_id):
    """Add a song to a playlist."""
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    data = load_data()

    if playlist_id >= len(data['playlists']):
        return "Playlist not found", 404

    if request.method == 'POST':
        song_name = request.form.get('song_name')
        artist_name = request.form.get('artist_name')

        if not song_name or not artist_name:
            return render_template('admin_add_song.html',
                                 playlist_id=playlist_id,
                                 error='Please provide both song and artist name')

        # Search YouTube
        youtube_url = search_youtube(song_name, artist_name)

        if not youtube_url:
            return render_template('admin_add_song.html',
                                 playlist_id=playlist_id,
                                 error='Could not find song on YouTube')

        # Generate filename
        safe_name = re.sub(r'[^\w\s-]', '', f"{song_name}-{artist_name}")
        safe_name = re.sub(r'[-\s]+', '-', safe_name)
        filename = f"{safe_name}.mp3"

        # Download from YouTube
        output_path = DOWNLOADS_DIR / filename
        success = download_from_youtube(youtube_url, output_path)

        if not success:
            return render_template('admin_add_song.html',
                                 playlist_id=playlist_id,
                                 error='Failed to download from YouTube')

        # Add to playlist
        data['playlists'][playlist_id]['songs'].append({
            'name': song_name,
            'artist': artist_name,
            'filename': filename,
            'youtube_url': youtube_url
        })
        save_data(data)

        return redirect(url_for('admin_dashboard'))

    return render_template('admin_add_song.html', playlist_id=playlist_id)


@app.route('/admin/playlist/<int:playlist_id>/delete', methods=['POST'])
def admin_delete_playlist(playlist_id):
    """Delete a playlist and its songs."""
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    data = load_data()

    if playlist_id >= len(data['playlists']):
        return "Playlist not found", 404

    playlist = data['playlists'][playlist_id]

    # Delete all song files
    for song in playlist['songs']:
        file_path = DOWNLOADS_DIR / song['filename']
        if file_path.exists():
            file_path.unlink()

    # Remove from data
    data['playlists'].pop(playlist_id)
    save_data(data)

    return redirect(url_for('admin_dashboard'))


@app.route('/admin/song/<int:playlist_id>/<int:song_id>/delete', methods=['POST'])
def admin_delete_song(playlist_id, song_id):
    """Delete a song from a playlist."""
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    data = load_data()

    if playlist_id >= len(data['playlists']):
        return "Playlist not found", 404

    playlist = data['playlists'][playlist_id]

    if song_id >= len(playlist['songs']):
        return "Song not found", 404

    song = playlist['songs'][song_id]

    # Delete file
    file_path = DOWNLOADS_DIR / song['filename']
    if file_path.exists():
        file_path.unlink()

    # Remove from data
    playlist['songs'].pop(song_id)
    save_data(data)

    return redirect(url_for('admin_dashboard'))


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(debug=True, host='0.0.0.0', port=port)
