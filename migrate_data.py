#!/usr/bin/env python3
"""
Migration script to convert old playlist-based data.json to new flat song list format.
Run this on Render via Shell if you have existing data.
"""

import json
from pathlib import Path

def migrate():
    data_file = Path('data.json')

    if not data_file.exists():
        print("No data.json found - nothing to migrate")
        return

    # Backup old data
    backup_file = Path('data.json.backup')
    with open(data_file, 'r') as f:
        old_data = json.load(f)

    with open(backup_file, 'w') as f:
        json.dump(old_data, f, indent=2, ensure_ascii=False)
    print(f"✓ Backed up data to {backup_file}")

    # Check if already migrated
    if 'songs' in old_data and 'playlists' not in old_data:
        print("✓ Data already in new format")
        # But add thumbnail field if missing
        updated = False
        for song in old_data['songs']:
            if 'thumbnail' not in song:
                song['thumbnail'] = None
                updated = True
        if updated:
            with open(data_file, 'w') as f:
                json.dump(old_data, f, indent=2, ensure_ascii=False)
            print("✓ Added thumbnail field to existing songs")
        else:
            print("✓ No migration needed")
        return

    # Convert to new format
    new_data = {'songs': []}

    for playlist in old_data.get('playlists', []):
        for song in playlist.get('songs', []):
            # Use the song name as display name, or combine name + artist
            display_name = f"{song.get('name', '')} - {song.get('artist', '')}"
            new_data['songs'].append({
                'display_name': display_name,
                'search_name': song.get('name', ''),
                'search_artist': song.get('artist', ''),
                'filename': song.get('filename', ''),
                'youtube_url': song.get('youtube_url', ''),
                'thumbnail': song.get('thumbnail', None)
            })

    # Save new data
    with open(data_file, 'w') as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)

    print(f"✓ Migrated {len(new_data['songs'])} songs to new format")
    print("\nNew data structure:")
    print(json.dumps(new_data, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    migrate()
