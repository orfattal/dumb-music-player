import os
import json
import re
import requests
import yt_dlp
import sys
import time
from flask import Flask, render_template, request, redirect, url_for, session, send_file, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv
from pathlib import Path

# Force unbuffered output for real-time logging
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin')

# Log EVERY request before it reaches any route
@app.before_request
def log_request():
    print(f"\n>>> [MIDDLEWARE] Request received: {request.method} {request.path}", flush=True)
    print(f">>> [MIDDLEWARE] Time: {time.time()}", flush=True)
    sys.stdout.flush()

# Add ngrok skip warning header to all responses
@app.after_request
def add_ngrok_header(response):
    response.headers['ngrok-skip-browser-warning'] = 'true'
    return response

# Directories
DOWNLOADS_DIR = Path('downloads')
DOWNLOADS_DIR.mkdir(exist_ok=True)
THUMBNAILS_DIR = Path('static/thumbnails')
THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)
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


def search_youtube(song_name, artist_name, num_results=5):
    """Search YouTube for a song and return top results with metadata."""
    query = f"{song_name} {artist_name}"

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(f"ytsearch{num_results}:{query}", download=False)
            if result and 'entries' in result and len(result['entries']) > 0:
                videos = []
                for video in result['entries']:
                    videos.append({
                        'id': video['id'],
                        'url': f"https://www.youtube.com/watch?v={video['id']}",
                        'title': video.get('title', ''),
                        'thumbnail': video.get('thumbnail', ''),
                        'duration': video.get('duration', 0),
                        'channel': video.get('channel', video.get('uploader', ''))
                    })
                return videos
    except Exception as e:
        print(f"Error searching YouTube: {e}")

    return []


def download_from_youtube(youtube_url, output_path, thumbnail_path=None):
    """Download audio from YouTube as MP3 and optionally save thumbnail."""
    print(f"  [download_from_youtube] Starting download for: {youtube_url}", flush=True)

    # Check if cookies file exists
    cookies_file = Path('cookies.txt')
    print(f"  [download_from_youtube] Checking for cookies.txt... {'FOUND' if cookies_file.exists() else 'NOT FOUND'}", flush=True)

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
        'writethumbnail': True if thumbnail_path else False,
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

    print(f"  [download_from_youtube] Will try {len(strategies)} strategies", flush=True)

    # Try each strategy until one works
    for strategy_index, (strategy_name, opts) in enumerate(strategies, 1):
        try:
            print(f"\n  [download_from_youtube] === STRATEGY {strategy_index}/{len(strategies)}: {strategy_name} ===", flush=True)
            print(f"  [download_from_youtube] Downloading from: {youtube_url}", flush=True)
            print(f"  [download_from_youtube] Output path: {output_path}", flush=True)

            import time
            strategy_start = time.time()

            print(f"  [download_from_youtube] Creating YoutubeDL instance...", flush=True)
            with yt_dlp.YoutubeDL(opts) as ydl:
                print(f"  [download_from_youtube] Calling extract_info()...", flush=True)
                info = ydl.extract_info(youtube_url, download=True)
                print(f"  [download_from_youtube] extract_info() completed", flush=True)

            strategy_elapsed = time.time() - strategy_start
            print(f"  [download_from_youtube] Strategy took {strategy_elapsed:.2f} seconds", flush=True)

            # Check if the mp3 file was created
            print(f"  [download_from_youtube] Checking if file exists at: {output_path}", flush=True)
            if output_path.exists():
                print(f"  [download_from_youtube] ✓ File created successfully: {output_path}", flush=True)
                file_size = output_path.stat().st_size / (1024 * 1024)  # MB
                print(f"  [download_from_youtube] File size: {file_size:.2f} MB", flush=True)

                # Handle thumbnail if requested
                if thumbnail_path:
                    print(f"  [download_from_youtube] Processing thumbnail...", flush=True)
                    # yt-dlp saves thumbnail with same basename as audio file
                    possible_thumb_exts = ['.jpg', '.png', '.webp']
                    base_path = output_path.with_suffix('')
                    for ext in possible_thumb_exts:
                        thumb_file = base_path.with_suffix(ext)
                        if thumb_file.exists():
                            # Move thumbnail to desired location
                            import shutil
                            shutil.move(str(thumb_file), str(thumbnail_path))
                            print(f"  [download_from_youtube] ✓ Thumbnail saved: {thumbnail_path}", flush=True)
                            break
                    else:
                        print(f"  [download_from_youtube] ⚠ No thumbnail found", flush=True)

                print(f"  [download_from_youtube] === SUCCESS ===", flush=True)
                return True
            else:
                print(f"  [download_from_youtube] ✗ File not created at expected path: {output_path}", flush=True)
                # Check if file exists without extension
                base_path = output_path.with_suffix('')
                if base_path.exists():
                    print(f"  [download_from_youtube] Found file without .mp3 extension, renaming...", flush=True)
                    base_path.rename(output_path)
                    print(f"  [download_from_youtube] === SUCCESS (after rename) ===", flush=True)
                    return True
                else:
                    print(f"  [download_from_youtube] File not found even without extension", flush=True)
        except Exception as e:
            import traceback
            print(f"  [download_from_youtube] ✗ Strategy '{strategy_name}' FAILED", flush=True)
            print(f"  [download_from_youtube] Error: {e}", flush=True)
            print(f"  [download_from_youtube] Traceback:", flush=True)
            traceback.print_exc()
            sys.stdout.flush()
            sys.stderr.flush()
            # Continue to next strategy
            continue

    # All strategies failed
    print(f"  [download_from_youtube] === ALL STRATEGIES FAILED ===", flush=True)
    print(f"  [download_from_youtube] Error: All download strategies failed for {youtube_url}", flush=True)
    print("  [download_from_youtube] Tip: For better reliability, export YouTube cookies to cookies.txt file", flush=True)
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
    """Search for a song on YouTube."""
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        print("\n" + "="*80, flush=True)
        print("SEARCH REQUEST STARTED", flush=True)
        print("="*80, flush=True)

        song_name = request.form.get('song_name')
        artist_name = request.form.get('artist_name')

        print(f"Song Name: {song_name}", flush=True)
        print(f"Artist Name: {artist_name}", flush=True)

        if not song_name or not artist_name:
            print("ERROR: Missing song_name or artist_name", flush=True)
            return render_template('admin_add_song.html', error='נא למלא שם שיר ושם אמן')

        # Search YouTube
        print("\n>>> CALLING search_youtube()...", flush=True)
        import time
        start_time = time.time()
        search_results = search_youtube(song_name, artist_name)
        elapsed_time = time.time() - start_time
        print(f"<<< search_youtube() COMPLETED in {elapsed_time:.2f} seconds", flush=True)
        print(f"Found {len(search_results)} results", flush=True)

        if not search_results:
            print("ERROR: No search results found", flush=True)
            return render_template('admin_add_song.html', error='לא נמצא שיר ביוטיוב')

        # Show search results
        print("\n>>> Rendering search results page...", flush=True)
        print("="*80, flush=True)
        print("SEARCH REQUEST COMPLETED", flush=True)
        print("="*80 + "\n", flush=True)
        return render_template('admin_search_results.html',
                             results=search_results,
                             song_name=song_name,
                             artist_name=artist_name)

    return render_template('admin_add_song.html')


