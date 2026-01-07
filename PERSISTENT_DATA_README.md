# Persistent Data Structure

This application stores all user data in a single directory for easy backup and persistent storage across deployments.

## Directory Structure

```
persistent_data/
├── downloads/          # MP3 audio files
├── thumbnails/         # YouTube video thumbnails
├── data.json          # Song metadata database
└── cookies.txt        # YouTube authentication cookies (optional)
```

## Render Disk Mount Configuration

### Step 1: Purchase Persistent Disk in Render

1. Go to your service dashboard: https://dashboard.render.com/web/srv-d5ed34shg0os7398isk0
2. Click "Disks" in the left sidebar
3. Click "Add Disk"
4. Configure:
   - **Name**: `music-player-data` (or any name you prefer)
   - **Mount Path**: `/opt/render/project/src/persistent_data`
   - **Size**: Start with 1 GB (can be increased later)
5. Click "Create Disk"

### Step 2: Set Environment Variable (Optional)

If you want to use a custom mount path, set this environment variable in Render:

- **Key**: `PERSISTENT_DATA_PATH`
- **Value**: Your custom path (e.g., `/data` or `/mnt/storage`)

If not set, the app defaults to `persistent_data/` in the project root.

### Step 3: Redeploy

After adding the disk, Render will automatically redeploy your service. The disk will be mounted and all data will persist across deployments.

## Default Mount Path

**Recommended mount path for Render**: `/opt/render/project/src/persistent_data`

This path:
- ✅ Is inside your project directory
- ✅ Works with the default `PERSISTENT_DATA_PATH` value
- ✅ No environment variable needed

## Data Persistence

Once the disk is mounted:
- ✅ Songs survive deployments
- ✅ Thumbnails are preserved
- ✅ Database persists
- ✅ Cookies remain configured

## Backup

To backup your data:
1. Download files from: `/opt/render/project/src/persistent_data/`
2. Or use Render's disk snapshot feature (if available on your plan)

## Migration from Old Structure

If you have existing data from before this change:
1. Old files were in: `downloads/`, `static/thumbnails/`, `data.json`, `cookies.txt`
2. These will NOT be automatically migrated
3. Old data will be lost on next deployment (not mounted to disk)
4. To preserve old data, manually copy it to the persistent disk before deploying

## Disk Size Recommendations

- **Small usage** (10-50 songs): 1 GB
- **Medium usage** (50-200 songs): 5 GB
- **Large usage** (200+ songs): 10+ GB

Each MP3 is typically 3-5 MB, so calculate based on your expected library size.

## Troubleshooting

### Data not persisting
- Check disk is mounted at correct path
- Verify `PERSISTENT_DATA_PATH` environment variable (if set)
- Check Render logs for initialization messages showing paths

### Thumbnails not loading
- Check `/thumbnails/<filename>` route is working
- Verify thumbnails exist in `persistent_data/thumbnails/`
- Check file permissions on disk

### Cookies not working
- Ensure `cookies.txt` is in `persistent_data/` directory
- Verify file format (Netscape cookies format)
- Check logs for "FOUND" message when downloading
