# Deploying to Render.com

Follow these steps to deploy your Dumb Music Player to Render.com (free tier):

## Step 1: Create a GitHub Repository

1. Go to https://github.com/new
2. Create a new repository called `dumb-music-player`
3. Make it **Public** (required for Render free tier)
4. Don't initialize with README (we already have files)
5. Click "Create repository"

## Step 2: Push Your Code to GitHub

Run these commands in your terminal (in the `/Users/orf/dumb-music-player` directory):

```bash
git remote add origin https://github.com/YOUR_USERNAME/dumb-music-player.git
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

## Step 3: Deploy to Render

1. Go to https://render.com and sign up (free account)
2. Click "New +" → "Web Service"
3. Connect your GitHub account
4. Select your `dumb-music-player` repository
5. Render will auto-detect the settings from `render.yaml`
6. Set these environment variables:
   - `ADMIN_PASSWORD`: Choose a secure password for admin access
7. Click "Create Web Service"

## Step 4: Wait for Deployment

Render will:
- Install dependencies
- Build your app
- Deploy it to a public URL like `https://dumb-music-player-xyz.onrender.com`

This takes about 5-10 minutes for the first deployment.

## Step 5: Access Your App

Once deployed, you'll get a URL like:
- **Public:** https://your-app-name.onrender.com
- **Admin:** https://your-app-name.onrender.com/admin

Use this URL on your Nokia 215 Opera Mini - it will work perfectly with no warnings!

## Important Notes

**File Storage:**
- Render's free tier has ephemeral storage
- Downloaded MP3 files will be deleted when the service restarts (every ~15 minutes of inactivity)
- For permanent storage, upgrade to a paid plan or use external storage (S3, Cloudinary, etc.)

**Free Tier Limitations:**
- Service spins down after 15 minutes of inactivity
- First request after spin-down takes ~30 seconds to wake up
- 750 hours/month of runtime (plenty for testing)

**To Keep Files Persistent:**
You would need to:
1. Use Render's paid plan with persistent disk ($7/month), OR
2. Store MP3s in external storage (AWS S3, Cloudinary, etc.)

For now, the free tier is perfect for testing and showing the concept!