@app.route('/admin/ping', methods=['GET', 'POST'])
def admin_ping():
    """Simple test endpoint to verify requests reach the server."""
    print("!!! PING ENDPOINT HIT !!!", flush=True)
    print(f"Method: {request.method}", flush=True)
    print(f"Form data: {dict(request.form)}", flush=True)
    return jsonify({'status': 'ok', 'message': 'Server is reachable'})


@app.route('/admin/download-song', methods=['POST'])
def admin_download_song():
    """Download selected song from YouTube."""
    import sys
    sys.stdout.flush()
    sys.stderr.flush()
    print("\n" + "="*80, flush=True)
    print("!!! DOWNLOAD ROUTE HIT !!!", flush=True)
    print("DOWNLOAD REQUEST STARTED", flush=True)
    print(f"Request method: {request.method}", flush=True)
    print(f"Request path: {request.path}", flush=True)
    print(f"Request form keys: {list(request.form.keys())}", flush=True)
    print("="*80, flush=True)

    if 'admin' not in session:
        print("ERROR: User not authenticated", flush=True)
        return redirect(url_for('admin_login'))

    youtube_url = request.form.get('youtube_url')
    youtube_title = request.form.get('youtube_title')
    youtube_thumbnail = request.form.get('youtube_thumbnail')
    song_name = request.form.get('song_name')
    artist_name = request.form.get('artist_name')

    print(f"Song Name: {song_name}", flush=True)
    print(f"Artist Name: {artist_name}", flush=True)
    print(f"YouTube URL: {youtube_url}", flush=True)
    print(f"YouTube Title: {youtube_title}", flush=True)

    if not youtube_url or not youtube_title:
        print("ERROR: Missing youtube_url or youtube_title", flush=True)
        return redirect(url_for('admin_add_song'))

    # Generate filename
    safe_name = re.sub(r'[^\w\s-]', '', f"{song_name}-{artist_name}")
    safe_name = re.sub(r'[-\s]+', '-', safe_name)
    filename = f"{safe_name}.mp3"

    # Generate thumbnail filename
    video_id = youtube_url.split('watch?v=')[-1]
    thumbnail_filename = f"{video_id}.jpg"
    thumbnail_path = THUMBNAILS_DIR / thumbnail_filename

    print(f"Output filename: {filename}", flush=True)
    print(f"Thumbnail filename: {thumbnail_filename}", flush=True)
    print("\n>>> CALLING download_from_youtube()...", flush=True)

    # Download from YouTube
    output_path = DOWNLOADS_DIR / filename

    import time
    start_time = time.time()
    success = download_from_youtube(youtube_url, output_path, thumbnail_path)
    elapsed_time = time.time() - start_time

    print(f"<<< download_from_youtube() COMPLETED in {elapsed_time:.2f} seconds", flush=True)
    print(f"Success: {success}", flush=True)

    if not success:
        print("ERROR: Download failed, re-rendering search results", flush=True)
        search_results = search_youtube(song_name, artist_name)
        return render_template('admin_search_results.html',
                             results=search_results,
                             song_name=song_name,
                             artist_name=artist_name,
                             error='שגיאה בהורדה מיוטיוב. אולי צריך לעדכן cookies?')

    print("\n>>> Adding song to database...", flush=True)
    # Add to songs list
    data = load_data()
    data['songs'].append({
        'display_name': youtube_title,
        'filename': filename,
        'youtube_url': youtube_url,
        'thumbnail': thumbnail_filename if thumbnail_path.exists() else None
    })
    save_data(data)
    print("<<< Song added to database successfully", flush=True)

    print("\n>>> Redirecting to admin dashboard...", flush=True)
    print("="*80, flush=True)
    print("DOWNLOAD REQUEST COMPLETED", flush=True)
    print("="*80 + "\n", flush=True)

    return redirect(url_for('admin_dashboard'))


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
