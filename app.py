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
    DATA_FILE.write_text(json.dumps({'songs': []}, indent=2))


def load_data():
    """Load songs data from JSON file."""
    with open(DATA_FILE, 'r') as f:
        return json.load(f)


def save_data(data):
    """Save songs data to JSON file."""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def search_youtube(song_name, artist_name):
    """Search YouTube for a song and return the first result URL and title."""
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
                url = f"https://www.youtube.com/watch?v={video['id']}"
                title = video.get('title', f"{song_name} - {artist_name}")
                return url, title
    except Exception as e:
        print(f"Error searching YouTube: {e}")

    return None, None


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


# ============ PUBLIC ROUTES ============

@app.route('/')
def index():
    """Public homepage showing all songs."""
    data = load_data()
    return render_template('index.html', songs=data['songs'])


@app.route('/download/<int:song_id>')
def download_song(song_id):
    """Download a specific song as MP3."""
    data = load_data()

    if song_id >= len(data['songs']):
        return "שיר לא נמצא", 404

    song = data['songs'][song_id]
    file_path = DOWNLOADS_DIR / song['filename']

    if not file_path.exists():
        return "קובץ לא נמצא", 404

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

    return render_template('admin_login.html', error='סיסמה שגויה')


@app.route('/admin/logout')
def admin_logout():
    """Admin logout."""
    session.pop('admin', None)
    return redirect(url_for('index'))


@app.route('/admin/dashboard')
def admin_dashboard():
    """Admin dashboard showing all songs."""
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    data = load_data()
    return render_template('admin_dashboard.html', songs=data['songs'])


@app.route('/admin/add-song', methods=['GET', 'POST'])
def admin_add_song():
    """Add a new song."""
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        song_name = request.form.get('song_name')
        artist_name = request.form.get('artist_name')

        if not song_name or not artist_name:
            return render_template('admin_add_song.html', error='נא למלא שם שיר ושם אמן')

        # Search YouTube
        youtube_url, youtube_title = search_youtube(song_name, artist_name)

        if not youtube_url:
            return render_template('admin_add_song.html', error='לא נמצא שיר ביוטיוב')

        # Generate filename
        safe_name = re.sub(r'[^\w\s-]', '', f"{song_name}-{artist_name}")
        safe_name = re.sub(r'[-\s]+', '-', safe_name)
        filename = f"{safe_name}.mp3"

        # Download from YouTube
        output_path = DOWNLOADS_DIR / filename
        success = download_from_youtube(youtube_url, output_path)

        if not success:
            return render_template('admin_add_song.html', error='שגיאה בהורדה מיוטיוב')

        # Add to songs list
        data = load_data()
        data['songs'].append({
            'display_name': youtube_title,
            'search_name': song_name,
            'search_artist': artist_name,
            'filename': filename,
            'youtube_url': youtube_url
        })
        save_data(data)

        return redirect(url_for('admin_dashboard'))

    return render_template('admin_add_song.html')


@app.route('/admin/song/<int:song_id>/edit', methods=['GET', 'POST'])
def admin_edit_song(song_id):
    """Edit a song's display name."""
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    data = load_data()

    if song_id >= len(data['songs']):
        return "שיר לא נמצא", 404

    song = data['songs'][song_id]

    if request.method == 'POST':
        new_name = request.form.get('display_name')

        if not new_name:
            return render_template('admin_edit_song.html', song=song, song_id=song_id, error='נא למלא שם')

        # Update song name
        data['songs'][song_id]['display_name'] = new_name
        save_data(data)

        return redirect(url_for('admin_dashboard'))

    return render_template('admin_edit_song.html', song=song, song_id=song_id)


@app.route('/admin/song/<int:song_id>/delete', methods=['POST'])
def admin_delete_song(song_id):
    """Delete a song."""
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    data = load_data()

    if song_id >= len(data['songs']):
        return "שיר לא נמצא", 404

    song = data['songs'][song_id]

    # Delete file
    file_path = DOWNLOADS_DIR / song['filename']
    if file_path.exists():
        file_path.unlink()

    # Remove from data
    data['songs'].pop(song_id)
    save_data(data)

    return redirect(url_for('admin_dashboard'))


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(debug=True, host='0.0.0.0', port=port)
