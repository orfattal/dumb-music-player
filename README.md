# Dumb Music Player

A lightweight web app optimized for Nokia 215 Opera Mini browser that allows users to browse playlists and download MP3s.

## Features

### Public Interface
- Simple, no-JavaScript interface optimized for Opera Mini
- Browse available playlists
- View songs in each playlist
- Download songs as MP3 files
- No login required for end users

### Admin Backend
- Password-protected admin interface
- Create playlists from Apple Music URLs
- Search and download songs from YouTube automatically
- Manage playlists and songs
- Delete unwanted content

## Prerequisites

- Python 3.8 or higher
- FFmpeg (required for audio conversion)

### Install FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
Download from https://ffmpeg.org/download.html

## Installation

1. Clone or download this repository

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Create environment file:
```bash
cp .env.example .env
```

4. Edit `.env` and set your admin password:
```
ADMIN_PASSWORD=your-secure-password
SECRET_KEY=your-secret-key-here
```

## Usage

### Start the server

```bash
python app.py
```

The app will be available at:
- Public interface: http://localhost:5000
- Admin login: http://localhost:5000/admin

### For Production

For production deployment, use a production WSGI server:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Admin Workflow

1. Go to `/admin` and log in with your password
2. Click "Add New Playlist"
3. Enter a playlist name and Apple Music URL (URL is stored but not parsed automatically)
4. Click "Add Song" for the playlist
5. Enter song name and artist name
6. The app will:
   - Search YouTube for the song
   - Download it as MP3
   - Add it to your playlist

## Project Structure

```
dumb-music-player/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── data.json             # Playlist database (auto-created)
├── downloads/            # MP3 files storage (auto-created)
├── templates/            # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── playlist.html
│   ├── admin_login.html
│   ├── admin_dashboard.html
│   ├── admin_add_playlist.html
│   └── admin_add_song.html
└── .env                  # Environment variables
```

## YouTube Authentication (Optional)

The app will attempt to download YouTube videos without authentication first, which works for most public videos. However, some videos may require authentication.

**If downloads fail**, you can provide YouTube cookies:

**Option 1: Export cookies manually (Recommended for production)**
1. Install a browser extension like "Get cookies.txt LOCALLY" for Chrome/Firefox
2. Visit youtube.com and make sure you're logged in
3. Click the extension and export cookies
4. Save as `cookies.txt` in the project root directory

**Option 2: Use browser cookies (automatic - Local development only)**
On your local machine with Chrome installed, the app will try to use cookies from your Chrome browser automatically.

**Download Strategy**:
The app tries multiple strategies in order:
1. cookies.txt file (if exists)
2. Chrome browser cookies (if Chrome is installed)
3. No authentication (works for most public videos)

## Notes

- **Apple Music API**: Currently, playlists are created manually. To automatically parse Apple Music playlists, you would need to implement proper Apple Music API integration or web scraping.
- **Opera Mini Optimization**: The UI uses minimal CSS, no JavaScript, and simple HTML that works well on feature phones.
- **YouTube Downloads**: Uses yt-dlp to search and download from YouTube. Make sure this complies with YouTube's Terms of Service in your jurisdiction.
- **Storage**: MP3 files are stored in the `downloads/` directory. Make sure you have enough disk space.

## License

MIT License - feel free to modify and use as needed.
