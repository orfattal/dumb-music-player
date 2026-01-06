# How to Export YouTube Cookies for Render Deployment

YouTube now requires authentication to download videos. For your Render deployment to work, you need to export cookies from your browser.

## Method 1: Using Browser Extension (Easiest)

### For Chrome/Edge:
1. Install extension: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
2. Go to https://youtube.com and make sure you're logged in
3. Click the extension icon
4. Click "Export" → Select "youtube.com"
5. Save the file as `cookies.txt`

### For Firefox:
1. Install addon: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)
2. Go to https://youtube.com and make sure you're logged in
3. Click the addon icon
4. Click "youtube.com" and export
5. Save as `cookies.txt`

## Method 2: Using yt-dlp Command (Alternative)

If you have yt-dlp installed locally:

```bash
yt-dlp --cookies-from-browser chrome --cookies cookies.txt "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

This will export Chrome cookies to `cookies.txt`.

## Adding Cookies to Render

### For Local Development:
Simply place `cookies.txt` in your project root directory (it's already in .gitignore so it won't be committed).

### For Render Deployment:
You have two options:

**Option A: Add cookies.txt to Render (Recommended)**
1. Export cookies as described above
2. In Render dashboard, go to your service
3. Go to "Environment" tab
4. Add a new **Secret File**:
   - **Filename**: `cookies.txt`
   - **Contents**: Paste the entire contents of your exported cookies.txt file
5. Save and redeploy

**Option B: Manual Upload (Requires Render paid plan)**
Upload cookies.txt directly to the server via Render's disk storage (requires paid plan).

## Testing Locally

After exporting cookies:

```bash
# Make sure cookies.txt is in your project root
ls cookies.txt

# Restart your Flask app - it should now work
python app.py
```

## Important Notes

- **Security**: Keep your cookies.txt file private! It contains authentication tokens
- **Expiration**: Cookies expire after some time (usually weeks/months). You'll need to re-export them when downloads start failing
- **Don't commit**: cookies.txt is already in .gitignore to prevent accidental commits

## Troubleshooting

If downloads still fail:
1. Make sure you're logged into YouTube in your browser
2. Try re-exporting the cookies
3. Check that cookies.txt is in the correct location
4. Make sure the cookies file isn't empty
