"""Export cover tags from COVER_POOL to tags.json and covers.ts.

Usage:
  python scripts/export_tags.py           # SVG placeholders (default)
  python scripts/export_tags.py --ext webp  # Real photos after download_covers.py
"""
import argparse
import json
import sys
sys.path.insert(0, 'scripts')
from cover_match_simulation import COVER_POOL


def build_data(ext: str) -> dict:
    data = {}
    for cat, entries in COVER_POOL.items():
        data[cat] = []
        for filename, tags in entries:
            entry = {'file': f'{filename}.{ext}'}
            for dim in ['cat', 'sub', 'fmt', 'vibe']:
                entry[dim] = sorted(tags[dim])
            data[cat].append(entry)
    return data


def write_tags_json(data: dict, path: str) -> None:
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def write_covers_ts(data: dict, path: str) -> None:
    """Write covers.ts — TypeScript module with `export default { ... } as const`."""
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f'export default {json_str} as const\n')


def main():
    parser = argparse.ArgumentParser(description='Export cover tags')
    parser.add_argument('--ext', default='svg', choices=['svg', 'webp', 'jpg'],
                        help='Image file extension (default: svg)')
    args = parser.parse_args()

    data = build_data(args.ext)

    tags_path = 'scustack-web/public/covers/tags.json'
    write_tags_json(data, tags_path)

    covers_ts_path = 'scustack-web/data/covers.ts'
    write_covers_ts(data, covers_ts_path)

    total = sum(len(v) for v in data.values())
    print(f'{total} covers across {len(data)} categories (.{args.ext})')
    print(f'  → {tags_path}')
    print(f'  → {covers_ts_path}')
    for cat, entries in data.items():
        sub = sum(1 for e in entries if e['sub'])
        gen = len(entries) - sub
        print(f'  {cat}: {len(entries)} ({sub} subject, {gen} generic)')


if __name__ == '__main__':
    main()
