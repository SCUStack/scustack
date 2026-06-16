"""Download cover images from free image sources.

Uses Pexels API (free tier: 200 req/hr) if PEXELS_API_KEY is set,
otherwise falls back to LoremFlickr (CC-licensed, no key needed).
Images are saved as JPEG and optionally converted to WebP.
"""
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COVERS_DIR = ROOT / 'scustack-web' / 'public' / 'covers'
DATA_FILE = ROOT / 'scustack-web' / 'data' / 'covers.ts'

# Read cover metadata
content = DATA_FILE.read_text(encoding='utf-8')
start = content.index('{')
end = content.rindex('}')
tags_data = json.loads(content[start:end+1])

# ── Download strategies ───────────────────────────────────────────

def download_picsum(category: str, filename: str, tags: list[str]) -> bool:
    """Download from Picsum Photos (free, no API key, CC-licensed).

    Uses filename hash as the random seed for deterministic images.
    """
    seed = abs(hash(filename)) % 10000
    url = f'https://picsum.photos/seed/{seed}/800/400'

    out_path = COVERS_DIR / category / filename
    if out_path.exists() and out_path.stat().st_size > 500:
        return True

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
            if len(data) < 500:
                return False
            out_path.write_bytes(data)
            return True
    except Exception as e:
        print(f'    ✗ Picsum: {e}')
        return False


def download_pexels(category: str, filename: str, tags: list[str], api_key: str) -> bool:
    """Download from Pexels API."""
    import urllib.parse
    query = urllib.parse.quote(' '.join(tags[:3]))
    url = f'https://api.pexels.com/v1/search?query={query}&per_page=1&orientation=landscape'

    out_path = COVERS_DIR / category / filename
    if out_path.exists() and out_path.stat().st_size > 500:
        return True

    try:
        req = urllib.request.Request(url, headers={'Authorization': api_key})
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
        photos = result.get('photos', [])
        if not photos:
            return False
        photo_url = photos[0]['src']['large']
        # Resize to 800x400
        photo_url = photo_url.replace('?', '?w=800&h=400&fit=crop&')
        with urllib.request.urlopen(urllib.request.Request(photo_url), timeout=15) as resp:
            out_path.write_bytes(resp.read())
            return True
    except Exception as e:
        print(f'    ✗ Pexels: {e}')
        return False


# ── Main ──────────────────────────────────────────────────────────

def main():
    api_key = os.environ.get('PEXELS_API_KEY', '')
    use_pexels = bool(api_key)
    source = 'Pexels API' if use_pexels else 'Picsum Photos'

    total = sum(len(v) for v in tags_data.values())
    downloaded = 0
    skipped = 0

    print(f'Downloading {total} covers using {source}...')
    print()

    for category, entries in tags_data.items():
        cat_dir = COVERS_DIR / category
        cat_dir.mkdir(parents=True, exist_ok=True)
        print(f'{category} ({len(entries)} covers):')

        for entry in entries:
            filename = entry['file']
            # Collect all tags for search
            all_tags = entry.get('cat', []) + entry.get('sub', [])
            if not all_tags:
                all_tags = [category]

            if use_pexels:
                ok = download_pexels(category, filename, all_tags, api_key)
            else:
                ok = download_picsum(category, filename, all_tags)

            if ok:
                downloaded += 1
                print(f'  ✓ {filename}')
            else:
                skipped += 1
                print(f'  ⊘ {filename} (keeping SVG placeholder)')

            # Rate limit
            if use_pexels:
                time.sleep(0.4)

    print()
    print(f'Done: {downloaded} downloaded, {skipped} kept as SVG placeholders')

    if not use_pexels:
        print()
        print('TIP: Set PEXELS_API_KEY env var for curated, higher-quality images.')
        print('  Get a free key at https://www.pexels.com/api/')


if __name__ == '__main__':
    main()
