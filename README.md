# נגן מוזיקה פשוט / Dumb Music Player

אפליקציית ווב קלת משקל המותאמת לדפדפן Opera Mini בנוקיה 215, מאפשרת למשתמשים לצפות ברשימת שירים ולהוריד MP3.

A lightweight web app optimized for Nokia 215 Opera Mini browser that allows users to browse songs and download MP3s.

## תכונות / Features

### ממשק ציבורי / Public Interface
- ממשק פשוט ללא JavaScript, מותאם ל-Opera Mini
- רשימת שירים עם שמות כפי שהם מופיעים ביוטיוב
- תמונות ממוזערות (thumbnails) ליד כל שיר
- חיפוש חופשי ביוטיוב עם תצוגה מקדימה
- הורדת שירים כקבצי MP3
- אין צורך בהתחברות למשתמשי קצה

- Simple, minimal JavaScript interface optimized for Opera Mini
- Flat list of songs with names as they appear on YouTube
- Thumbnails displayed next to each song
- Free YouTube search with preview
- Download songs as MP3 files
- No login required for end users

### ממשק ניהול / Admin Backend
- ממשק ניהול מוגן בסיסמה
- חיפוש שירים ביוטיוב: תוצאות עם תמונות ממוזערות ואפשרות תצוגה מקדימה
- בחירת הסרטון הנכון מתוך תוצאות החיפוש
- הורדה אוטומטית עם שמירת thumbnail
- עריכת שמות שירים
- מחיקת שירים
- הכל בעברית

- Password-protected admin interface
- Search YouTube: results with thumbnails and preview option
- Select the correct video from search results
- Automatic download with thumbnail saving
- Edit song names
- Delete songs
- Full Hebrew interface

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

## Admin Workflow / תהליך ניהול

1. עבור ל-`/admin` והתחבר עם הסיסמה שלך / Go to `/admin` and log in with your password
2. לחץ "הוסף שיר חדש" / Click "הוסף שיר חדש" (Add New Song)
3. הזן שם שיר ושם אמן / Enter song name and artist name
4. לחץ "חפש ביוטיוב" / Click "חפש ביוטיוב" (Search YouTube)
5. תראה 5 תוצאות עם תמונות ממוזערות / See 5 results with thumbnails
6. לחץ על סרטון כדי לראות נגן YouTube מוטמע בדף / Click a video to see embedded YouTube player in page
7. בחר את הסרטון הנכון עם כפתור הרדיו / Select the correct video with radio button
8. לחץ "הורד את השיר הנבחר" / Click "הורד את השיר הנבחר" (Download selected song)
9. השיר יתווסף עם thumbnail / Song will be added with thumbnail
10. ערוך את השם לפי הצורך / Edit the name if needed

## Project Structure

```
dumb-music-player/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── data.json             # Songs database (auto-created)
├── downloads/            # MP3 files storage (auto-created)
├── templates/            # HTML templates (Hebrew)
│   ├── base.html
│   ├── index.html
│   ├── admin_login.html
│   ├── admin_dashboard.html
│   ├── admin_add_song.html
│   └── admin_edit_song.html
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

## Notes / הערות

- **Hebrew Interface / ממשק עברי**: All UI text is in Hebrew with RTL support for optimal viewing.
- **Opera Mini Optimization / אופטימיזציה ל-Opera Mini**: The UI uses minimal CSS, no JavaScript, and simple HTML that works well on feature phones.
- **YouTube Downloads / הורדות מיוטיוב**: Uses yt-dlp to search and download from YouTube. Make sure this complies with YouTube's Terms of Service in your jurisdiction.
- **Storage / אחסון**: MP3 files are stored in the `downloads/` directory. Make sure you have enough disk space.
- **Song Names / שמות שירים**: Songs are initially named as they appear on YouTube, but can be edited through the admin interface.

## License

MIT License - feel free to modify and use as needed.
